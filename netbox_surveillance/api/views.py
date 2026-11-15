# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.viewsets import NetBoxModelViewSet

from .. import filtersets
from ..forms import FORM_FIELDS
from .serializers import SERIALIZERS

_RELATED = {"device", "recorder", "camera", "relay", "notification", "trigger"}


def _viewset(model):
    related = [f for f in FORM_FIELDS[model] if f in _RELATED]
    return type(
        f"{model.__name__}ViewSet",
        (NetBoxModelViewSet,),
        {
            "queryset": model.objects.select_related(*related).prefetch_related("tags"),
            "serializer_class": SERIALIZERS[model],
            "filterset_class": getattr(filtersets, f"{model.__name__}FilterSet"),
        },
    )


VIEWSETS = {m: _viewset(m) for m in FORM_FIELDS}
