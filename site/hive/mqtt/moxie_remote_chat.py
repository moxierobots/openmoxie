'''
MOXIE REMOTE CHAT - Handle Remote Chat protocol messages from Moxie

Remote Chat (RemoteChatRequest/Response) messages make up the bulk of the remote module
interface for Moxie.  Module/Content IDs that are remote, send inputs and get outputs
using these messages.

Moxie Remote Chat uses a "notify" tracking approach for context, meaning that Moxie notifies
the remote service everytime it says something.  This data is used to accumulate the true
history of the conversation and provides mostly seemless conversation context for the AI,
even when the user provides input in multiple speech windows before hearing a response.
'''
import concurrent.futures
from ..models import SinglePromptChat
from ..automarkup import process as automarkup_process
from ..automarkup import initialize_rules as automarkup_initialize_rules
import logging
import time
from .global_responses import GlobalResponses
from .conversations import ChatSession, SinglePromptDBChatSession
from .volley import Volley
from .protos.embodied.unity.cloudtts_pb2 import CloudTTSRequest

# Turn on to enable global commands in the cloud
_ENABLE_GLOBAL_COMMANDS = True
_LOG_ALL_RCR = False
_LOG_NOTIFY_RCR = True
_MAX_WORKER_THREADS = 5

logger = logging.getLogger(__name__)

