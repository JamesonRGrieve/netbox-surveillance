# SPDX-License-Identifier: AGPL-3.0-or-later
# Hand-authored initial migration (NetBox disables makemigrations in production). Verify with:
#   python manage.py makemigrations netbox_surveillance --check --dry-run   (on a dev NetBox)
# ("dcim", "0001_initial") and ("extras", "0001_initial") resolve through each app's squashed
# initial's `replaces`. Standalone: depends on no other plugin's migrations.
import django.core.validators
import django.db.models.deletion
import taggit.managers
import utilities.json
from django.db import migrations, models

import netbox_surveillance.choices
import netbox_surveillance.models

_BASE = [
    ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
    ("created", models.DateTimeField(auto_now_add=True, blank=True, null=True)),
    ("last_updated", models.DateTimeField(auto_now=True, blank=True, null=True)),
    ("custom_field_data", models.JSONField(blank=True, default=dict, encoder=utilities.json.CustomFieldJSONEncoder)),
]


def _tags():
    return ("tags", taggit.managers.TaggableManager(through="extras.TaggedItem", to="extras.Tag"))


def _week():
    return models.CharField(blank=True, max_length=168, validators=[netbox_surveillance.models.validate_week_table])


def _ref():
    return models.CharField(blank=True, max_length=255, validators=[netbox_surveillance.models.validate_openbao_ref])


def _pct(lo, hi):
    return models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[django.core.validators.MinValueValidator(lo), django.core.validators.MaxValueValidator(hi)],
    )


def _device(related):
    return models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name=related, to="dcim.device")


