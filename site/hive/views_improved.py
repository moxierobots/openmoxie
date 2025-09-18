"""
Improved views with proper error handling and validation
This file contains fixes for the critical parts of views.py
"""
from django.forms import model_to_dict
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.views import generic
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
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
from .markup_validator import (
    validate_markup, validate_mood, validate_intensity,
    validate_behavior_name, validate_sound_name, validate_volume,
    validate_sequence_data, sanitize_markup
)
import json
import uuid
import logging
import csv
import io
from django.utils import timezone
from .automarkup import process as automarkup_process
from .automarkup import initialize_rules as automarkup_initialize_rules

logger = logging.getLogger(__name__)

# Maximum JSON size to prevent DoS
MAX_JSON_SIZE = 1024 * 1024  # 1MB


def validate_json_size(request):
    """Validate JSON request body size"""
    if request.body and len(request.body) > MAX_JSON_SIZE:
        raise ValueError(f"Request body too large (max {MAX_JSON_SIZE} bytes)")


# PUPPET-POST - Handle user input during puppet mode with improved validation
@require_http_methods(["POST"])
def puppet_command_improved(request, pk):
    """Improved puppet command with proper validation and error handling"""
    try:
        device = get_object_or_404(MoxieDevice, pk=pk)
        command = request.POST.get('command')

        if not command:
            return JsonResponse({'result': 'error', 'message': 'No command specified'}, status=400)

        if command == 'speak':
            speech = sanitize_input(request.POST.get('speech', ''), max_length=1000)
            markup = request.POST.get('markup', '')

            if markup:
                # Validate markup
                is_valid, error_msg = validate_markup(markup)
                if not is_valid:
                    return JsonResponse({
                        'result': 'error',
                        'message': f'Invalid markup: {error_msg}'
                    }, status=400)

                get_instance().send_telehealth_markup(device.device_id, markup, speech)
            else:
                # Validate mood and intensity
                mood = request.POST.get('mood', 'neutral')
                if not validate_mood(mood):
                    return JsonResponse({
                        'result': 'error',
                        'message': f'Invalid mood: {mood}'
                    }, status=400)

                intensity_str = request.POST.get('intensity', '0.5')
                is_valid, intensity = validate_intensity(intensity_str)
                if not is_valid:
                    return JsonResponse({
                        'result': 'error',
                        'message': 'Invalid intensity value (must be 0.0-1.0)'
                    }, status=400)

                get_instance().send_telehealth_speech(device.device_id, speech, mood, intensity)

            return JsonResponse({
                'result': 'success',
                'message': f'Sent speech command',
                'device': device.device_id
            })

        elif command == 'interrupt':
            get_instance().send_telehealth_interrupt(device.device_id)
            return JsonResponse({'result': 'success', 'message': 'Sent interrupt command'})

        else:
            return JsonResponse({'result': 'error', 'message': f'Unknown command: {command}'}, status=400)

    except MoxieDevice.DoesNotExist:
        logger.warning(f"Puppet command for non-existent device pk={pk}")
        return JsonResponse({'result': 'error', 'message': 'Device not found'}, status=404)
    except Exception as e:
        logger.error(f"Error in puppet command for pk={pk}: {str(e)}", exc_info=True)
        return JsonResponse({'result': 'error', 'message': 'Internal server error'}, status=500)


