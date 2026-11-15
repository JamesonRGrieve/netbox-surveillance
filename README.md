# netbox-surveillance

A NetBox 4.6 plugin that models IP cameras, NVRs and door stations without tying them to one vendor.

Devices, their interfaces, addresses and WiFi stay in core NetBox (DCIM, IPAM, wireless). This
plugin adds what core NetBox has no place for, hung off `dcim.Device`:

| Model | Holds |
|---|---|
| Camera | A camera: its own device, or the NVR channel it sits on |
| Stream | One encoded stream (codec, resolution, fps, bitrate, RTSP path) and its Frigate roles |
| RecordingSchedule | Recording mode and a 168-hour week table |
| MotionDetection | Motion detection on/off, sensitivity and week table |
| Notification | Push, email, FTP, HTTP or SIP alerts a device sends |
| DoorRelay | A door station's relay and its passcode reference |
| DoorTrigger, DoorTriggerWindow | Input (doorbell, keypad, motion, RFID) → action rules and their time windows |
| SipEndpoint | A door station's SIP client |

No secret is ever stored here. Passwords, passcodes and keypad codes live in OpenBao; the `*_ref`
fields hold the OpenBao path and reject anything that looks like a value.

The OpenTofu `reolink` and `doorbird` providers (tofu-providers) realize these rows on the devices,
and Frigate can read cameras and streams from the same API.

## Install

Add `netbox_surveillance` to `PLUGINS` and run `manage.py migrate`.

## Tests

`python manage.py test netbox_surveillance --keepdb` on a NetBox dev instance. Tests use a real
database, never mocks.

## License

AGPL-3.0-or-later.
