"""
CloudTTS Handler for processing CloudTTSRequest messages and responding with audio
"""
import logging
import time
import wave
import io
import struct
import tempfile
import os
from .moxie_zmq_handler import ZMQHandler
from .protos.embodied.unity.cloudtts_pb2 import CloudTTSRequest, CloudTTSResponse, AudioBuffer, TTSMark, RequestSourceType
from .ai_factory import create_openai

# OpenAI TTS Configuration
OPENAI_TTS_MODEL = 'tts-1'  # or 'tts-1-hd' for higher quality
OPENAI_TTS_VOICE = 'alloy'  # alloy, echo, fable, onyx, nova, shimmer
OPENAI_TTS_FORMAT = 'wav'   # wav, mp3, aac, opus, flac, pcm
OPENAI_TTS_SPEED = 1.0      # 0.25 to 4.0

logger = logging.getLogger(__name__)

def now_ms():
    return time.time_ns() // 1_000_000

class CloudTTSHandler(ZMQHandler):
    """
    Handler for CloudTTSRequest messages from the zmq topic.
    Responds with CloudTTSResponse containing audio data from WAV files.
    """
    
    def __init__(self, server):
        super().__init__(server)
        self._audio_cache = {}  # Cache for audio files if needed
        
    def handle_zmq(self, device_id, protoname, protodata):
        """Handle incoming CloudTTSRequest messages"""
        if protoname == "embodied.unity.CloudTTSRequest":
            try:
                request = CloudTTSRequest()
                request.ParseFromString(protodata)
                logger.info(f"Received CloudTTSRequest for device {device_id}, event_id: {request.event_id}")
                
                # Process the request and send response
                self._process_cloudtts_request(device_id, request)
                
            except Exception as e:
                logger.error(f"Error processing CloudTTSRequest: {e}")
    
    def _process_cloudtts_request(self, device_id, request):
        """Process CloudTTSRequest and generate CloudTTSResponse using OpenAI TTS"""
        try:
            start_time = now_ms()
            
            # Extract text from markup (remove SSML tags for now)
            text = self._extract_text_from_markup(request.markup)
            logger.info(f"Generating TTS for text: '{text}' (event_id: {request.event_id})")
            
            # Generate audio using OpenAI TTS
            audio_data, channels, sample_rate = self._generate_openai_tts(text)
            
            synthesis_time = now_ms() - start_time
            
            # Create CloudTTSResponse
            response = CloudTTSResponse()
            response.request_source = RequestSourceType.REMOTECHAT_TTS_REQUEST
            response.event_id = request.event_id
            response.chunk_num = request.chunk_num
            response.timestamp = now_ms()
            response.total_time = synthesis_time
            response.synthesis_time = synthesis_time
            response.software_version = request.software_version
            response.module_name = request.module_name
            
            # Set audio buffer
            response.audio.buffer = audio_data
            response.audio.channels = channels
            response.audio.sample_rate = sample_rate
            
            # Add basic viseme marks (could be enhanced with phoneme analysis)
            mark = response.marks.add()
            mark.time = 0
            mark.start = 0
            mark.end = len(text)
            mark.type = "word"
            mark.value = text
            
            # Send response back to device
            logger.info(f"Sending CloudTTSResponse for event_id: {request.event_id} (synthesis_time: {synthesis_time}ms)")
            self.zmq_reply(device_id, response)
            
        except Exception as e:
            logger.error(f"Error processing CloudTTS request: {e}")
            # Send error response if possible
            self._send_error_response(device_id, request, str(e))
    
    def _generate_openai_tts(self, text):
        """
        Generate audio using OpenAI TTS API
        
        Args:
            text: Text to synthesize
            
        Returns:
            tuple: (pcm_data, channels, sample_rate)
        """
        try:
            # Create OpenAI client
            client = create_openai()
            
            # Generate TTS audio
            logger.info(f"Calling OpenAI TTS API for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            
            response = client.audio.speech.create(
                model=OPENAI_TTS_MODEL,
                voice=OPENAI_TTS_VOICE,
                input=text,
                response_format=OPENAI_TTS_FORMAT,
                speed=OPENAI_TTS_SPEED
            )
            
            # Get audio data as bytes
            audio_bytes = response.content
            logger.info(f"OpenAI TTS generated {len(audio_bytes)} bytes of audio data")
            
            # Convert to PCM format
            return self._convert_audio_to_pcm(audio_bytes)
            
        except Exception as e:
            logger.error(f"Error generating OpenAI TTS: {e}")
            # Fallback to sample audio
            logger.info("Falling back to sample audio")
            return self._generate_sample_audio(), 1, 22050
    
    def _convert_audio_to_pcm(self, audio_bytes):
        """
        Convert audio bytes (WAV format) to PCM data
        
        Args:
            audio_bytes: Audio data in WAV format
            
        Returns:
            tuple: (pcm_data, channels, sample_rate)
        """
        try:
            # Create a temporary file to write the audio data
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file_path = temp_file.name
            
            try:
                # Load the WAV file and extract PCM data
                pcm_data, channels, sample_rate = self.load_wav_file(temp_file_path)
                return pcm_data, channels, sample_rate
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error converting audio to PCM: {e}")
            raise
    
    def _extract_text_from_markup(self, markup):
        """
        Extract plain text from SSML markup
        
        Args:
            markup: SSML markup string
            
        Returns:
            str: Plain text without markup tags
        """
        import re
        
        # Simple SSML tag removal (could be enhanced with proper SSML parsing)
        # Remove XML/SSML tags
        text = re.sub(r'<[^>]+>', '', markup)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _send_error_response(self, device_id, request, error_message):
        """
        Send an error response when TTS generation fails
        
        Args:
            device_id: Target device ID
            request: Original CloudTTSRequest
            error_message: Error description
        """
        try:
            # Generate a short error audio (silence)
            error_audio = self._generate_sample_audio()
            
            # Create error response
            response = CloudTTSResponse()
            response.request_source = RequestSourceType.REMOTECHAT_TTS_REQUEST
            response.event_id = request.event_id
            response.chunk_num = request.chunk_num
            response.timestamp = now_ms()
            response.total_time = 100
            response.synthesis_time = 0
            response.software_version = request.software_version
            response.module_name = request.module_name
            
            # Set minimal audio buffer (silence)
            response.audio.buffer = error_audio
            response.audio.channels = 1
            response.audio.sample_rate = 22050
            
            # Add error mark
            mark = response.marks.add()
            mark.time = 0
            mark.start = 0
            mark.end = len(error_message)
            mark.type = "error"
            mark.value = f"TTS Error: {error_message}"
            
            logger.info(f"Sending error CloudTTSResponse for event_id: {request.event_id}")
            self.zmq_reply(device_id, response)
            
        except Exception as e:
            logger.error(f"Error sending error response: {e}")
    
    def _generate_sample_audio(self):
        """Generate sample PCM audio data (fallback when TTS fails)"""
        # Generate 1 second of silence as PCM 16-bit mono at 22050 Hz
        sample_rate = 22050
        duration = 1.0  # seconds
        num_samples = int(sample_rate * duration)
        
        # Create silence
        audio_samples = [0] * num_samples
        
        # Convert to 16-bit PCM bytes
        pcm_data = b''.join(struct.pack('<h', sample) for sample in audio_samples)
        
        return pcm_data
    
    def load_wav_file(self, wav_file_path):
        """
        Load WAV file and extract PCM data for AudioBuffer
        
        Args:
            wav_file_path: Path to WAV file
            
        Returns:
            tuple: (pcm_data, channels, sample_rate)
        """
        try:
            with wave.open(wav_file_path, 'rb') as wav_file:
                # Get WAV parameters
                channels = wav_file.getnchannels()
                sample_rate = wav_file.getframerate()
                sample_width = wav_file.getsampwidth()
                num_frames = wav_file.getnframes()
                
                logger.info(f"Loading WAV: {channels} channels, {sample_rate}Hz, {sample_width} bytes/sample, {num_frames} frames")
                
                # Read all frames
                raw_audio = wav_file.readframes(num_frames)
                
                # Ensure 16-bit PCM format
                if sample_width != 2:
                    raise ValueError(f"Expected 16-bit audio, got {sample_width * 8}-bit")
                
                return raw_audio, channels, sample_rate
                
        except Exception as e:
            logger.error(f"Error loading WAV file {wav_file_path}: {e}")
            raise
    
    def create_cloudtts_response_from_wav(self, request, wav_file_path, viseme_marks=None):
        """
        Create CloudTTSResponse from WAV file
        
        Args:
            request: Original CloudTTSRequest
            wav_file_path: Path to WAV audio file
            viseme_marks: List of viseme timing marks (optional)
            
        Returns:
            CloudTTSResponse: Populated response message
        """
        try:
            # Load audio from WAV file
            pcm_data, channels, sample_rate = self.load_wav_file(wav_file_path)
            
            # Create response
            response = CloudTTSResponse()
            response.request_source = RequestSourceType.REMOTECHAT_TTS_REQUEST
            response.event_id = request.event_id
            response.chunk_num = request.chunk_num
            response.timestamp = now_ms()
            response.total_time = len(pcm_data) * 1000 // (sample_rate * channels * 2)  # milliseconds
            response.synthesis_time = 100  # milliseconds (simulated)
            response.software_version = request.software_version
            response.module_name = request.module_name
            
            # Set audio buffer
            response.audio.buffer = pcm_data
            response.audio.channels = channels
            response.audio.sample_rate = sample_rate
            
            # Add viseme marks if provided
            if viseme_marks:
                for mark_data in viseme_marks:
                    mark = response.marks.add()
                    mark.time = mark_data.get('time', 0)
                    mark.start = mark_data.get('start', 0)
                    mark.end = mark_data.get('end', 0)
                    mark.type = mark_data.get('type', 'word')
                    mark.value = mark_data.get('value', '')
            else:
                # Add default mark for entire text
                mark = response.marks.add()
                mark.time = 0
                mark.start = 0
                mark.end = len(request.markup)
                mark.type = "word"
                mark.value = request.markup
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating CloudTTSResponse from WAV: {e}")
            raise
    
    def send_audio_response(self, device_id, event_id, wav_file_path, markup_text="", viseme_marks=None):
        """
        Send CloudTTSResponse with audio from WAV file
        
        Args:
            device_id: Target device ID
            event_id: Event ID to match with request
            wav_file_path: Path to WAV audio file
            markup_text: Original markup text (optional)
            viseme_marks: List of viseme timing marks (optional)
        """
        try:
            # Create a mock request for response generation
            mock_request = CloudTTSRequest()
            mock_request.event_id = event_id
            mock_request.markup = markup_text
            mock_request.chunk_num = 0
            mock_request.timestamp = now_ms()
            mock_request.software_version = "openmoxie"
            mock_request.module_name = "cloudtts_handler"
            
            # Create response from WAV file
            response = self.create_cloudtts_response_from_wav(mock_request, wav_file_path, viseme_marks)
            
            # Send response
            logger.info(f"Sending CloudTTSResponse for event_id: {event_id} with audio from {wav_file_path}")
            self.zmq_reply(device_id, response)
            
        except Exception as e:
            logger.error(f"Error sending audio response: {e}")
