from django.db import models
from django.forms import JSONField
from django.contrib.auth import get_user_model
from django.utils import timezone
from enum import Enum
import os
import uuid

User = get_user_model()


class MoxieDevice(models.Model):
    device_id = models.CharField(max_length=200, unique=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    schedule = models.ForeignKey("MoxieSchedule", on_delete=models.SET_NULL, blank=True, null=True)
    robot_settings = models.JSONField(blank=True, null=True)
    robot_config = models.JSONField(blank=True, null=True)
    first_connect = models.DateTimeField(auto_now_add=True, editable=False)
    last_connect = models.DateTimeField(blank=True, null=True)
    last_disconnect = models.DateTimeField(blank=True, null=True)

    @property
    def is_paired(self):
        """Check if the device is paired based on robot_settings or robot_config"""
        # Check robot_settings first
        if self.robot_settings and isinstance(self.robot_settings, dict):
            pairing_status = self.robot_settings.get('pairing_status')
            if pairing_status == 'paired':
                return True

        # Check robot_config as fallback
        if self.robot_config and isinstance(self.robot_config, dict):
            pairing_status = self.robot_config.get('pairing_status')
            if pairing_status == 'paired':
                return True

        # Default to unpaired if no clear status found
        return False

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f'{self.device_id}'


class PersistentData(models.Model):
    device = models.OneToOneField(MoxieDevice, on_delete=models.CASCADE)
    data = models.JSONField(blank=True, null=True)
    last_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.device.device_id} persistent data'


class MoxieSchedule(models.Model):
    name = models.CharField(max_length=80, unique=True)
    schedule = models.JSONField()
    source_version = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class GlobalResponse(models.Model):
    name = models.CharField(max_length=80, unique=True)
    module_id = models.CharField(max_length=20, default="CC")
    content_id = models.CharField(max_length=40, default="response")
    triggers = models.JSONField(blank=True, null=True)
    queries = models.CharField(max_length=800, blank=True, null=True)
    responses = models.CharField(max_length=800)
    source_version = models.IntegerField(default=0)
    priority = models.IntegerField(default=100)

    def __str__(self):
        return self.name


class SinglePromptChat(models.Model):
    module_id = models.CharField(max_length=40, unique=False)
    content_id = models.CharField(max_length=40, unique=False)
    name = models.CharField(max_length=80, blank=True, null=True)
    debug_instructions = models.CharField(max_length=800, blank=True, null=True)
    prompt = models.TextField(blank=True, null=True)
    initial_npc = models.TextField(blank=True, null=True)
    source_version = models.IntegerField(default=0)

    class Meta:
        unique_together = ('module_id', 'content_id')

    def __str__(self):
        if self.name:
            return self.name
        else:
            return f'{self.module_id}|{self.content_id}'


class HiveConfiguration(models.Model):
    name = models.CharField(max_length=80, unique=True, default='default')
    openai_api_key = models.CharField(max_length=100, blank=True, null=True)
    google_api_key = models.TextField(blank=True, null=True)
    external_host = models.CharField(max_length=80, blank=True, null=True)
    allow_unverified_bots = models.BooleanField(default=False)
    common_config = models.JSONField(blank=True, null=True)
    common_settings = models.JSONField(blank=True, null=True)

    @classmethod
    def get_current(cls):
        # Support multiple configs by environment variable
        name = os.getenv('HIVE_CONFIG_NAME', 'default')
        config, created = cls.objects.get_or_create(name=name)
        return config

    def __str__(self):
        return self.name


class MentorBehavior(models.Model):
    device = models.ForeignKey(MoxieDevice, on_delete=models.CASCADE)
    # Fields for MBH
    module_id = models.CharField(max_length=80, null=True, blank=True)
    content_id = models.CharField(max_length=80, null=True, blank=True)
    content_day = models.CharField(max_length=80, null=True, blank=True)
    timestamp = models.BigIntegerField()
    action = models.CharField(max_length=80, null=True, blank=True)
    instance_id = models.BigIntegerField()
    ended_reason = models.CharField(max_length=80, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['device', 'timestamp'], name='device_timestamp_idx'),
        ]

    def __str__(self):
        return f'{self.timestamp}-{self.device}-{self.module_id}/{self.content_id}-{self.action}'


class APIKey(models.Model):
    """
    Model for managing API keys separately from other authentication
    """
    key = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.key or self.key == str(uuid.uuid4()):
            # Generate a proper API key
            from .auth_utils import generate_api_key
            self.key = generate_api_key()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"


class GlobalAction(Enum):
    # Global response actions
    RESPONSE = 'response'
    DEBUG_RESPONSE = 'debug-response'
