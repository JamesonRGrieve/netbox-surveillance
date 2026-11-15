# SPDX-License-Identifier: AGPL-3.0-or-later
from netbox.api.routers import NetBoxRouter

from ..urls import SLUGS
from .views import VIEWSETS

app_name = "netbox_surveillance"

router = NetBoxRouter()
for model, viewset in VIEWSETS.items():
    router.register(SLUGS[model._meta.model_name], viewset)

urlpatterns = router.urls