# DJ-POST - Handle DJ commands with improved validation
@require_http_methods(["POST"])
@csrf_exempt  # If using AJAX with custom headers
def dj_command_improved(request, pk):
    """Improved DJ command endpoint with proper validation"""
    try:
        # Validate request size
        validate_json_size(request)

        device = get_object_or_404(MoxieDevice, pk=pk)

        # Handle both form data and JSON data
        content_type = request.content_type or ''
        if content_type.startswith('application/json'):
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in DJ command: {e}")
                return JsonResponse({'result': 'error', 'message': 'Invalid JSON format'}, status=400)
        else:
            data = request.POST

        cmd = data.get('command')
        if not cmd:
            return JsonResponse({'result': 'error', 'message': 'No command specified'}, status=400)

        # Initialize device config if needed
        if not device.robot_config:
            device.robot_config = {}

        # Process commands with validation
        if cmd == "enable":
            with transaction.atomic():
                device.robot_config["moxie_mode"] = "TELEHEALTH"
                device.save()
            get_instance().handle_config_updated(device)

        elif cmd == "disable":
            with transaction.atomic():
                device.robot_config.pop("moxie_mode", None)
                device.save()
            get_instance().handle_config_updated(device)

        elif cmd == "interrupt":
            get_instance().send_telehealth_interrupt(device.device_id)

        elif cmd == "speak":
            text = sanitize_input(data.get('text', ''), max_length=1000)
            markup = data.get('markup', '')

            if markup:
                is_valid, error_msg = validate_markup(markup)
                if not is_valid:
                    return JsonResponse({
                        'result': 'error',
                        'message': f'Invalid markup: {error_msg}'
                    }, status=400)
                get_instance().send_telehealth_markup(device.device_id, markup, text)
            else:
                mood = data.get('mood', 'neutral')
                if not validate_mood(mood):
                    return JsonResponse({
                        'result': 'error',
                        'message': f'Invalid mood: {mood}'
                    }, status=400)

                is_valid, intensity = validate_intensity(data.get('intensity', 0.5))
                if not is_valid:
                    return JsonResponse({
                        'result': 'error',
                        'message': 'Invalid intensity value'
                    }, status=400)

                get_instance().send_telehealth_speech(device.device_id, text, mood, intensity)

        elif cmd == "behavior":
            behavior_name = data.get('behavior_name')
            if not validate_behavior_name(behavior_name):
                return JsonResponse({
                    'result': 'error',
                    'message': 'Invalid behavior name'
                }, status=400)
            dj_handle_behavior(device.device_id, behavior_name)

        elif cmd == "sound_effect":
            sound_name = data.get('sound_name')
            if not validate_sound_name(sound_name):
                return JsonResponse({
                    'result': 'error',
                    'message': 'Invalid sound name'
                }, status=400)

            is_valid, volume = validate_volume(data.get('volume', 0.75))
            if not is_valid:
                return JsonResponse({
                    'result': 'error',
                    'message': 'Invalid volume value'
                }, status=400)

            dj_handle_sound_effect(device.device_id, sound_name, volume)

        elif cmd == "custom_markup":
            markup = data.get('markup')
            if not markup:
                return JsonResponse({
                    'result': 'error',
                    'message': 'No markup provided'
                }, status=400)

            is_valid, error_msg = validate_markup(markup)
            if not is_valid:
                return JsonResponse({
                    'result': 'error',
                    'message': f'Invalid markup: {error_msg}'
                }, status=400)

            get_instance().send_telehealth_markup(device.device_id, markup)

        elif cmd == "play_custom_sequence":
            sequence_data_raw = data.get('sequence_data')
            if isinstance(sequence_data_raw, str):
                try:
                    sequence_data = json.loads(sequence_data_raw)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'result': 'error',
                        'message': 'Invalid sequence data format'
                    }, status=400)
            else:
                sequence_data = sequence_data_raw or []

            is_valid, error_msg = validate_sequence_data(sequence_data)
            if not is_valid:
                return JsonResponse({
                    'result': 'error',
                    'message': f'Invalid sequence: {error_msg}'
                }, status=400)

            dj_handle_custom_sequence(device.device_id, sequence_data)

        else:
            return JsonResponse({
                'result': 'error',
                'message': f'Unknown command: {cmd}'
            }, status=400)

        return JsonResponse({'result': 'success', 'message': f'Executed command: {cmd}'})

    except MoxieDevice.DoesNotExist:
        logger.warning(f"DJ command for non-existent device pk={pk}")
        return JsonResponse({'result': 'error', 'message': 'Device not found'}, status=404)
    except ValueError as e:
        logger.warning(f"Validation error in DJ command: {e}")
        return JsonResponse({'result': 'error', 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in DJ command for pk={pk}: {str(e)}", exc_info=True)
        return JsonResponse({'result': 'error', 'message': 'Internal server error'}, status=500)


# Import data with proper transaction management
@require_http_methods(['POST'])
def import_data_improved(request):
    """Improved import with transaction management"""
    try:
        # Get import lists
        g_list = request.POST.getlist("globals")
        s_list = request.POST.getlist("schedules")
        c_list = request.POST.getlist("conversations")

        # Get and validate JSON data
        jstring = request.POST.get("json_data")
        if not jstring:
            return redirect('hive:dashboard_alert', alert_message='No import data provided')

        try:
            json_data = json.loads(jstring)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in import: {e}")
            return redirect('hive:dashboard_alert', alert_message='Invalid import data format')

        # Import with transaction
        with transaction.atomic():
            message = import_content(json_data, g_list, s_list, c_list)

        # Refresh cached data
        get_instance().update_from_database()

        return redirect('hive:dashboard_alert', alert_message=message)

    except Exception as e:
        logger.error(f"Error during import: {str(e)}", exc_info=True)
        return redirect('hive:dashboard_alert', alert_message='Import failed: An error occurred')


# Mission edit with proper error handling
@require_http_methods(["POST"])
def mission_edit_improved(request, pk):
    """Improved mission edit with transaction and error handling"""
    try:
        device = get_object_or_404(MoxieDevice, pk=pk)
        mission_action = request.POST.get("mission_action")

        if not mission_action:
            return redirect('hive:dashboard_alert', alert_message='No action specified')

        with transaction.atomic():
            if mission_action == "reset":
                # Delete all MBH to start fresh
                deleted_count = MentorBehavior.objects.filter(device=device).delete()[0]
                msg = f'Reset ALL progress for {device} ({deleted_count} records deleted)'

            elif mission_action in ["forget", "complete"]:
                # Handle mission set actions
                mission_sets = request.POST.getlist("mission_sets")
                if not mission_sets:
                    return redirect('hive:dashboard_alert', alert_message='No mission sets selected')

                dm_cid_list = []
                for ms in mission_sets:
                    cids = DM_MISSION_CONTENT_IDS.get(ms, [])
                    dm_cid_list.extend(cids)

                if mission_action == "forget":
                    deleted_count = MentorBehavior.objects.filter(
                        device=device,
                        module_id='DM',
                        content_id__in=dm_cid_list
                    ).delete()[0]
                    msg = f'Forgot {len(mission_sets)} Daily Mission Sets ({deleted_count} missions) for {device}'
                else:  # complete
                    get_instance().robot_data().add_mbh_completion_bulk(
                        device.device_id,
                        module_id="DM",
                        content_id_list=dm_cid_list
                    )
                    msg = f'Completed {len(mission_sets)} Daily Mission Sets ({len(dm_cid_list)} missions) for {device}'
            else:
                return redirect('hive:dashboard_alert', alert_message=f'Unknown action: {mission_action}')

        return redirect('hive:dashboard_alert', alert_message=msg)

    except MoxieDevice.DoesNotExist:
        logger.warning(f"Mission edit for non-existent device pk={pk}")
        return redirect('hive:dashboard_alert', alert_message='Device not found')
    except Exception as e:
        logger.error(f"Error in mission edit for pk={pk}: {str(e)}", exc_info=True)
        return redirect('hive:dashboard_alert', alert_message='An error occurred while updating missions')


# Helper functions referenced in the views
def dj_handle_behavior(device_id, behavior_name):
    """Handle direct behavior tree execution with detailed markup"""
    markup = get_behavior_markup(behavior_name)
    get_instance().send_telehealth_markup(device_id, markup)


def dj_handle_sound_effect(device_id, sound_name, volume):
    """Handle sound effect playback"""
    markup = get_sound_effect_markup(sound_name, volume)
    get_instance().send_telehealth_markup(device_id, markup)


def dj_handle_custom_sequence(device_id, sequence_data):
    """Handle custom sequence execution"""
    for item in sequence_data:
        item_type = item.get('type')
        if item_type == 'behavior':
            dj_handle_behavior(device_id, item['value'])
        elif item_type == 'sound':
            volume = item.get('volume', 0.75)
            dj_handle_sound_effect(device_id, item['value'], volume)
        elif item_type == 'pause':
            # Pauses are handled in markup
            pass
