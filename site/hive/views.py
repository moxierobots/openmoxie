from django.forms import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse,HttpResponseRedirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import qrcode
from PIL import Image
from io import BytesIO

from .models import GlobalResponse, SinglePromptChat, MoxieDevice, MoxieSchedule, HiveConfiguration, MentorBehavior
from .content.data import DM_MISSION_CONTENT_IDS, get_moxie_customization_groups
from .data_import import update_import_status, import_content
from .mqtt.moxie_server import get_instance
from .mqtt.robot_data import DEFAULT_ROBOT_CONFIG, DEFAULT_ROBOT_SETTINGS
from .mqtt.volley import Volley
from .validators import (
    validate_openai_api_key, validate_google_api_key, validate_hostname,
    sanitize_input, validate_device_name, ValidationError as CustomValidationError
)
from .auth_utils import require_api_key, rate_limit
from .behavior_config import (get_behavior_markup, get_quick_action_behavior, 
                              get_preset_actions, get_sound_effect_markup,
                              get_sequence_markup)
import json
import uuid
import logging
import csv
import io
from django.utils import timezone
from .automarkup import process as automarkup_process
from .automarkup import initialize_rules as automarkup_initialize_rules

logger = logging.getLogger(__name__)

# Initialize automarkup rules for the public API
_automarkup_rules = None

def get_automarkup_rules():
    global _automarkup_rules
    if _automarkup_rules is None:
        _automarkup_rules = automarkup_initialize_rules()
    return _automarkup_rules

# ROOT - Show setup if we have no config record, dashboard otherwise
def root_view(request):
    cfg = HiveConfiguration.get_current()
    # Check if this is a newly created config (empty openai_api_key indicates setup needed)
    if cfg and cfg.openai_api_key:
        return HttpResponseRedirect(reverse("hive:dashboard"))
    else:
        return HttpResponseRedirect(reverse("hive:setup"))

# SETUP - Edit systemn configuration record
class SetupView(generic.TemplateView):
    template_name = "hive/setup.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        User = get_user_model()
        context['needs_admin'] = not User.objects.filter(is_superuser=True).exists()
        curr_cfg = HiveConfiguration.get_current()
        if curr_cfg:
            context['object'] = curr_cfg
        return context

# SETUP-POST - Save system config changes
@require_http_methods(["POST"])
def hive_configure(request):
    cfg = HiveConfiguration.get_current()
    
    try:
        # Validate and sanitize OpenAI API key
        openai = sanitize_input(request.POST.get('apikey', ''), max_length=100)
        if openai:
            validate_openai_api_key(openai)
            cfg.openai_api_key = openai
        
        # Validate and process Google API key
        google = sanitize_input(request.POST.get('googleapikey', ''), max_length=10000)
        if google:
            parsed_google = validate_google_api_key(google)
            # Moxie likes compact json, so rewrite json input to be safe
            cfg.google_api_key = json.dumps(parsed_google, separators=(',', ':'))
        
        # Validate hostname
        hostname = sanitize_input(request.POST.get('hostname', ''), max_length=255)
        validate_hostname(hostname)
        cfg.external_host = hostname
        
        cfg.allow_unverified_bots = request.POST.get('allowall') == "on"
        
    except CustomValidationError as e:
        logger.error(f"Validation error in hive configuration: {str(e)}")
        return redirect('hive:setup', alert_message=f'Configuration error: {str(e)}')
    except Exception as e:
        logger.error(f"Unexpected error in hive configuration: {str(e)}")
        return redirect('hive:setup', alert_message='An unexpected error occurred. Please check your input.')
    # Bootstrap any default data if not present
    if not cfg.common_config:
        cfg.common_config = DEFAULT_ROBOT_CONFIG
    if not cfg.common_settings:
        cfg.common_settings = DEFAULT_ROBOT_SETTINGS
    cfg.save()

    # Create Admin User if data exists and we dont have one
    User = get_user_model()
    if not User.objects.filter(is_superuser=True).exists():
        admin = request.POST.get("adminUser")
        adminPassword = request.POST.get("adminPassword")
        if admin and adminPassword:
            User.objects.create_superuser(admin, None, adminPassword)
            logger.info(f"Created superuser '{admin}'")
        else:
            logger.warning(f"Couldn't create missing superuser")

    logger.info("Updated default Hive Configuration")
    # reload any cached db objects
    get_instance().update_from_database()
    return HttpResponseRedirect(reverse("hive:dashboard"))

# DASHBOARD - View and overview of the system
class DashboardView(generic.TemplateView):
    template_name = "hive/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        alert_message = kwargs.get('alert_message', None)
        if alert_message:
            context['alert'] = alert_message
        
        # Paginate devices
        devices_list = MoxieDevice.objects.select_related('schedule').order_by('-last_connect')
        devices_paginator = Paginator(devices_list, 10)  # 10 devices per page
        devices_page = self.request.GET.get('devices_page', 1)
        
        try:
            context['recent_devices'] = devices_paginator.page(devices_page)
        except PageNotAnInteger:
            context['recent_devices'] = devices_paginator.page(1)
        except EmptyPage:
            context['recent_devices'] = devices_paginator.page(devices_paginator.num_pages)
        
        # Paginate conversations
        conversations_list = SinglePromptChat.objects.order_by('name')
        conv_paginator = Paginator(conversations_list, 5)  # 5 conversations per page
        conv_page = self.request.GET.get('conv_page', 1)
        
        try:
            context['conversations'] = conv_paginator.page(conv_page)
        except PageNotAnInteger:
            context['conversations'] = conv_paginator.page(1)
        except EmptyPage:
            context['conversations'] = conv_paginator.page(conv_paginator.num_pages)
        
        context['schedules'] = MoxieSchedule.objects.all()  # Keep schedules unpaginated for now
        context['live'] = get_instance().robot_data().connected_list()
        
        return context

# INTERACT - Chat with a remote conversation
class InteractionView(generic.DetailView):
    template_name = "hive/interact.html"
    model = SinglePromptChat

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['token'] = uuid.uuid4().hex
        return context

