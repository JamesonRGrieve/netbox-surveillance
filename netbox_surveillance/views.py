# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.views import generic

from . import filtersets
from .forms import FILTER_FORMS, FORM_FIELDS, MODEL_FORMS
from .tables import TABLES


def _detail_fields(model):
    shown = [f for f in FORM_FIELDS[model] if f != "tags"]

    def get_extra_context(self, request, instance):
        return {"fields": [(model._meta.get_field(f).verbose_name, getattr(instance, f)) for f in shown]}

    return get_extra_context


def _views(model):
    """The five generic views of one model: detail, list, edit, delete, bulk delete."""
    qs = model.objects.all()
    fs = getattr(filtersets, f"{model.__name__}FilterSet")
    return {
        "detail": type(
            f"{model.__name__}View",
            (generic.ObjectView,),
            {
                "queryset": qs,
                "template_name": "netbox_surveillance/object.html",
                "get_extra_context": _detail_fields(model),
            },
        ),
        "list": type(
            f"{model.__name__}ListView",
            (generic.ObjectListView,),
            {"queryset": qs, "table": TABLES[model], "filterset": fs, "filterset_form": FILTER_FORMS[model]},
        ),
        "edit": type(
            f"{model.__name__}EditView", (generic.ObjectEditView,), {"queryset": qs, "form": MODEL_FORMS[model]}
        ),
        "delete": type(f"{model.__name__}DeleteView", (generic.ObjectDeleteView,), {"queryset": qs}),
        "bulk_delete": type(
            f"{model.__name__}BulkDeleteView", (generic.BulkDeleteView,), {"queryset": qs, "table": TABLES[model]}
        ),
    }


VIEWS = {m: _views(m) for m in FORM_FIELDS}
