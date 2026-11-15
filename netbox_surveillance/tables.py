# SPDX-License-Identifier: AGPL-3.0-or-later
import django_tables2 as tables
from netbox.tables import NetBoxTable, columns

from .forms import FORM_FIELDS

# Columns linkified when they hold a related object; choice columns get their colour badge.
_LINKED = {"device", "recorder", "camera", "relay", "notification", "trigger"}
_CHOICES = {"role", "codec", "mode", "kind", "input", "action"}


def _table(model):
    name = model._meta.model_name
    shown = [f for f in FORM_FIELDS[model] if f != "tags"]
    attrs = {
        "pk_link": tables.Column(accessor="pk", linkify=True, verbose_name="ID"),
        "tags": columns.TagColumn(url_name=f"plugins:netbox_surveillance:{name}_list"),
    }
    for f in shown:
        if f in _LINKED:
            attrs[f] = tables.Column(linkify=True)
        elif f in _CHOICES:
            attrs[f] = columns.ChoiceFieldColumn()
    attrs["Meta"] = type(
        "Meta",
        (NetBoxTable.Meta,),
        {
            "model": model,
            "fields": ("pk", "id", "pk_link", *shown, "tags", "created", "last_updated"),
            "default_columns": ("pk_link", *shown[:6]),
        },
    )
    return type(f"{model.__name__}Table", (NetBoxTable,), attrs)


TABLES = {m: _table(m) for m in FORM_FIELDS}
