# SPDX-License-Identifier: AGPL-3.0-or-later
"""Vendor-neutral surveillance and door-station models.

Every model hangs off ``dcim.Device`` (FK by string label; core apps are never imported here).

- :class:`Camera` is one camera: its own device, or (behind an NVR's PoE ports) the NVR channel it
  sits on. :class:`Stream` is one of its encoded streams; Frigate takes ``frigate_record`` and
  ``frigate_detect`` inputs from these.
- :class:`RecordingSchedule` and :class:`MotionDetection` are a camera's recording and motion
  settings, each with a ``week_table``: 168 characters of ``0``/``1``, one per hour from Sunday
  00:00 (Reolink's own table shape).
- :class:`Notification` is an alert a device sends (push / email / FTP / HTTP / SIP).
- :class:`DoorRelay`, :class:`DoorTrigger` (+ :class:`DoorTriggerWindow`) and
  :class:`SipEndpoint` are a door station's relays, its input → action rules and its SIP client.

SECRET POLICY: no password, passcode or keypad code is ever a field. ``*_ref`` fields hold OpenBao
KV paths and are validated by :func:`validate_openbao_ref`.
"""

import re

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from netbox.models import NetBoxModel

from .choices import (
    CodecChoices,
    NotificationKindChoices,
    RecordingModeChoices,
    StreamRoleChoices,
    TriggerActionChoices,
    TriggerInputChoices,
)

WEEK_HOURS = 168
WEEK_SECONDS = 7 * 24 * 3600
HALF_HOUR = 1800
_WEEK_TABLE = re.compile(r"[01]{%d}" % WEEK_HOURS)


def validate_openbao_ref(value):
    """An OpenBao KV path: contains ``/``, never ``://`` or ``@``. Blank is unset."""
    if not value:
        return
    if "://" in value or "@" in value:
        raise ValidationError("Must be an OpenBao KV path, not a URL or literal value.")
    if "/" not in value:
        raise ValidationError("Must be an OpenBao KV path; it has to contain '/'.")


def validate_week_table(value):
    """168 characters of 0/1, one per hour from Sunday 00:00. Blank is unset."""
    if value and not _WEEK_TABLE.fullmatch(value):
        raise ValidationError(f"Must be exactly {WEEK_HOURS} characters of 0 or 1 (one per hour).")


class _Base(NetBoxModel):
    class Meta:
        abstract = True

    def get_absolute_url(self):
        return reverse(f"plugins:netbox_surveillance:{self._meta.model_name}", args=[self.pk])


class Camera(_Base):
    name = models.CharField(max_length=100, unique=True)
    device = models.ForeignKey(
        "dcim.Device",
        on_delete=models.CASCADE,
        related_name="surveillance_cameras",
        help_text="The camera itself, or the NVR when the camera has no address of its own.",
    )
    recorder = models.ForeignKey(
        "dcim.Device",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_cameras",
        help_text="The NVR that records this camera.",
    )
    channel = models.PositiveSmallIntegerField(null=True, blank=True, help_text="The recorder channel (0-based).")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["recorder", "channel"], name="surveillance_camera_unique_channel")
        ]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if self.channel is not None and self.recorder_id is None:
            raise ValidationError({"channel": "A channel needs a recorder."})


