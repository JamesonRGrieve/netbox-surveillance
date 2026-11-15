# SPDX-License-Identifier: AGPL-3.0-or-later
"""netbox-surveillance: NetBox as the native, vendor-neutral source of truth for IP cameras,
NVRs and door stations: cameras and the NVR channel each sits on, their streams, recording
schedules, motion detection, notifications, and a door station's relays, triggers and SIP endpoint.

The devices themselves, their interfaces, addresses and WiFi stay native DCIM / IPAM / wireless.
Every model here hangs off ``dcim.Device``. The ``reolink`` and ``doorbird`` OpenTofu providers
realize these rows on the devices; Frigate reads cameras and streams from the same rows.

**Standalone SoT, no plugin dependency.** FKs only core NetBox.

**Secret policy (load-bearing):** no password, passcode or keypad code is ever a field here.
``*_ref`` fields are OpenBao KV path references, validated by :func:`validate_openbao_ref`.
"""

from netbox.plugins import PluginConfig

__version__ = "0.0.1"


class NetBoxSurveillanceConfig(PluginConfig):
    name = "netbox_surveillance"
    verbose_name = "NetBox Surveillance"
    description = "Vendor-neutral SoT for IP cameras, NVRs and door stations"
    version = __version__
    author = "Jameson"
    base_url = "surveillance"
    min_version = "4.6.0"
    max_version = "4.6.99"


config = NetBoxSurveillanceConfig