# INTERACT-POST - Handle user input during interact
@require_http_methods(["POST"])
def interact_update(request):
    speech = request.POST['speech']
    token = request.POST['token']
    module_id = request.POST['module_id']
    content_id = request.POST['content_id'].split('|')[0]
    session = get_instance().get_web_session_for_module(token, module_id, content_id)
    volley = Volley.request_from_speech(speech, device_id=token, module_id=module_id, content_id=content_id, local_data=session.local_data)
    # Check global responses manually
    gresp = get_instance().get_web_session_global_response(volley) if speech else None
    if gresp:
        line = gresp
        details = {}
    else:
        session.handle_volley(volley)
        line = volley.debug_response_string()
        details = volley.response
    return JsonResponse({'message': line, 'details': details})

# RELOAD - Reload any records initialized from the database
def reload_database(request):
    get_instance().update_from_database()
    return redirect('hive:dashboard_alert', alert_message='Updated from database.')

# ENDPOINT - Render QR code to migrate Moxie
def endpoint_qr(request):
    img = qrcode.make(get_instance().get_endpoint_qr_data())
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    return HttpResponse(buffer, content_type='image/png')

# WIFI EDIT - Edit wifi params to create QR Code
class WifiQREditView(generic.TemplateView):
    template_name = "hive/wifi.html"

# WIFI-POST - Render QR code for Wifi Creds
@require_http_methods(["POST"])
def wifi_qr(request):
    ssid = request.POST['ssid']
    password = request.POST['password']
    band_id = request.POST['frequency']
    hidden = 'hidden' in request.POST
    img = qrcode.make(get_instance().get_wifi_qr_data(ssid, password, band_id, hidden))
    buffer = BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)
    return HttpResponse(buffer, content_type='image/png')

# MOXIE - View Moxie Params and config
class MoxieView(generic.DetailView):
    template_name = "hive/moxie.html"
    model = MoxieDevice

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_config'] = get_instance().robot_data().get_config_for_device(self.object)
        context['schedules'] = MoxieSchedule.objects.all()
        return context