class Stream(_Base):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="streams")
    role = models.CharField(max_length=8, choices=StreamRoleChoices)
    codec = models.CharField(max_length=8, choices=CodecChoices, blank=True)
    width = models.PositiveSmallIntegerField(null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    fps = models.PositiveSmallIntegerField(null=True, blank=True)
    bitrate_kbps = models.PositiveIntegerField(null=True, blank=True)
    gop = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Key-frame interval (frames).")
    rtsp_path = models.CharField(max_length=200, blank=True, help_text="Path part of the RTSP URL.")
    frigate_record = models.BooleanField(default=False)
    frigate_detect = models.BooleanField(default=False)

    class Meta:
        ordering = ["camera", "role"]
        constraints = [models.UniqueConstraint(fields=["camera", "role"], name="surveillance_stream_unique_role")]

    def __str__(self):
        return f"{self.camera} {self.role}"

    def get_role_color(self):
        return StreamRoleChoices.colors.get(self.role)


class RecordingSchedule(_Base):
    camera = models.OneToOneField(Camera, on_delete=models.CASCADE, related_name="recording_schedule")
    mode = models.CharField(max_length=12, choices=RecordingModeChoices)
    week_table = models.CharField(max_length=WEEK_HOURS, blank=True, validators=[validate_week_table])

    class Meta:
        ordering = ["camera"]

    def __str__(self):
        return f"{self.camera} recording"

    def get_mode_color(self):
        return RecordingModeChoices.colors.get(self.mode)


class MotionDetection(_Base):
    camera = models.OneToOneField(Camera, on_delete=models.CASCADE, related_name="motion_detection")
    enabled = models.BooleanField(default=True)
    sensitivity = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(100)], help_text="0-100; unset = device default."
    )
    week_table = models.CharField(max_length=WEEK_HOURS, blank=True, validators=[validate_week_table])

    class Meta:
        ordering = ["camera"]
        verbose_name = "Motion detection"
        verbose_name_plural = "Motion detection"

    def __str__(self):
        return f"{self.camera} motion"


class Notification(_Base):
    device = models.ForeignKey("dcim.Device", on_delete=models.CASCADE, related_name="surveillance_notifications")
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    name = models.CharField(max_length=100)
    kind = models.CharField(max_length=8, choices=NotificationKindChoices)
    target = models.CharField(
        max_length=255,
        blank=True,
        help_text="Address, URL or SIP target, with no credentials in it (those go in secret_ref).",
    )
    enabled = models.BooleanField(default=True)
    week_table = models.CharField(max_length=WEEK_HOURS, blank=True, validators=[validate_week_table])
    secret_ref = models.CharField(max_length=255, blank=True, validators=[validate_openbao_ref])

    class Meta:
        ordering = ["device", "name"]
        constraints = [
            models.UniqueConstraint(fields=["device", "kind", "name"], name="surveillance_notification_unique")
        ]

    def __str__(self):
        return f"{self.device} {self.kind} {self.name}"

    def clean(self):
        super().clean()
        if "@" in self.target and "://" in self.target and self.target.split("://", 1)[1].split("/")[0].count("@"):
            raise ValidationError({"target": "Credentials belong in secret_ref, not in the target URL."})
        if self.camera_id and self.camera.device_id != self.device_id and self.camera.recorder_id != self.device_id:
            raise ValidationError({"camera": "The camera must be on this device or recorded by it."})


class DoorRelay(_Base):
    device = models.ForeignKey("dcim.Device", on_delete=models.CASCADE, related_name="door_relays")
    number = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    name = models.CharField(max_length=100, blank=True)
    passcode_ref = models.CharField(max_length=255, blank=True, validators=[validate_openbao_ref])

    class Meta:
        ordering = ["device", "number"]
        constraints = [models.UniqueConstraint(fields=["device", "number"], name="surveillance_relay_unique")]

    def __str__(self):
        return f"{self.device} relay {self.number}"


