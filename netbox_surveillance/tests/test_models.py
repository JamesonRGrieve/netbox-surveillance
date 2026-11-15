# SPDX-License-Identifier: AGPL-3.0-or-later
"""Model validation against a real test database (no mocks)."""

from dcim.models import Device, DeviceRole, DeviceType, Manufacturer, Site
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from netbox_surveillance.choices import (
    RecordingModeChoices,
    StreamRoleChoices,
    TriggerActionChoices,
    TriggerInputChoices,
)
from netbox_surveillance.models import (
    Camera,
    DoorRelay,
    DoorTrigger,
    DoorTriggerWindow,
    Notification,
    RecordingSchedule,
    SipEndpoint,
    Stream,
    validate_openbao_ref,
    validate_week_table,
)


def make_device(name):
    site = Site.objects.get_or_create(name="Shop", slug="shop")[0]
    mfr = Manufacturer.objects.get_or_create(name="Generic", slug="generic")[0]
    dt = DeviceType.objects.get_or_create(manufacturer=mfr, model="Cam", slug="cam")[0]
    role = DeviceRole.objects.get_or_create(name="IP Camera", slug="ip-camera")[0]
    return Device.objects.create(name=name, site=site, device_type=dt, role=role)


class ValidatorTest(TestCase):
    def test_openbao_ref(self):
        validate_openbao_ref("")
        validate_openbao_ref("prod/zephyrex/infra/shop/shop-doorbird/keypad")
        for bad in ("hunter2", "https://bao/x", "user@host/x"):
            with self.assertRaises(ValidationError):
                validate_openbao_ref(bad)

    def test_week_table(self):
        validate_week_table("")
        validate_week_table("1" * 168)
        for bad in ("1" * 167, "2" * 168, "1" * 169):
            with self.assertRaises(ValidationError):
                validate_week_table(bad)


class CameraTest(TestCase):
    def setUp(self):
        self.nvr = make_device("nvr")

    def test_channel_needs_recorder(self):
        cam = Camera(name="garage", device=self.nvr, channel=3)
        with self.assertRaises(ValidationError):
            cam.full_clean()
        cam.recorder = self.nvr
        cam.full_clean()

    def test_one_camera_per_recorder_channel(self):
        Camera.objects.create(name="a", device=self.nvr, recorder=self.nvr, channel=0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Camera.objects.create(name="b", device=self.nvr, recorder=self.nvr, channel=0)

    def test_stream_role_unique_and_cascade(self):
        cam = Camera.objects.create(name="a", device=self.nvr)
        Stream.objects.create(camera=cam, role=StreamRoleChoices.MAIN, frigate_record=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Stream.objects.create(camera=cam, role=StreamRoleChoices.MAIN)
        RecordingSchedule.objects.create(camera=cam, mode=RecordingModeChoices.MOTION, week_table="1" * 168)
        cam.delete()
        self.assertFalse(Stream.objects.exists())
        self.assertFalse(RecordingSchedule.objects.exists())


class NotificationTest(TestCase):
    def test_no_credentials_in_target_and_camera_on_device(self):
        dev, other = make_device("nvr"), make_device("other")
        n = Notification(device=dev, name="ha", kind="http", target="https://user:pw@ha.local/hook")
        with self.assertRaises(ValidationError):
            n.full_clean()
        n.target = "https://ha.local/hook"
        n.full_clean()
        n.camera = Camera.objects.create(name="elsewhere", device=other)
        with self.assertRaises(ValidationError):
            n.full_clean()


class DoorStationTest(TestCase):
    def setUp(self):
        self.door = make_device("shop-doorbird")
        self.relay = DoorRelay.objects.create(device=self.door, number=1, name="shop door")

    def test_keypad_needs_ref_and_doorbell_has_none(self):
        t = DoorTrigger(
            device=self.door,
            input=TriggerInputChoices.KEYPAD,
            input_label="family",
            action=TriggerActionChoices.RELAY,
            relay=self.relay,
        )
        with self.assertRaises(ValidationError):
            t.full_clean()
        t.input_ref = "prod/zephyrex/infra/shop/shop-doorbird/keypad"
        t.full_clean()
        bell = DoorTrigger(
            device=self.door,
            input=TriggerInputChoices.DOORBELL,
            input_label="1",
            input_ref="prod/x/y",
            action=TriggerActionChoices.NOTIFY,
        )
        with self.assertRaises(ValidationError):
            bell.full_clean()

    def test_action_target_matches(self):
        t = DoorTrigger(
            device=self.door, input=TriggerInputChoices.DOORBELL, input_label="1", action=TriggerActionChoices.RELAY
        )
        with self.assertRaises(ValidationError):
            t.full_clean()
        other_relay = DoorRelay.objects.create(device=make_device("other"), number=1)
        t.relay = other_relay
        with self.assertRaises(ValidationError):
            t.full_clean()
        t.relay = self.relay
        t.full_clean()
        http = DoorTrigger(
            device=self.door, input=TriggerInputChoices.MOTION, input_label="", action=TriggerActionChoices.HTTP
        )
        with self.assertRaises(ValidationError):
            http.full_clean()

    def test_window_half_hour_and_order(self):
        t = DoorTrigger.objects.create(
            device=self.door,
            input=TriggerInputChoices.DOORBELL,
            input_label="1",
            action=TriggerActionChoices.RELAY,
            relay=self.relay,
        )
        DoorTriggerWindow(trigger=t, start_second=0, end_second=604799).full_clean()
        for start, end in ((900, 2000), (3600, 1800), (0, 604800)):
            with self.assertRaises(ValidationError):
                DoorTriggerWindow(trigger=t, start_second=start, end_second=end).full_clean()

    def test_sip_registration_needs_user_and_ref(self):
        s = SipEndpoint(device=self.door, register_url="pbx.local")
        with self.assertRaises(ValidationError):
            s.full_clean()
        s.register_user, s.password_ref = "101", "prod/zephyrex/infra/shop/shop-doorbird/sip"
        s.full_clean()
        s.mic_volume = 0
        with self.assertRaises(ValidationError):
            s.full_clean()
