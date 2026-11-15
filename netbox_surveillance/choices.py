# SPDX-License-Identifier: AGPL-3.0-or-later
from utilities.choices import ChoiceSet


class StreamRoleChoices(ChoiceSet):
    MAIN = "main"
    SUB = "sub"
    EXT = "ext"
    CHOICES = [(MAIN, "Main", "blue"), (SUB, "Sub", "cyan"), (EXT, "Extra", "gray")]


class CodecChoices(ChoiceSet):
    H264 = "h264"
    H265 = "h265"
    MJPEG = "mjpeg"
    CHOICES = [(H264, "H.264"), (H265, "H.265"), (MJPEG, "MJPEG")]


class RecordingModeChoices(ChoiceSet):
    CONTINUOUS = "continuous"
    MOTION = "motion"
    OFF = "off"
    CHOICES = [
        (CONTINUOUS, "Continuous", "green"),
        (MOTION, "On motion", "blue"),
        (OFF, "Off", "gray"),
    ]


class NotificationKindChoices(ChoiceSet):
    PUSH = "push"
    EMAIL = "email"
    FTP = "ftp"
    HTTP = "http"
    SIP = "sip"
    CHOICES = [(PUSH, "Push"), (EMAIL, "Email"), (FTP, "FTP"), (HTTP, "HTTP(S)"), (SIP, "SIP call")]


class TriggerInputChoices(ChoiceSet):
    DOORBELL = "doorbell"
    KEYPAD = "keypad"
    MOTION = "motion"
    RFID = "rfid"
    FINGERPRINT = "fingerprint"
    CHOICES = [
        (DOORBELL, "Doorbell button"),
        (KEYPAD, "Keypad code"),
        (MOTION, "Motion"),
        (RFID, "RFID transponder"),
        (FINGERPRINT, "Fingerprint"),
    ]
    # Inputs identified by a secret (a code, a transponder, a finger): the identifier is an
    # OpenBao ref, never a field value.
    SECRET = (KEYPAD, RFID, FINGERPRINT)


class TriggerActionChoices(ChoiceSet):
    RELAY = "relay"
    NOTIFY = "notify"
    HTTP = "http"
    SIP = "sip"
    CHOICES = [(RELAY, "Open relay"), (NOTIFY, "Push / history"), (HTTP, "HTTP call"), (SIP, "SIP call")]