class DoorTrigger(_Base):
    device = models.ForeignKey("dcim.Device", on_delete=models.CASCADE, related_name="door_triggers")
    input = models.CharField(max_length=12, choices=TriggerInputChoices)
    input_label = models.CharField(
        max_length=100, help_text="Names the input: a doorbell number, or a label for a code / transponder."
    )
    input_ref = models.CharField(
        max_length=255,
        blank=True,
        validators=[validate_openbao_ref],
        help_text="OpenBao path of the code, transponder or fingerprint id (secret inputs only).",
    )
    action = models.CharField(max_length=8, choices=TriggerActionChoices)
    relay = models.ForeignKey(DoorRelay, on_delete=models.CASCADE, null=True, blank=True, related_name="triggers")
    notification = models.ForeignKey(
        Notification, on_delete=models.CASCADE, null=True, blank=True, related_name="door_triggers"
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["device", "input", "input_label", "action"]
        constraints = [
            models.UniqueConstraint(
                fields=["device", "input", "input_label", "action", "relay", "notification"],
                name="surveillance_trigger_unique",
            )
        ]

    def __str__(self):
        return f"{self.device} {self.input}:{self.input_label} → {self.action}"

    def clean(self):
        super().clean()
        if self.input in TriggerInputChoices.SECRET and not self.input_ref:
            raise ValidationError({"input_ref": "A code, transponder or fingerprint input needs its OpenBao ref."})
        if self.input not in TriggerInputChoices.SECRET and self.input_ref:
            raise ValidationError({"input_ref": "Only a code, transponder or fingerprint input has a ref."})
        if (self.action == TriggerActionChoices.RELAY) != (self.relay_id is not None):
            raise ValidationError({"relay": "A relay action names exactly one relay; other actions name none."})
        if (self.action in (TriggerActionChoices.HTTP, TriggerActionChoices.SIP)) != (self.notification_id is not None):
            raise ValidationError({"notification": "An HTTP or SIP action names its target notification; others none."})
        if self.relay_id and self.relay.device_id != self.device_id:
            raise ValidationError({"relay": "The relay must be on the same device."})


class DoorTriggerWindow(_Base):
    trigger = models.ForeignKey(DoorTrigger, on_delete=models.CASCADE, related_name="windows")
    start_second = models.PositiveIntegerField(
        validators=[MaxValueValidator(WEEK_SECONDS - 1)], help_text="Seconds from Sunday 00:00 UTC."
    )
    end_second = models.PositiveIntegerField(
        validators=[MaxValueValidator(WEEK_SECONDS - 1)], help_text="Inclusive end, seconds from Sunday 00:00 UTC."
    )

    class Meta:
        ordering = ["trigger", "start_second"]
        constraints = [models.UniqueConstraint(fields=["trigger", "start_second"], name="surveillance_window_unique")]

    def __str__(self):
        return f"{self.trigger} {self.start_second}-{self.end_second}"

    def clean(self):
        super().clean()
        if self.start_second is not None and self.start_second % HALF_HOUR:
            raise ValidationError({"start_second": "Must start on a half-hour (a multiple of 1800)."})
        if self.start_second is not None and self.end_second is not None and self.end_second < self.start_second:
            raise ValidationError({"end_second": "Must not be before the start."})


class SipEndpoint(_Base):
    device = models.OneToOneField("dcim.Device", on_delete=models.CASCADE, related_name="sip_endpoint")
    enabled = models.BooleanField(default=False)
    register_url = models.CharField(max_length=255, blank=True, help_text="SIP proxy host; blank for peer-to-peer.")
    register_user = models.CharField(max_length=100, blank=True)
    password_ref = models.CharField(max_length=255, blank=True, validators=[validate_openbao_ref])
    incoming_call_enable = models.BooleanField(default=False)
    incoming_call_user = models.CharField(max_length=255, blank=True)
    dtmf = models.BooleanField(default=False)
    anc = models.BooleanField(default=True, help_text="Acoustic noise cancellation.")
    mic_volume = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    spk_volume = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    ring_time_limit = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(10), MaxValueValidator(300)]
    )
    call_time_limit = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(300)]
    )

    class Meta:
        ordering = ["device"]
        verbose_name = "SIP endpoint"

    def __str__(self):
        return f"{self.device} SIP"

    def clean(self):
        super().clean()
        if self.register_url and not (self.register_user and self.password_ref):
            raise ValidationError({"register_url": "Registration needs register_user and password_ref."})


MODELS = (
    Camera,
    Stream,
    RecordingSchedule,
    MotionDetection,
    Notification,
    DoorRelay,
    DoorTrigger,
    DoorTriggerWindow,
    SipEndpoint,
)