'''
RemoteChat is the plugin to the MoxieServer that handles all remote module requests.  It
keeps track of the active remote module, creates new ones as needed, and ignores all data
from local modules.  It also manages auto-markup, which renders plaintext into a markup
language with animated gestures.
'''
class RemoteChat:
    _global_responses: GlobalResponses
    def __init__(self, server):
        self._server = server
        self._device_sessions = {}
        self._modules = { }
        self._modules_info = { "modules": [], "version": "openmoxie_v1" }
        self._worker_queue = concurrent.futures.ThreadPoolExecutor(max_workers=_MAX_WORKER_THREADS)
        self._automarkup_rules = automarkup_initialize_rules()
        self._global_responses = GlobalResponses()

    def register_module(self, module_id, content_id, cname):
        self._modules[f'{module_id}/{content_id}'] = cname

    # Gets the remote module info record to share remote modules with Moxie
    def get_modules_info(self):
        return self._modules_info

    # Update database backed records.  Query to get all the module/content IDs and update the modules schema and register the modules
    def update_from_database(self):
        new_modules = {}
        mod_map = {}
        for chat in SinglePromptChat.objects.all():
            # one module can support many content IDs, separated by | like openers
            cid_list = chat.content_id.split('|')
            for content_id in cid_list:
                new_modules[f'{chat.module_id}/{content_id}'] = { 'xtor': SinglePromptDBChatSession, 'params': { 'pk': chat.pk } }
                logger.debug(f'Registering {chat.module_id}/{content_id}')
                # Group content IDs under module IDs
                if chat.module_id in mod_map:
                    mod_map[chat.module_id].append(content_id)
                else:
                    mod_map[chat.module_id] = [ content_id ]
        # Models/content IDs into the module info schema - bare bones mandatory fields only
        mlist = []
        for mod in mod_map.keys():
            modinfo = { "info": { "id": mod }, "rules": "RANDOM", "source": "REMOTE_CHAT", "content_infos": [] }
            for cid in mod_map[mod]:
                modinfo["content_infos"].append({ "info": { "id": cid } })
            mlist.append(modinfo)
        self._modules_info["modules"] = mlist
        self._modules = new_modules
        self._global_responses.update_from_database()

    # Handle GLOBAL patterns, available inside (almost) any module
    def check_global(self, volley):
        return self._global_responses.check_global(volley) if _ENABLE_GLOBAL_COMMANDS else None

    def on_chat_complete(self, device_id, id, session:ChatSession):
        logger.info(f'Chat Session Complete: {id} {session.has_complete_hook()}')
        if session.has_complete_hook():
            # make a data-only Volley for the completion hook
            volley = Volley({}, device_id=device_id, robot_data=self._server.robot_data().get_volley_data(device_id), local_data=session.local_data, data_only=True)
            self._worker_queue.submit(session.complete_hook, volley)

    # Get the current or a new session for this device for this module/content ID pair
    def active_session_data(self, device_id):
        if device_id in self._device_sessions:
            return self._device_sessions[device_id]['session'].local_data
        return None

    # Get the current or a new session for this device for this module/content ID pair
    def get_session(self, device_id, id, maker) -> ChatSession:
        # each device has a single session only for now
        if device_id in self._device_sessions:
            if self._device_sessions[device_id]['id'] == id:
                return self._device_sessions[device_id]['session']
            else:
                self.on_chat_complete(device_id, self._device_sessions[device_id]['id'], self._device_sessions[device_id]['session'])

        # new session needed
        new_session = { 'id': id, 'session': maker['xtor'](**maker['params']) }
        self._device_sessions[device_id] = new_session
        return new_session['session']

    # Get's a chat session object for use in the web chat
    def get_web_session_for_module(self, device_id, module_id, content_id):
        id = module_id + '/' + content_id
        maker = self._modules.get(id)
        return self.get_session(device_id, id, maker) if maker else None

    def get_web_session_global_response(self, volley: Volley):
        global_functor = self.check_global(volley)
        if global_functor:
            resp = global_functor()
            if isinstance(resp, str):
                return resp
            else:
                return volley.debug_response_string()
        return None

    # Markup text
    def make_markup(self, text, mood_and_intensity = None):
        return automarkup_process(text, self._automarkup_rules, mood_and_intensity=mood_and_intensity)

    # Get the next response to a chat
    def create_session_response(self, device_id, sess:ChatSession, volley: Volley):
        sess.handle_volley(volley)
        if 'markup' not in volley.response['output']:
            # if we don't have markup, create it
            text = volley.response['output']['text']
            volley.set_output(text, self.make_markup(text))

        if _LOG_ALL_RCR:
            logger.info(f"RemoteChatResponse\n{volley.response}")

        # Send RemoteChatResponse to device
        self._server.send_command_to_bot_json(device_id, 'remote_chat', volley.response)

        # Check if CloudTTS is enabled and send parallel CloudTTSRequest
        self._send_cloudtts_if_enabled(device_id, volley)

    # Produce / execute a global response
    def global_response(self, device_id, functor):
        resp = functor()
        output = resp.get('output')
        if output.get('text') and not output.get('markup'):
            # Run automarkup on any text-only responses
            output['markup'] = self.make_markup(output['text'])

        # Send RemoteChatResponse to device
        self._server.send_command_to_bot_json(device_id, 'remote_chat', resp)

        # Check if CloudTTS is enabled and send parallel CloudTTSRequest for global responses
        # Create a mock volley for global responses to reuse CloudTTS logic
        mock_volley = type('MockVolley', (), {'response': resp, 'config': self._server.robot_data().get_config(device_id)})()
        self._send_cloudtts_if_enabled(device_id, mock_volley)

    def log_notify(self, rcr):
        moxie_speech = rcr.get('speech')
        for el in rcr.get('extra_lines', []):
            if el.get('context_type') == 'input':
                logger.info(f"-- USER: {el.get('text')}")
        if moxie_speech:
            logger.info(f"-- MOXIE: {moxie_speech} [{rcr.get('module_id')}/{rcr.get('content_id')}]")

    # Entry point where all RemoteChatRequests arrive
    def handle_request(self, device_id, rcr, volley_data):
        if _LOG_ALL_RCR:
            logger.info(f"RemoteChatRequest\n{rcr}")
        id = rcr.get('module_id', '') + '/' + rcr.get('content_id', '')
        cmd = rcr.get('command')
        if _LOG_NOTIFY_RCR and cmd == 'notify':
            self.log_notify(rcr)

        maker = self._modules.get(id)
        if maker:
            # THIS IS THE PATH FOR REMOTE CONTENT - MODULE/CONTENT HOSTED IN OPENMOXIE
            logger.debug(f'Handling RCR:{cmd} for {id}')
            sess = self.get_session(device_id, id, maker)
            if cmd == 'notify':
                volley = Volley(rcr, device_id=device_id, robot_data=volley_data, local_data=sess.local_data, data_only=True)
                sess.ingest_notify(volley)
            else:
                volley = Volley(rcr, device_id=device_id, robot_data=volley_data, local_data=sess.local_data)
                if not self.handled_global(device_id, volley):
                    self._worker_queue.submit(self.create_session_response, device_id, sess, volley)
        else:
            # THIS IS THE PATH FOR MOXIE ON-BOARD CONTENT
            session_reset = False
            if device_id in self._device_sessions:
                session = self._device_sessions.pop(device_id, None)
                self.on_chat_complete(device_id, session['id'], session['session'])
                session_reset = True
            if cmd != 'notify':
                volley = Volley(rcr, device_id=device_id, robot_data=volley_data)
                if not self.handled_global(device_id, volley):
                    logger.debug(f'Ignoring request for other module: {id} SessionReset:{session_reset}')
                    # Rather than ignoring these, we return a generic FALLBACK response
                    fbline = "I'm sorry. Can  you repeat that?"
                    volley.set_output(fbline, self.make_markup(fbline), output_type='FALLBACK')
                    self._server.send_command_to_bot_json(device_id, 'remote_chat', volley.response)

                    # Check if CloudTTS is enabled and send parallel CloudTTSRequest for fallback
                    self._send_cloudtts_if_enabled(device_id, volley)

    def handled_global(self, device_id, volley):
        global_functor = self.check_global(volley)
        if global_functor:
            logger.debug(f'Global response inside {id}')
            self._worker_queue.submit(self.global_response, device_id, global_functor)
            return True
        return False

    def _send_cloudtts_if_enabled(self, device_id, volley):
        """
        Send CloudTTSRequest if cloud_tts is enabled in robot configuration.
        This allows Unity to receive both ChatResponse and CloudTTSResponse with matching event_ids.
        """
        try:
            # Check if cloud_tts is enabled in robot configuration
            config = getattr(volley, 'config', None) or self._server.robot_data().get_config(device_id)
            cloud_tts_enabled = config.get('settings', {}).get('props', {}).get('cloud_tts', '0') == '1'

            if not cloud_tts_enabled:
                logger.debug(f"CloudTTS disabled for device {device_id}")
                return

            # Get response data
            response = volley.response
            event_id = response.get('event_id')
            markup = response.get('output', {}).get('markup', '')

            if not event_id or not markup:
                logger.debug(f"Missing event_id or markup for CloudTTS request (device: {device_id})")
                return

            logger.info(f"Sending CloudTTSRequest for event_id: {event_id} (device: {device_id})")

            # Create CloudTTSRequest message
            cloudtts_request = CloudTTSRequest()
            cloudtts_request.event_id = str(event_id)
            cloudtts_request.markup = str(markup)
            cloudtts_request.timestamp = int(time.time() * 1000)  # Using time.time() instead of now_ms()
            cloudtts_request.chunk_num = 0
            cloudtts_request.software_version = "openmoxie_v1"
            cloudtts_request.module_name = "remote_chat"

            # Send CloudTTSRequest via ZMQ topic
            self._server.send_zmq_to_bot(device_id, cloudtts_request)

            logger.debug(f"CloudTTSRequest sent for event_id: {event_id}")

        except Exception as e:
            logger.error(f"Error sending CloudTTSRequest for device {device_id}: {e}")
