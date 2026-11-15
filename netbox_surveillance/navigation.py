# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem


def _item(model, label):
    return PluginMenuItem(
        link=f"plugins:netbox_surveillance:{model}_list",
        link_text=label,
        buttons=[PluginMenuButton(f"plugins:netbox_surveillance:{model}_add", "Add", "mdi mdi-plus-thick")],
    )


menu = PluginMenu(
    label="Surveillance",
    groups=(
        (
            "Cameras",
            (
                _item("camera", "Cameras"),
                _item("stream", "Streams"),
                _item("recordingschedule", "Recording schedules"),
                _item("motiondetection", "Motion detection"),
            ),
        ),
        ("Alerts", (_item("notification", "Notifications"),)),
        (
            "Door stations",
            (
                _item("doorrelay", "Relays"),
                _item("doortrigger", "Triggers"),
                _item("doortriggerwindow", "Trigger windows"),
                _item("sipendpoint", "SIP endpoints"),
            ),
        ),
    ),
    icon_class="mdi mdi-cctv",
)
