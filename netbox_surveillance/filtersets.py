# SPDX-License-Identifier: AGPL-3.0-or-later
import django_filters
from dcim.models import Device
from django.db.models import Q
from netbox.filtersets import NetBoxModelFilterSet

from . import choices
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

# django-filter does not derive `<fk>_id` from a bare FK in Meta.fields; NetBox convention is an
# explicit `<fk>_id` filter by PK.


def _fk(field, queryset, label):
    return django_filters.ModelMultipleChoiceFilter(field_name=field, queryset=queryset, label=label)


def _device(field="device"):
    return _fk(field, Device.objects.all(), f"{field} (ID)")


class CameraFilterSet(NetBoxModelFilterSet):
    device_id = _device()
    recorder_id = _device("recorder")

    class Meta:
        model = Camera
        fields = ["id", "name", "channel"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))


class StreamFilterSet(NetBoxModelFilterSet):
    camera_id = _fk("camera", Camera.objects.all(), "Camera (ID)")
    role = django_filters.MultipleChoiceFilter(choices=choices.StreamRoleChoices)
    codec = django_filters.MultipleChoiceFilter(choices=choices.CodecChoices)

    class Meta:
        model = Stream
        fields = ["id", "frigate_record", "frigate_detect"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(camera__name__icontains=value) | Q(rtsp_path__icontains=value))


class RecordingScheduleFilterSet(NetBoxModelFilterSet):
    camera_id = _fk("camera", Camera.objects.all(), "Camera (ID)")
    mode = django_filters.MultipleChoiceFilter(choices=choices.RecordingModeChoices)

    class Meta:
        model = RecordingSchedule
        fields = ["id"]

    def search(self, queryset, name, value):
        return queryset.filter(camera__name__icontains=value)


class MotionDetectionFilterSet(NetBoxModelFilterSet):
    camera_id = _fk("camera", Camera.objects.all(), "Camera (ID)")

    class Meta:
        model = MotionDetection
        fields = ["id", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(camera__name__icontains=value)


class NotificationFilterSet(NetBoxModelFilterSet):
    device_id = _device()
    camera_id = _fk("camera", Camera.objects.all(), "Camera (ID)")
    kind = django_filters.MultipleChoiceFilter(choices=choices.NotificationKindChoices)

    class Meta:
        model = Notification
        fields = ["id", "name", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(target__icontains=value))


class DoorRelayFilterSet(NetBoxModelFilterSet):
    device_id = _device()

    class Meta:
        model = DoorRelay
        fields = ["id", "number", "name"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(name__icontains=value) | Q(device__name__icontains=value))


class DoorTriggerFilterSet(NetBoxModelFilterSet):
    device_id = _device()
    relay_id = _fk("relay", DoorRelay.objects.all(), "Relay (ID)")
    notification_id = _fk("notification", Notification.objects.all(), "Notification (ID)")
    input = django_filters.MultipleChoiceFilter(choices=choices.TriggerInputChoices)
    action = django_filters.MultipleChoiceFilter(choices=choices.TriggerActionChoices)

    class Meta:
        model = DoorTrigger
        fields = ["id", "input_label", "enabled"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(input_label__icontains=value) | Q(device__name__icontains=value))


class DoorTriggerWindowFilterSet(NetBoxModelFilterSet):
    trigger_id = _fk("trigger", DoorTrigger.objects.all(), "Trigger (ID)")

    class Meta:
        model = DoorTriggerWindow
        fields = ["id", "start_second", "end_second"]

    def search(self, queryset, name, value):
        return queryset.filter(trigger__input_label__icontains=value)


class SipEndpointFilterSet(NetBoxModelFilterSet):
    device_id = _device()

    class Meta:
        model = SipEndpoint
        fields = ["id", "enabled", "register_user"]

    def search(self, queryset, name, value):
        return queryset.filter(Q(device__name__icontains=value) | Q(register_url__icontains=value))