class Migration(migrations.Migration):
    initial = True
    dependencies = [("dcim", "0001_initial"), ("extras", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="Camera",
            fields=[
                *_BASE,
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "device",
                    models.ForeignKey(
                        help_text="The camera itself, or the NVR when the camera has no address of its own.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="surveillance_cameras",
                        to="dcim.device",
                    ),
                ),
                (
                    "recorder",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        help_text="The NVR that records this camera.",
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="recorded_cameras",
                        to="dcim.device",
                    ),
                ),
                (
                    "channel",
                    models.PositiveSmallIntegerField(
                        blank=True, null=True, help_text="The recorder channel (0-based)."
                    ),
                ),
                ("description", models.CharField(blank=True, max_length=200)),
                _tags(),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddConstraint(
            model_name="camera",
            constraint=models.UniqueConstraint(
                fields=("recorder", "channel"), name="surveillance_camera_unique_channel"
            ),
        ),
        migrations.CreateModel(
            name="Stream",
            fields=[
                *_BASE,
                (
                    "camera",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="streams",
                        to="netbox_surveillance.camera",
                    ),
                ),
                ("role", models.CharField(choices=netbox_surveillance.choices.StreamRoleChoices, max_length=8)),
                ("codec", models.CharField(blank=True, choices=netbox_surveillance.choices.CodecChoices, max_length=8)),
                ("width", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("height", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("fps", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("bitrate_kbps", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "gop",
                    models.PositiveSmallIntegerField(blank=True, null=True, help_text="Key-frame interval (frames)."),
                ),
                ("rtsp_path", models.CharField(blank=True, help_text="Path part of the RTSP URL.", max_length=200)),
                ("frigate_record", models.BooleanField(default=False)),
                ("frigate_detect", models.BooleanField(default=False)),
                _tags(),
            ],
            options={"ordering": ["camera", "role"]},
        ),
        migrations.AddConstraint(
            model_name="stream",
            constraint=models.UniqueConstraint(fields=("camera", "role"), name="surveillance_stream_unique_role"),
        ),
        migrations.CreateModel(
            name="RecordingSchedule",
            fields=[
                *_BASE,
                (
                    "camera",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recording_schedule",
                        to="netbox_surveillance.camera",
                    ),
                ),
                ("mode", models.CharField(choices=netbox_surveillance.choices.RecordingModeChoices, max_length=12)),
                ("week_table", _week()),
                _tags(),
            ],
            options={"ordering": ["camera"]},
        ),
        migrations.CreateModel(
            name="MotionDetection",
            fields=[
                *_BASE,
                (
                    "camera",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="motion_detection",
                        to="netbox_surveillance.camera",
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                (
                    "sensitivity",
                    models.PositiveSmallIntegerField(
                        blank=True,
                        null=True,
                        help_text="0-100; unset = device default.",
                        validators=[django.core.validators.MaxValueValidator(100)],
                    ),
                ),
                ("week_table", _week()),
                _tags(),
            ],
            options={
                "ordering": ["camera"],
                "verbose_name": "Motion detection",
                "verbose_name_plural": "Motion detection",
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                *_BASE,
                ("device", _device("surveillance_notifications")),
                (
                    "camera",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="netbox_surveillance.camera",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("kind", models.CharField(choices=netbox_surveillance.choices.NotificationKindChoices, max_length=8)),
                (
                    "target",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        help_text="Address, URL or SIP target, with no credentials in it (those go in secret_ref).",
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                ("week_table", _week()),
                ("secret_ref", _ref()),
                _tags(),
            ],
            options={"ordering": ["device", "name"]},
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                fields=("device", "kind", "name"), name="surveillance_notification_unique"
            ),
        ),
        migrations.CreateModel(
            name="DoorRelay",
            fields=[
                *_BASE,
                ("device", _device("door_relays")),
                ("number", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
                ("name", models.CharField(blank=True, max_length=100)),
                ("passcode_ref", _ref()),
                _tags(),
            ],
            options={"ordering": ["device", "number"]},
        ),
        migrations.AddConstraint(
            model_name="doorrelay",
            constraint=models.UniqueConstraint(fields=("device", "number"), name="surveillance_relay_unique"),
        ),
        migrations.CreateModel(
            name="DoorTrigger",
            fields=[
                *_BASE,
                ("device", _device("door_triggers")),
                ("input", models.CharField(choices=netbox_surveillance.choices.TriggerInputChoices, max_length=12)),
                (
                    "input_label",
                    models.CharField(
                        help_text="Names the input: a doorbell number, or a label for a code / transponder.",
                        max_length=100,
                    ),
                ),
                (
                    "input_ref",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        validators=[netbox_surveillance.models.validate_openbao_ref],
                        help_text="OpenBao path of the code, transponder or fingerprint id (secret inputs only).",
                    ),
                ),
                ("action", models.CharField(choices=netbox_surveillance.choices.TriggerActionChoices, max_length=8)),
                (
                    "relay",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="triggers",
                        to="netbox_surveillance.doorrelay",
                    ),
                ),
                (
                    "notification",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="door_triggers",
                        to="netbox_surveillance.notification",
                    ),
                ),
                ("enabled", models.BooleanField(default=True)),
                _tags(),
            ],
            options={"ordering": ["device", "input", "input_label", "action"]},
        ),
        migrations.AddConstraint(
            model_name="doortrigger",
            constraint=models.UniqueConstraint(
                fields=("device", "input", "input_label", "action", "relay", "notification"),
                name="surveillance_trigger_unique",
            ),
        ),
        migrations.CreateModel(
            name="DoorTriggerWindow",
            fields=[
                *_BASE,
                (
                    "trigger",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="windows",
                        to="netbox_surveillance.doortrigger",
                    ),
                ),
                (
                    "start_second",
                    models.PositiveIntegerField(
                        help_text="Seconds from Sunday 00:00 UTC.",
                        validators=[django.core.validators.MaxValueValidator(604799)],
                    ),
                ),
                (
                    "end_second",
                    models.PositiveIntegerField(
                        help_text="Inclusive end, seconds from Sunday 00:00 UTC.",
                        validators=[django.core.validators.MaxValueValidator(604799)],
                    ),
                ),
                _tags(),
            ],
            options={"ordering": ["trigger", "start_second"]},
        ),
        migrations.AddConstraint(
            model_name="doortriggerwindow",
            constraint=models.UniqueConstraint(fields=("trigger", "start_second"), name="surveillance_window_unique"),
        ),
        migrations.CreateModel(
            name="SipEndpoint",
            fields=[
                *_BASE,
                (
                    "device",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="sip_endpoint", to="dcim.device"
                    ),
                ),
                ("enabled", models.BooleanField(default=False)),
                (
                    "register_url",
                    models.CharField(blank=True, help_text="SIP proxy host; blank for peer-to-peer.", max_length=255),
                ),
                ("register_user", models.CharField(blank=True, max_length=100)),
                ("password_ref", _ref()),
                ("incoming_call_enable", models.BooleanField(default=False)),
                ("incoming_call_user", models.CharField(blank=True, max_length=255)),
                ("dtmf", models.BooleanField(default=False)),
                ("anc", models.BooleanField(default=True, help_text="Acoustic noise cancellation.")),
                ("mic_volume", _pct(1, 100)),
                ("spk_volume", _pct(1, 100)),
                ("ring_time_limit", _pct(10, 300)),
                ("call_time_limit", _pct(30, 300)),
                _tags(),
            ],
            options={"ordering": ["device"], "verbose_name": "SIP endpoint"},
        ),
    ]