# MOXIE-POST - Save changes to a Moxie record
@require_http_methods(["POST"])
def moxie_edit(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        
        # Validate and sanitize inputs
        moxie_name = sanitize_input(request.POST.get("moxie_name", ""), max_length=200)
        validate_device_name(moxie_name)
        
        # Validate numeric inputs
        try:
            screen_brightness = float(request.POST.get("screen_brightness", 0.5))
            if not (0.0 <= screen_brightness <= 1.0):
                raise ValueError("Screen brightness must be between 0.0 and 1.0")
                
            audio_volume = float(request.POST.get("audio_volume", 0.5))
            if not (0.0 <= audio_volume <= 1.0):
                raise ValueError("Audio volume must be between 0.0 and 1.0")
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid numeric value in moxie_edit: {str(e)}")
            return redirect('hive:dashboard_alert', alert_message=f'Invalid input: {str(e)}')
        
        # Validate schedule
        schedule_pk = request.POST.get("schedule")
        if schedule_pk:
            try:
                schedule = MoxieSchedule.objects.get(pk=int(schedule_pk))
            except (MoxieSchedule.DoesNotExist, ValueError):
                logger.warning(f"Invalid schedule ID: {schedule_pk}")
                return redirect('hive:dashboard_alert', alert_message='Invalid schedule selected')
        else:
            schedule = None
        
        # Validate nickname
        nickname = sanitize_input(request.POST.get("nickname", ""), max_length=50)
        
        # Validate pairing status
        pairing_status = request.POST.get("pairing_status", "paired")
        if pairing_status not in ["paired", "unpairing"]:
            pairing_status = "paired"
        
        # Apply changes to base model
        device.name = moxie_name
        device.schedule = schedule
        
        # Apply changes to json field inside config
        if device.robot_config is None:
            # robot_config optional, create a new one to hold these
            device.robot_config = {}
        
        device.robot_config["screen_brightness"] = screen_brightness
        device.robot_config["audio_volume"] = audio_volume
        
        if "child_pii" in device.robot_config:
            device.robot_config["child_pii"]["nickname"] = nickname
        else:
            device.robot_config["child_pii"] = {"nickname": nickname}
        
        # pairing/unpairing
        device.robot_config["pairing_status"] = pairing_status
        
        device.save()
        get_instance().handle_config_updated(device)
        
    except CustomValidationError as e:
        logger.warning(f"Validation error in moxie_edit for pk {pk}: {str(e)}")
        return redirect('hive:dashboard_alert', alert_message=f'Validation error: {str(e)}')
    except MoxieDevice.DoesNotExist:
        logger.warning(f"Moxie update for unfound pk {pk}")
        return redirect('hive:dashboard_alert', alert_message='Device not found')
    except Exception as e:
        logger.error(f"Unexpected error in moxie_edit for pk {pk}: {str(e)}")
        return redirect('hive:dashboard_alert', alert_message='An error occurred while updating the device')
    
    return HttpResponseRedirect(reverse("hive:dashboard"))

# MOXIE - Edit Moxie Face Customizations
class MoxieFaceView(generic.DetailView):
    template_name = "hive/face.html"
    model = MoxieDevice

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['assets'] = get_moxie_customization_groups()
        context['face_options'] = get_instance().robot_data().get_config_for_device(self.object).get('child_pii', {}).get('face_options', [])
        return context

# FACE-POST - Save changes to a Moxie Face
@require_http_methods(["POST"])
def face_edit(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        new_face = []
        for key in request.POST.keys():
            if key.startswith('asset_'):
                val = request.POST[key]
                if val != '--':
                    new_face.append(val)

        if "child_pii" in device.robot_config:
            device.robot_config["child_pii"]["face_options"] = new_face
        else:
            device.robot_config["child_pii"] = { "face_options": new_face }

        # Moxie-Unity keeps a cached record of face textture keyed by the 'id' field.  This
        # Sets a new unique id to invalidate any old/corrupt cached record
        suffix = ''
        if request.POST.get('child_recover'):
            device.robot_config["child_pii"]["id"] = str(uuid.uuid4())
            suffix = " - Created new child ID"

        device.save()
        get_instance().handle_config_updated(device)
        return redirect('hive:dashboard_alert', alert_message=f'Updated face for {device}{suffix}')
    except MoxieDevice.DoesNotExist as e:
        logger.warning("Moxie update for unfound pk {pk}")
        return redirect('hive:dashboard_alert', alert_message='No such Moxie')

# MOXIE - Puppeteer Moxie
class MoxiePuppetView(generic.DetailView):
    template_name = "hive/puppet.html"
    model = MoxieDevice

# Simple puppet command endpoint for testing
@csrf_exempt 
def puppet_command(request, pk):
    """Simple endpoint to send puppet commands without CSRF issues"""
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    
    try:
        device = MoxieDevice.objects.get(pk=pk)
        command = request.POST.get('command')
        
        if command == 'speak':
            speech = request.POST.get('speech', '')
            mood = request.POST.get('mood', 'neutral')
            intensity = float(request.POST.get('intensity', '0.5'))
            
            server = get_instance()
            result = server.send_telehealth_speech(device.device_id, speech, mood, intensity)
            
            return JsonResponse({
                'result': 'success', 
                'message': f'Sent speech command: {speech}',
                'device': device.device_id
            })
        elif command == 'interrupt':
            server = get_instance()
            server.send_telehealth_interrupt(device.device_id)
            return JsonResponse({'result': 'success', 'message': 'Sent interrupt command'})
        else:
            return JsonResponse({'result': 'error', 'message': f'Unknown command: {command}'})
            
    except MoxieDevice.DoesNotExist:
        return JsonResponse({'result': 'error', 'message': 'Device not found'})
    except Exception as e:
        return JsonResponse({'result': 'error', 'message': str(e)})

# PUPPET API - Handle AJAX calls from puppet view
# Note: CSRF exempted for puppet mode functionality
@csrf_exempt
def puppet_api(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        if request.method == 'GET':
            # Handle GET request
            result = {
                "online": get_instance().robot_data().device_online(device.device_id),
                "puppet_state": get_instance().robot_data().get_puppet_state(device.device_id),
                "puppet_enabled": device.robot_config.get("moxie_mode") == "TELEHEALTH" if device.robot_config else False
            }
            return JsonResponse(result)
        elif request.method == 'POST':
            # Handle COMMANDS request
            if not device.robot_config:
                device.robot_config = {}
            cmd = request.POST['command']
            if cmd == "enable":
                device.robot_config["moxie_mode"] = "TELEHEALTH"
                device.save()
                get_instance().handle_config_updated(device)
            elif cmd == "disable":
                device.robot_config.pop("moxie_mode", None)
                device.save()
                get_instance().handle_config_updated(device)
            elif cmd == "interrupt":
                get_instance().send_telehealth_interrupt(device.device_id)
            elif cmd == "speak":
                speech = request.POST.get('speech', '')
                markup = request.POST.get('markup', '')
                if markup:
                    # Use custom markup (text will be empty in markup mode)
                    get_instance().send_telehealth_markup(device.device_id, markup, speech)
                else:
                    # Use auto-generated markup from text
                    get_instance().send_telehealth_speech(device.device_id, speech,
                                                          request.POST['mood'], float(request.POST['intensity']))
        return JsonResponse({'result': True})
    except MoxieDevice.DoesNotExist as e:
        logger.warning("Moxie puppet speak for unfound pk {pk}")
        return HttpResponseBadRequest()

# MOXIE - View Moxie Mission Sets to Complete
class MoxieMissionsView(generic.DetailView):
    template_name = "hive/missions.html"
    model = MoxieDevice

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # list of tupes (key,prettykey)
        context['mission_sets'] = [ (key, key.replace("_", " ")) for key in DM_MISSION_CONTENT_IDS.keys() ]
        return context

# MOXIE-POST - Save changes to a Moxie record
@require_http_methods(["POST"])
def mission_edit(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)

        mission_action = request.POST["mission_action"]
        if mission_action == "reset":
            # Delete all MBH to start fresh
            MentorBehavior.objects.filter(device=device).delete()
            msg = f'Reset ALL progress for {device}'
        else:
            # Handle mission set actions... get all the CIDs for the selected sets
            mission_sets = request.POST.getlist("mission_sets")
            dm_cid_list = [cid for ms in mission_sets for cid in DM_MISSION_CONTENT_IDS.get(ms, [])]
            if mission_action == "forget":
                # Delete any records with these module/content ID (completed, quit)
                MentorBehavior.objects.filter(device=device, module_id='DM', content_id__in=dm_cid_list).delete()
                msg = f'Forgot {len(mission_sets)} Daily Mission Sets ({len(dm_cid_list)} missions) for {device}'
            else: # == "complete"
                # Create new completions for all these mission content IDs
                get_instance().robot_data().add_mbh_completion_bulk(device.device_id, module_id="DM", content_id_list=dm_cid_list)
                msg = f'Completed {len(mission_sets)} Daily Mission Sets ({len(dm_cid_list)} missions) for {device}'

        return redirect('hive:dashboard_alert', alert_message=msg)
    except MoxieDevice.DoesNotExist as e:
        logger.warning("Moxie update for unfound pk {pk}")
        return redirect('hive:dashboard_alert', alert_message='No such Moxie')

# WAKE UP A MOXIE THAT IS USING WAKE BUTTON
def moxie_wake(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        logger.info(f'Waking up {device}')
        alert_msg = "Wake message sent!" if get_instance().send_wakeup_to_bot(device.device_id) else 'Moxie was offline.'
        return redirect('hive:dashboard_alert', alert_message=alert_msg)
    except MoxieDevice.DoesNotExist as e:
        logger.warning("Moxie wake for unfound pk {pk}")
        return redirect('hive:dashboard_alert', alert_message='No such Moxie')

# MOXIE - Export Moxie Content Data - Selection View
class ExportDataView(generic.TemplateView):
    template_name = "hive/export.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conversations'] = SinglePromptChat.objects.all()
        context['schedules'] = MoxieSchedule.objects.all()
        context['globals'] = GlobalResponse.objects.all()
        return context

# MOXIE - Export Moxie Content Data - Save Action
@require_http_methods(["POST"])
def export_data(request):
    content_name = request.POST['content_name']
    content_details = request.POST['content_details']
    globals = request.POST.getlist("globals")
    schedules = request.POST.getlist("schedules")
    conversations = request.POST.getlist("conversations")
    if not content_name:
        content_name = 'moxie_content'
    output = { "name": content_name, "details": content_details }
    for pk in globals:
        r = GlobalResponse.objects.get(pk=pk)
        rec = model_to_dict(r, exclude=['id'])
        output["globals"] = output.get("globals", []) + [rec]
    for pk in schedules:
        r = MoxieSchedule.objects.get(pk=pk)
        rec = model_to_dict(r, exclude=['id'])
        output["schedules"] = output.get("schedules", []) + [rec]
    for pk in conversations:
        r = SinglePromptChat.objects.get(pk=pk)
        rec = model_to_dict(r, exclude=['id'])
        output["conversations"] = output.get("conversations", []) + [rec]
    # Save output as JSON file
    response = JsonResponse(output, json_dumps_params={'indent': 4})
    response['Content-Disposition'] = f'attachment; filename="{content_name}.json"'
    return response

# MOXIE - Import Moxie Content Data
@require_http_methods(['POST'])
def upload_import_data(request):
    json_file = request.FILES.get('json_file')
    if not json_file:
        return JsonResponse({'error': 'No file uploaded'}, status=400)

    try:
        json_data = json.loads(json_file.read().decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON file'}, status=400)

    # Preprocess the JSON data to build the context for the template
    update_import_status(json_data)
    context = {
        'json_data': json_data,
        'json_data_str': json.dumps(json_data)
        # Add other context variables as needed
    }
    return render(request, 'hive/import.html', context)

@require_http_methods(['POST'])
def import_data(request):
    # these hold indexes into the source JSON arrays that we want to import
    g_list = request.POST.getlist("globals")
    s_list = request.POST.getlist("schedules")
    c_list = request.POST.getlist("conversations")
    # the original JSON upload, passed back to us
    jstring = request.POST.get("json_data")
    logger.info(f'IMPORTING {jstring}')
    json_data = json.loads(jstring)
    # finally import the data
    message = import_content(json_data, g_list, s_list, c_list)
    # and refresh all things
    get_instance().update_from_database()
    return redirect('hive:dashboard_alert', alert_message=message)

# MOXIE - View Moxie Data
class MoxieDataView(generic.DetailView):
    template_name = "hive/moxie_data.html"
    model = MoxieDevice

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_config'] = json.dumps(get_instance().robot_data().get_config_for_device(self.object))
        context['persist_data'] = json.dumps(get_instance().robot_data().get_persist_for_device(self.object))
        return context


# PUBLIC API - Text Markup Endpoint
@require_api_key
@rate_limit(max_requests=30, window_seconds=60)
@require_http_methods(['POST'])
def public_markup_api(request):
    """
    Public API endpoint for text markup processing.
    Accepts JSON with 'text' field and optional 'mood' and 'intensity' fields.
    Returns JSON with 'markup' field containing the processed markup.
    """
    try:
        # Parse JSON request
        data = json.loads(request.body.decode('utf-8'))
        
        # Validate required fields
        if 'text' not in data:
            return JsonResponse({
                'error': 'Missing required field: text'
            }, status=400)
        
        text = data['text']
        if not text or not isinstance(text, str):
            return JsonResponse({
                'error': 'Text field must be a non-empty string'
            }, status=400)
        
        # Extract optional mood and intensity parameters
        mood = data.get('mood')
        intensity = data.get('intensity')
        mood_and_intensity = None
        
        if mood is not None:
            if not isinstance(mood, str):
                return JsonResponse({
                    'error': 'Mood must be a string'
                }, status=400)
            
            # Default intensity to 0.5 if mood is provided but intensity is not
            if intensity is None:
                intensity = 0.5
            
            if not isinstance(intensity, (int, float)) or intensity < 0 or intensity > 1:
                return JsonResponse({
                    'error': 'Intensity must be a number between 0 and 1'
                }, status=400)
            
            mood_and_intensity = (mood, float(intensity))
        
        # Process the text through automarkup
        rules = get_automarkup_rules()
        markup_result = automarkup_process(text, rules, mood_and_intensity=mood_and_intensity)
        
        # Return the result
        return JsonResponse({
            'text': text,
            'markup': markup_result,
            'mood': mood,
            'intensity': intensity
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        logger.error(f"Error in public markup API: {str(e)}")
        return JsonResponse({
            'error': 'Internal server error'
        }, status=500)

# MOXIE - DJ Control Panel
class MoxieDJPanelView(generic.DetailView):
    template_name = "hive/dj_panel.html"
    model = MoxieDevice

# DJ PANEL API - Handle AJAX calls from DJ panel
# Note: This uses Django's default CSRF protection for session-based requests
# Simple DJ command endpoint for testing without CSRF issues
@csrf_exempt 
def dj_command(request, pk):
    """Simple endpoint to send DJ commands without CSRF issues"""
    import json  # Move json import to function level
    
    if request.method != 'POST':
        return HttpResponseBadRequest('POST required')
    
    try:
        device = MoxieDevice.objects.get(pk=pk)
        
        # Handle both form data and JSON data
        if request.content_type == 'application/json':
            logger.info(f"Parsing JSON request body: {request.body}")
            data = json.loads(request.body)
            cmd = data.get('command')
            logger.info(f"Extracted command from JSON: {cmd}")
        else:
            data = request.POST
            cmd = request.POST.get('command')
            logger.info(f"Extracted command from POST: {cmd}")
        
        if not device.robot_config:
            device.robot_config = {}
        
        if cmd == "enable":
            device.robot_config["moxie_mode"] = "TELEHEALTH"
            device.save()
            get_instance().handle_config_updated(device)
        elif cmd == "disable":
            device.robot_config.pop("moxie_mode", None)
            device.save()
            get_instance().handle_config_updated(device)
        elif cmd == "interrupt":
            get_instance().send_telehealth_interrupt(device.device_id)
        elif cmd == "speak":
            text = data.get('text', '')
            markup = data.get('markup', '')
            if markup:
                get_instance().send_telehealth_markup(device.device_id, markup, text)
            else:
                mood = data.get('mood', 'neutral')
                intensity = float(data.get('intensity', 0.5))
                get_instance().send_telehealth_speech(device.device_id, text, mood, intensity)
        elif cmd == "quick_action":
            action = data.get('action')
            dj_handle_quick_action(device.device_id, action)
        elif cmd == "behavior":
            behavior_name = data.get('behavior_name')
            dj_handle_behavior(device.device_id, behavior_name)
        elif cmd == "sound_effect":
            sound_name = data.get('sound_name')
            volume = float(data.get('volume', 0.75))
            dj_handle_sound_effect(device.device_id, sound_name, volume)
        elif cmd == "preset":
            preset_name = data.get('preset_name')
            dj_handle_preset(device.device_id, preset_name)
        elif cmd == "sequence":
            sequence_name = data.get('sequence_name')
            dj_handle_sequence(device.device_id, sequence_name)
        elif cmd == "play_custom_sequence":
            sequence_data_raw = data.get('sequence_data')
            if isinstance(sequence_data_raw, str):
                sequence_data = json.loads(sequence_data_raw)
            else:
                sequence_data = sequence_data_raw or []
            dj_handle_custom_sequence(device.device_id, sequence_data)
        elif cmd == "save_sequence":
            sequence_name = data.get('sequence_name')
            sequence_data_raw = data.get('sequence_data')
            if isinstance(sequence_data_raw, str):
                sequence_data = json.loads(sequence_data_raw)
            else:
                sequence_data = sequence_data_raw or []
            result = dj_save_sequence(device, sequence_name, sequence_data)
            return JsonResponse(result)
        elif cmd == "load_sequence":
            sequence_name = data.get('sequence_name')
            result = dj_load_sequence(device, sequence_name)
            return JsonResponse(result)
        elif cmd == "list_sequences":
            result = dj_list_sequences(device)
            return JsonResponse(result)
        elif cmd == "play_macro":
            macro_actions_raw = data.get('macro_actions')
            if isinstance(macro_actions_raw, str):
                macro_actions = json.loads(macro_actions_raw)
            else:
                macro_actions = macro_actions_raw or []
            dj_handle_play_macro(device.device_id, macro_actions)
        elif cmd == "delete_sequence":
            sequence_name = data.get('sequence_name')
            result = dj_delete_sequence(device, sequence_name)
            return JsonResponse(result)
        else:
            return JsonResponse({'result': 'error', 'message': f'Unknown command: {cmd}'})
            
        return JsonResponse({'result': 'success', 'message': f'Executed command: {cmd}'})
        
    except MoxieDevice.DoesNotExist:
        return JsonResponse({'result': 'error', 'message': 'Device not found'})
    except Exception as e:
        logger.error(f"Error in DJ command API: {str(e)}")
        return JsonResponse({'result': 'error', 'message': str(e)})

def dj_panel_api(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        if request.method == 'GET':
            # Handle GET request - return status
            result = {
                "online": get_instance().robot_data().device_online(device.device_id),
                "dj_state": get_instance().robot_data().get_puppet_state(device.device_id),
                "dj_enabled": device.robot_config.get("moxie_mode") == "TELEHEALTH" if device.robot_config else False
            }
            return JsonResponse(result)
        elif request.method == 'POST':
            # Handle DJ command requests
            if not device.robot_config:
                device.robot_config = {}
            
            cmd = request.POST['command']
            
            if cmd == "enable":
                device.robot_config["moxie_mode"] = "TELEHEALTH"
                device.save()
                get_instance().handle_config_updated(device)
            elif cmd == "disable":
                device.robot_config.pop("moxie_mode", None)
                device.save()
                get_instance().handle_config_updated(device)
            elif cmd == "interrupt":
                get_instance().send_telehealth_interrupt(device.device_id)
            elif cmd == "speak":
                text = request.POST.get('text', '')
                markup = request.POST.get('markup', '')
                if markup:
                    get_instance().send_telehealth_markup(device.device_id, markup, text)
                else:
                    mood = request.POST.get('mood', 'neutral')
                    intensity = float(request.POST.get('intensity', 0.5))
                    get_instance().send_telehealth_speech(device.device_id, text, mood, intensity)
            elif cmd == "quick_action":
                action = request.POST.get('action')
                dj_handle_quick_action(device.device_id, action)
            elif cmd == "behavior":
                behavior_name = request.POST.get('behavior_name')
                dj_handle_behavior(device.device_id, behavior_name)
            elif cmd == "sound_effect":
                sound_name = request.POST.get('sound_name')
                volume = float(request.POST.get('volume', 0.75))
                dj_handle_sound_effect(device.device_id, sound_name, volume)
            elif cmd == "preset":
                preset_name = request.POST.get('preset_name')
                dj_handle_preset(device.device_id, preset_name)
            elif cmd == "sequence":
                sequence_name = request.POST.get('sequence_name')
                dj_handle_sequence(device.device_id, sequence_name)
            elif cmd == "play_custom_sequence":
                sequence_data = json.loads(request.POST.get('sequence_data', '[]'))
                dj_handle_custom_sequence(device.device_id, sequence_data)
            elif cmd == "save_sequence":
                sequence_name = request.POST.get('sequence_name')
                sequence_data = json.loads(request.POST.get('sequence_data', '[]'))
                result = dj_save_sequence(device, sequence_name, sequence_data)
                return JsonResponse(result)
            elif cmd == "load_sequence":
                sequence_name = request.POST.get('sequence_name')
                result = dj_load_sequence(device, sequence_name)
                return JsonResponse(result)
            elif cmd == "list_sequences":
                result = dj_list_sequences(device)
                return JsonResponse(result)
            elif cmd == "play_macro":
                macro_actions = json.loads(request.POST.get('macro_actions', '[]'))
                dj_handle_play_macro(device.device_id, macro_actions)
            elif cmd == "delete_sequence":
                sequence_name = request.POST.get('sequence_name')
                result = dj_delete_sequence(device, sequence_name)
                return JsonResponse(result)
                
        return JsonResponse({'result': True})
    except MoxieDevice.DoesNotExist as e:
        logger.warning(f"Moxie DJ panel for unfound pk {pk}")
        return HttpResponseBadRequest()
    except Exception as e:
        logger.error(f"Error in DJ panel API: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# DJ Panel Helper Functions
def dj_handle_quick_action(device_id, action):
    """Handle quick action buttons like celebrate, dance, laugh, etc."""
    behavior = get_quick_action_behavior(action)
    # Use the detailed behavior handler which has full markup commands
    dj_handle_behavior(device_id, behavior)

def dj_handle_behavior(device_id, behavior_name):
    """Handle direct behavior tree execution with detailed markup"""
    markup = get_behavior_markup(behavior_name)
    get_instance().send_telehealth_markup(device_id, markup)

def dj_handle_sound_effect(device_id, sound_name, volume):
    """Handle sound effect playback"""
    markup = get_sound_effect_markup(sound_name, volume)
    get_instance().send_telehealth_markup(device_id, markup)

def dj_handle_preset(device_id, preset_name):
    """Handle preset combinations of actions"""
    preset = get_preset_actions(preset_name)
    for action_type, params in preset:
        if action_type == 'speak':
            get_instance().send_telehealth_speech(device_id, 
                                                 params['text'], 
                                                 params['mood'], 
                                                 params['intensity'])
        elif action_type == 'behavior':
            dj_handle_behavior(device_id, params['behavior_name'])
        elif action_type == 'sound_effect':
            dj_handle_sound_effect(device_id, params['sound_name'], params['volume'])
        elif action_type == 'sequence':
            dj_handle_sequence(device_id, params['sequence_name'])
        # Add small delay between actions
        import time
        time.sleep(0.5)

def dj_handle_welcome_test_sequence(device_id):
    """Handle the welcome test sequence with individual commands and timing"""
    import threading
    import time
    
    def run_sequence():
        # Step 1: Wave behavior
        logger.info(f"Welcome test: Starting wave behavior for device {device_id}")
        dj_handle_behavior(device_id, 'Bht_Wait_Hug')
        time.sleep(3)  # Wait for wave to complete
        
        # Step 2: Clear throat behavior  
        logger.info(f"Welcome test: Starting clear throat behavior for device {device_id}")
        dj_handle_behavior(device_id, 'Bht_Vg_Clear_Throat')
        time.sleep(2)  # Wait for clear throat to complete
        
        # Step 3: Welcome speech
        logger.info(f"Welcome test: Starting welcome speech for device {device_id}")
        get_instance().send_telehealth_speech(
            device_id, 
            "Welcome my friends! Your love and stories make me so happy! Now you can talk with me directly. I can't wait to see what you share with me!",
            'happy',
            0.7
        )
        logger.info(f"Welcome test: Sequence completed for device {device_id}")
    
    # Run sequence in background thread so it doesn't block
    thread = threading.Thread(target=run_sequence)
    thread.daemon = True
    thread.start()

def dj_handle_sequence(device_id, sequence_name):
    """Handle predefined sequences of behaviors and speech"""
    # Handle welcome_test as a special case with individual commands
    if sequence_name == 'welcome_test':
        dj_handle_welcome_test_sequence(device_id)
        return
    
    sequence_markup = get_sequence_markup(sequence_name)
    if sequence_markup:
        get_instance().send_telehealth_markup(device_id, sequence_markup)
    else:
        logger.warning(f"Unknown sequence: {sequence_name}")

def dj_handle_custom_sequence(device_id, sequence_data):
    """Handle custom sequence from sequence designer"""
    if not sequence_data:
        logger.warning("Empty sequence data")
        return
    
    import threading
    import time
    
    def run_sequence():
        """Run the sequence in a background thread to avoid blocking"""
        logger.info(f"Starting custom sequence playback for device {device_id} with {len(sequence_data)} items")
        
        # Track current emotional state for the sequence
        current_mood = 'neutral'
        current_intensity = 0.5
        
        for i, item in enumerate(sequence_data):
            logger.info(f"Executing sequence item {i+1}/{len(sequence_data)}: {item}")
            
            item_type = item.get('type')
            if item_type == 'behavior':
                dj_handle_behavior(device_id, item.get('value'))
                # Add small delay after behaviors to let them start
                time.sleep(0.5)
            elif item_type == 'set_emotion':
                # Update current emotional state
                emotion_value = item.get('value', {})
                if emotion_value.get('mood'):
                    current_mood = emotion_value.get('mood')
                if emotion_value.get('intensity') is not None:
                    current_intensity = float(emotion_value.get('intensity'))
                logger.info(f"Updated emotion state: mood={current_mood}, intensity={current_intensity}")
            elif item_type == 'speech':
                # Use emotion from item if provided, otherwise use current sequence emotion
                mood = item.get('mood', current_mood)
                intensity = float(item.get('intensity', current_intensity))
                logger.info(f"Speaking with emotion: mood={mood}, intensity={intensity}, text='{item.get('value')}'")
                get_instance().send_telehealth_speech(device_id, item.get('value'), mood, intensity)
                # Add delay after speech to let it complete
                time.sleep(2.0)
            elif item_type == 'sound':
                volume = float(item.get('volume', 0.75))
                dj_handle_sound_effect(device_id, item.get('value'), volume)
                # Add small delay after sound effects
                time.sleep(0.5)
            elif item_type == 'pause':
                pause_duration = float(item.get('value', 1.0))
                logger.info(f"Pausing for {pause_duration} seconds")
                time.sleep(pause_duration)
                
            # Add small delay between items to prevent overwhelming the robot
            if i < len(sequence_data) - 1:  # Don't delay after the last item
                time.sleep(0.2)
        
        logger.info(f"Custom sequence completed for device {device_id}")
    
    # Start the sequence in a background thread
    thread = threading.Thread(target=run_sequence)
    thread.daemon = True
    thread.start()
    
    logger.info(f"Custom sequence started in background thread for device {device_id}")

def dj_save_sequence(device, sequence_name, sequence_data):
    """Save a custom sequence to device configuration"""
    try:
        if not device.robot_config:
            device.robot_config = {}
        
        if 'custom_sequences' not in device.robot_config:
            device.robot_config['custom_sequences'] = {}
        
        device.robot_config['custom_sequences'][sequence_name] = {
            'name': sequence_name,
            'sequence': sequence_data,
            'created_at': timezone.now().isoformat()
        }
        
        device.save()
        logger.info(f"Saved custom sequence '{sequence_name}' for device {device.device_id}")
        
        return {'success': True, 'message': f'Sequence "{sequence_name}" saved successfully'}
    except Exception as e:
        logger.error(f"Failed to save sequence: {str(e)}")
        return {'success': False, 'message': f'Failed to save sequence: {str(e)}'}

def dj_load_sequence(device, sequence_name):
    """Load a custom sequence from device configuration"""
    try:
        if not device.robot_config or 'custom_sequences' not in device.robot_config:
            return {'success': False, 'message': 'No saved sequences found'}
        
        sequences = device.robot_config['custom_sequences']
        if sequence_name not in sequences:
            return {'success': False, 'message': f'Sequence "{sequence_name}" not found'}
        
        sequence_data = sequences[sequence_name]
        logger.info(f"Loaded custom sequence '{sequence_name}' for device {device.device_id}")
        
        return {
            'success': True, 
            'message': f'Sequence "{sequence_name}" loaded successfully',
            'sequence': sequence_data['sequence']
        }
    except Exception as e:
        logger.error(f"Failed to load sequence: {str(e)}")
        return {'success': False, 'message': f'Failed to load sequence: {str(e)}'}

def dj_list_sequences(device):
    """List all saved custom sequences for device"""
    try:
        if not device.robot_config or 'custom_sequences' not in device.robot_config:
            return {'success': True, 'sequences': []}
        
        sequences = device.robot_config['custom_sequences']
        sequence_list = []
        
        for name, data in sequences.items():
            sequence_list.append({
                'name': name,
                'created_at': data.get('created_at'),
                'steps': len(data.get('sequence', []))
            })
        
        return {'success': True, 'sequences': sequence_list}
    except Exception as e:
        logger.error(f"Failed to list sequences: {str(e)}")
        return {'success': False, 'message': f'Failed to list sequences: {str(e)}'}

def dj_delete_sequence(device, sequence_name):
    """Delete a custom sequence from device configuration"""
    try:
        if not device.robot_config or 'custom_sequences' not in device.robot_config:
            return {'success': False, 'message': 'No saved sequences found'}
        
        sequences = device.robot_config['custom_sequences']
        if sequence_name not in sequences:
            return {'success': False, 'message': f'Sequence "{sequence_name}" not found'}
        
        # Delete the sequence
        del sequences[sequence_name]
        device.save()
        
        logger.info(f"Deleted custom sequence '{sequence_name}' for device {device.device_id}")
        
        return {'success': True, 'message': f'Sequence "{sequence_name}" deleted successfully'}
    except Exception as e:
        logger.error(f"Failed to delete sequence: {str(e)}")
        return {'success': False, 'message': f'Failed to delete sequence: {str(e)}'}

def dj_handle_play_macro(device_id, macro_actions):
    """Handle playback of recorded macro sequences"""
    for action_data in macro_actions:
        cmd = action_data.get('command')
        if cmd == 'speak':
            text = action_data.get('text', '')
            markup = action_data.get('markup', '')
            if markup:
                get_instance().send_telehealth_markup(device_id, markup, text)
            else:
                mood = action_data.get('mood', 'neutral')
                intensity = action_data.get('intensity', 0.5)
                get_instance().send_telehealth_speech(device_id, text, mood, intensity)
        elif cmd == 'quick_action':
            dj_handle_quick_action(device_id, action_data.get('action'))
        elif cmd == 'behavior':
            dj_handle_behavior(device_id, action_data.get('behavior_name'))
        elif cmd == 'sound_effect':
            dj_handle_sound_effect(device_id, action_data.get('sound_name'), action_data.get('volume', 0.75))
        elif cmd == 'preset':
            dj_handle_preset(device_id, action_data.get('preset_name'))
        
        # Add delay between macro actions
        import time
        time.sleep(0.3)

# ANIMATION TESTER - Load animations from CSV and provide testing interface
class AnimationTesterView(generic.DetailView):
    template_name = "hive/animation_tester.html"
    model = MoxieDevice
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        animations = self.load_animations_from_session()
        context['total_animations'] = len(animations)
        context['has_uploaded_file'] = len(animations) > 0
        return context
    
    def load_animations_from_session(self):
        """Load animations from uploaded file in session"""
        # Get animations from session (already parsed and stored)
        animations = self.request.session.get('animations_data', [])
        return animations

# ANIMATION TESTER API - Handle AJAX calls from animation tester
# Note: This uses Django's default CSRF protection for session-based requests
def animation_tester_api(request, pk):
    try:
        device = MoxieDevice.objects.get(pk=pk)
        
        if request.method == 'GET':
            # Return status information
            result = {
                "online": get_instance().robot_data().device_online(device.device_id),
                "device_name": device.name
            }
            return JsonResponse(result)
            
        elif request.method == 'POST':
            cmd = request.POST['command']
            
            if cmd == "test_animation":
                # Send animation to robot
                animation_name = request.POST.get('animation_name')
                markup = request.POST.get('markup', '')
                
                if markup:
                    # Use provided markup
                    get_instance().send_telehealth_markup(device.device_id, markup)
                else:
                    # Generate markup for behavior tree command
                    generated_markup = f'<mark name="cmd:behaviour-tree,data:{{+transition+:0.3,+duration+:2.0,+repeat+:1,+layerBlendInTime+:0.4,+layerBlendOutTime+:0.4,+blocking+:false,+action+:0,+eventName+:+Gesture_None+,+category+:+None+,+behaviour+:+{animation_name}+,+Track+:++}}"/>'
                    get_instance().send_telehealth_markup(device.device_id, generated_markup)
                
                logger.info(f"Sent animation {animation_name} to device {device.device_id}")
                return JsonResponse({'result': 'Animation sent', 'animation': animation_name})
                
            elif cmd == "mark_result":
                # Store test result in session
                animation_id = request.POST.get('animation_id')
                result = request.POST.get('result')  # 'yes' or 'no'
                
                # Initialize session data if needed
                if 'animation_results' not in request.session:
                    request.session['animation_results'] = {}
                
                request.session['animation_results'][animation_id] = result
                request.session.modified = True
                
                logger.info(f"Marked animation {animation_id} as {result}")
                return JsonResponse({'result': 'Result saved', 'animation_id': animation_id, 'test_result': result})
                
            elif cmd == "get_results":
                # Return current test results
                results = request.session.get('animation_results', {})
                return JsonResponse({'results': results})
                
            elif cmd == "clear_results":
                # Clear all test results
                request.session['animation_results'] = {}
                request.session.modified = True
                return JsonResponse({'result': 'Results cleared'})
                
            elif cmd == "clear_single_result":
                # Clear result for a single animation
                animation_id = request.POST.get('animation_id')
                if 'animation_results' in request.session and animation_id in request.session['animation_results']:
                    del request.session['animation_results'][animation_id]
                    request.session.modified = True
                    logger.info(f"Cleared result for animation {animation_id}")
                return JsonResponse({'result': 'Single result cleared', 'animation_id': animation_id})
                
            elif cmd == "get_animations":
                # Return animations data safely
                animations = request.session.get('animations_data', [])
                return JsonResponse({'animations': animations})
        
        return JsonResponse({'result': True})
        
    except MoxieDevice.DoesNotExist:
        logger.warning(f"Animation tester for unfound device pk {pk}")
        return HttpResponseBadRequest()
    except Exception as e:
        logger.error(f"Error in animation tester API: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

# ANIMATION RESULTS DOWNLOAD - Export test results as CSV
def animation_results_download(request, pk):
    """Download animation test results as CSV"""
    try:
        device = MoxieDevice.objects.get(pk=pk)
        
        # Load original animations from session
        animations = request.session.get('animations_data', [])
        
        if not animations:
            return HttpResponseBadRequest("No animation data found. Please upload a CSV file first.")
        
        # Get test results from session
        results = request.session.get('animation_results', {})
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="animation_test_results_{device.name}.csv"'
        
        writer = csv.writer(response)
        # Write header with new 'Worked' column
        writer.writerow(['File Name', 'Markup', 'Does it work?', 'Function', 'Notes/Observations', 'Video Recording', 'Test Result'])
        
        # Write animation data with test results
        for animation in animations:
            animation_id = str(animation['id'])
            worked_result = results.get(animation_id, '')
            
            # Convert yes/no to more readable format
            if worked_result == 'yes':
                test_result = 'Working'
            elif worked_result == 'no':
                test_result = 'Not Working'
            else:
                test_result = 'Not Tested'
            
            writer.writerow([
                animation['file_name'],
                animation['markup'],
                animation.get('does_it_work', ''),  # Original column data
                animation['function'],
                animation['notes'],
                animation['video_recording'],
                test_result
            ])
        
        return response
        
    except MoxieDevice.DoesNotExist:
        return HttpResponseBadRequest("Device not found")
    except Exception as e:
        logger.error(f"Error downloading animation results: {str(e)}")
        return HttpResponseBadRequest(str(e))

# ANIMATION CSV UPLOAD - Handle animation CSV file uploads
@require_http_methods(["POST"])
def upload_animation_csv(request):
    """Handle animation CSV file upload"""
    try:
        if 'animation_file' not in request.FILES:
            return redirect('hive:dashboard_alert', alert_message='No file uploaded.')
        
        animation_file = request.FILES['animation_file']
        
        # Validate file type
        if not (csv_file.name.endswith('.csv') or csv_file.name.endswith('.tsv')):
            return redirect('hive:dashboard_alert', alert_message='Please upload a CSV or TSV file.')
        
        # Read and parse CSV content with encoding detection
        raw_content = csv_file.read()
        
        # Try different encodings with fallback
        encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
        csv_content = None
        
        for encoding in encodings:
            try:
                csv_content = raw_content.decode(encoding)
                logger.info(f"Successfully decoded file using {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        
        if csv_content is None:
            return redirect('hive:dashboard_alert', alert_message='Could not decode file. Please ensure it uses UTF-8 encoding.')
        logger.info(f"Uploaded CSV file: {csv_file.name}, size: {len(csv_content)} chars")
        logger.info(f"CSV content preview: {csv_content[:300]}...")
        
        animations = parse_animation_csv_content(csv_content)
        
        if not animations:
            logger.warning(f"No animations parsed from file {animation_file.name}")
            return redirect('hive:dashboard_alert', alert_message=f'No valid animations found in file. Check that it uses tab (TSV), comma (CSV), or pipe delimiters and has the correct headers: File Name, Markup, Does it work?, Function, Notes/Observations, Video Recording')
        
        # Store in session for use in animation tester (only store parsed data)
        request.session['animation_file_name'] = animation_file.name
        request.session['animation_count'] = len(animations)
        request.session['animations_data'] = animations
        request.session.modified = True
        
        logger.info(f"Uploaded animation CSV with {len(animations)} animations")
        return redirect('hive:dashboard_alert', alert_message=f'Successfully uploaded {len(animations)} animations from {animation_file.name}')
        
    except Exception as e:
        logger.error(f"Error uploading animation CSV: {str(e)}")
        return redirect('hive:dashboard_alert', alert_message=f'Error processing CSV file: {str(e)}')

# CLEAR ANIMATION CSV - Clear uploaded animation CSV from session
def clear_animation_csv(request):
    """Clear uploaded animation file from session"""
    request.session.pop('animation_file_name', None)
    request.session.pop('animation_count', None)
    request.session.pop('animations_data', None)
    request.session.pop('animation_results', None)
    request.session.modified = True
    
    return redirect('hive:dashboard_alert', alert_message='Animation file cleared.')

# HELPER FUNCTION - Parse animation CSV content
def parse_animation_csv_content(csv_content):
    """Parse CSV content and return list of animations"""
    animations = []
    
    try:
        # Use StringIO to treat the string as a file-like object
        csv_file = io.StringIO(csv_content)
        
        # Try different delimiters: tab first (for TSV), then comma, then pipe
        delimiters = [('\t', 'tab'), (',', 'comma'), ('|', 'pipe')]
        reader = None
        
        for delimiter, name in delimiters:
            csv_file.seek(0)
            test_reader = csv.DictReader(csv_file, delimiter=delimiter)
            fieldnames = test_reader.fieldnames
            logger.info(f"Trying {name} delimiter, headers: {fieldnames}")
            
            if fieldnames and 'File Name' in fieldnames:
                csv_file.seek(0)
                reader = csv.DictReader(csv_file, delimiter=delimiter)
                logger.info(f"Successfully using {name} delimiter")
                break
        
        if not reader:
            logger.error("Could not find suitable delimiter for CSV file")
            return []
        
        animation_count = 0
        for i, row in enumerate(reader):
            # Get the file name and check if it exists
            file_name = row.get('File Name', '').strip()
            
            # Skip empty rows or header-like rows
            if not file_name or file_name == 'File Name':
                continue
                
            animation_count += 1
            animation = {
                'id': animation_count,
                'file_name': file_name,
                'markup': row.get('Markup', '').strip(),
                'function': row.get('Function', '').strip(),
                'notes': row.get('Notes/Observations', '').strip(),
                'video_recording': row.get('Video Recording', '').strip(),
                'does_it_work': row.get('Does it work?', '').strip()
            }
            animations.append(animation)
            
            # Debug: log first few animations
            if animation_count <= 3:
                logger.info(f"Parsed animation {animation_count}: {file_name}")
            
    except Exception as e:
        logger.error(f"Error parsing CSV content: {str(e)}")
        logger.error(f"CSV content preview: {csv_content[:200]}...")
        
    logger.info(f"Total animations parsed: {len(animations)}")
    return animations

