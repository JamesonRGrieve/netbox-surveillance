# SPDX-License-Identifier: AGPL-3.0-or-later
from dcim.models import Device
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField, TagFilterField

from .models import (
    Camera,
    DoorRelay,
    DoorTrigger,
    DoorTriggerWindow,
    MotionDetection,
    Notification,
    RecordingSchedule,
    SipEndpoint,
    Stream,
)

# Edit-form fields per model, and the FK fields that get a dynamic (API-backed) chooser.
FORM_FIELDS = {
    Camera: ["name", "device", "recorder", "channel", "description", "tags"],
    Stream: [
        "camera",
        "role",
        "codec",
        "width",
        "height",
        "fps",
        "bitrate_kbps",
        "gop",
        "rtsp_path",
        "frigate_record",
        "frigate_detect",
        "tags",
    ],
    RecordingSchedule: ["camera", "mode", "week_table", "tags"],
    MotionDetection: ["camera", "enabled", "sensitivity", "week_table", "tags"],
    Notification: ["device", "camera", "name", "kind", "target", "enabled", "week_table", "secret_ref", "tags"],
    DoorRelay: ["device", "number", "name", "passcode_ref", "tags"],
    DoorTrigger: ["device", "input", "input_label", "input_ref", "action", "relay", "notification", "enabled", "tags"],
    DoorTriggerWindow: ["trigger", "start_second", "end_second", "tags"],
    SipEndpoint: [
        "device",
        "enabled",
        "register_url",
        "register_user",
        "password_ref",
        "incoming_call_enable",
        "incoming_call_user",
        "dtmf",
        "anc",
        "mic_volume",
        "spk_volume",
        "ring_time_limit",
        "call_time_limit",
        "tags",
    ],
}
_FK_QUERYSETS = {
    "device": Device.objects.all,
    "recorder": Device.objects.all,
    "camera": Camera.objects.all,
    "relay": DoorRelay.objects.all,
    "notification": Notification.objects.all,
    "trigger": DoorTrigger.objects.all,
}
_OPTIONAL_FKS = {"recorder", "relay", "notification"}


def _model_form(model):
    attrs = {
        fk: DynamicModelChoiceField(
            queryset=_FK_QUERYSETS[fk](), required=fk in _OPTIONAL_FKS or (model is Notification and fk == "camera")
        )
        for fk in FORM_FIELDS[model]
        if fk in _FK_QUERYSETS
    }
    attrs["Meta"] = type("Meta", (), {"model": model, "fields": FORM_FIELDS[model]})
    return type(f"{model.__name__}Form", (NetBoxModelForm,), attrs)


def _filter_form(model):
    return type(
        f"{model.__name__}FilterForm", (NetBoxModelFilterSetForm,), {"model": model, "tag": TagFilterField(model)}
    )


MODEL_FORMS = {m: _model_form(m) for m in FORM_FIELDS}
FILTER_FORMS = {m: _filter_form(m) for m in FORM_FIELDS}
