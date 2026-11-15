# SPDX-License-Identifier: AGPL-3.0-or-later
from dcim.api.serializers import DeviceSerializer
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from ..forms import FORM_FIELDS
from ..models import Camera, DoorRelay, DoorTrigger, Notification

_META = ["id", "url", "display"]
_TAIL = ["tags", "custom_fields", "created", "last_updated"]


def _nested(model):
    """The brief (nested) serializer of a plugin model, used by the models that point at it."""
    name = model._meta.model_name
    return type(
        f"Nested{model.__name__}Serializer",
        (NetBoxModelSerializer,),
        {
            "url": serializers.HyperlinkedIdentityField(view_name=f"plugins-api:netbox_surveillance-api:{name}-detail"),
            "Meta": type("Meta", (), {"model": model, "fields": _META, "brief_fields": _META}),
        },
    )


_NESTED = {m: _nested(m) for m in (Camera, DoorRelay, DoorTrigger, Notification)}
_FK_SERIALIZERS = {
    "device": lambda req: DeviceSerializer(nested=True, required=req),
    "recorder": lambda req: DeviceSerializer(nested=True, required=False, allow_null=True),
    "camera": lambda req: _NESTED[Camera](nested=True, required=req, allow_null=not req),
    "relay": lambda req: _NESTED[DoorRelay](nested=True, required=False, allow_null=True),
    "notification": lambda req: _NESTED[Notification](nested=True, required=False, allow_null=True),
    "trigger": lambda req: _NESTED[DoorTrigger](nested=True, required=req),
}
# A model's optional camera FK (a notification may be for the whole device).
_OPTIONAL_CAMERA = {Notification}


def _serializer(model):
    name = model._meta.model_name
    fields = [f for f in FORM_FIELDS[model] if f != "tags"]
    attrs = {
        "url": serializers.HyperlinkedIdentityField(view_name=f"plugins-api:netbox_surveillance-api:{name}-detail")
    }
    for f in fields:
        if f in _FK_SERIALIZERS:
            attrs[f] = _FK_SERIALIZERS[f](not (f == "camera" and model in _OPTIONAL_CAMERA))
    attrs["Meta"] = type(
        "Meta", (), {"model": model, "fields": _META + fields + _TAIL, "brief_fields": _META + fields[:2]}
    )
    return type(f"{model.__name__}Serializer", (NetBoxModelSerializer,), attrs)


SERIALIZERS = {m: _serializer(m) for m in FORM_FIELDS}

# NetBox resolves a model's serializer by name (utilities.api.get_serializer_for_model), so each
# generated class is also a module-level name.
globals().update({cls.__name__: cls for cls in SERIALIZERS.values()})
