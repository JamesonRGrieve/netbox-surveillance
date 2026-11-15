# SPDX-License-Identifier: AGPL-3.0-or-later
"""REST CRUD against a real DB and the real API client (no mocks)."""

from utilities.testing import APIViewTestCases

from netbox_surveillance.choices import RecordingModeChoices, StreamRoleChoices, TriggerActionChoices
from netbox_surveillance.models import Camera, DoorRelay, DoorTrigger, RecordingSchedule, Stream

from .test_models import make_device


class _CRUD(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    pass


class CameraAPITest(_CRUD):
    model = Camera
    brief_fields = ["device", "display", "id", "name", "url"]
    bulk_update_data = {"description": "updated"}

    @classmethod
    def setUpTestData(cls):
        nvr = make_device("nvr")
        for i in range(3):
            Camera.objects.create(name=f"cam{i}", device=nvr, recorder=nvr, channel=i)
        cls.create_data = [
            {"name": f"new{i}", "device": nvr.pk, "recorder": nvr.pk, "channel": 10 + i} for i in range(3)
        ]


class StreamAPITest(_CRUD):
    model = Stream
    brief_fields = ["camera", "display", "id", "role", "url"]
    bulk_update_data = {"fps": 15}

    @classmethod
    def setUpTestData(cls):
        dev = make_device("cam")
        cams = [Camera.objects.create(name=f"c{i}", device=dev) for i in range(6)]
        for c in cams[:3]:
            Stream.objects.create(camera=c, role=StreamRoleChoices.MAIN)
        cls.create_data = [{"camera": c.pk, "role": StreamRoleChoices.SUB, "frigate_detect": True} for c in cams[3:]]


class RecordingScheduleAPITest(_CRUD):
    model = RecordingSchedule
    brief_fields = ["camera", "display", "id", "mode", "url"]
    bulk_update_data = {"mode": RecordingModeChoices.OFF}

    @classmethod
    def setUpTestData(cls):
        dev = make_device("cam")
        cams = [Camera.objects.create(name=f"c{i}", device=dev) for i in range(6)]
        for c in cams[:3]:
            RecordingSchedule.objects.create(camera=c, mode=RecordingModeChoices.CONTINUOUS)
        cls.create_data = [
            {"camera": c.pk, "mode": RecordingModeChoices.MOTION, "week_table": "1" * 168} for c in cams[3:]
        ]


class DoorRelayAPITest(_CRUD):
    model = DoorRelay
    brief_fields = ["device", "display", "id", "number", "url"]
    bulk_update_data = {"name": "door"}

    @classmethod
    def setUpTestData(cls):
        dev = make_device("door")
        for n in (1, 2, 3):
            DoorRelay.objects.create(device=dev, number=n)
        cls.create_data = [
            {"device": dev.pk, "number": n, "passcode_ref": "prod/zephyrex/infra/shop/door/keypad"} for n in (4, 5, 6)
        ]


class DoorTriggerAPITest(_CRUD):
    model = DoorTrigger
    brief_fields = ["device", "display", "id", "input", "url"]
    bulk_update_data = {"enabled": False}

    @classmethod
    def setUpTestData(cls):
        dev = make_device("door")
        relay = DoorRelay.objects.create(device=dev, number=1)
        for i in range(3):
            DoorTrigger.objects.create(
                device=dev, input="doorbell", input_label=str(i), action=TriggerActionChoices.RELAY, relay=relay
            )
        cls.create_data = [
            {
                "device": dev.pk,
                "input": "keypad",
                "input_label": f"code{i}",
                "input_ref": "prod/zephyrex/infra/shop/door/keypad",
                "action": "relay",
                "relay": relay.pk,
            }
            for i in range(3)
        ]
