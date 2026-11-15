# SPDX-License-Identifier: AGPL-3.0-or-later
from django.urls import path
from netbox.views.generic import ObjectChangeLogView, ObjectJournalView

from .models import MODELS
from .views import VIEWS

# URL slug per model (also the REST route).
SLUGS = {
    "camera": "cameras",
    "stream": "streams",
    "recordingschedule": "recording-schedules",
    "motiondetection": "motion-detection",
    "notification": "notifications",
    "doorrelay": "door-relays",
    "doortrigger": "door-triggers",
    "doortriggerwindow": "door-trigger-windows",
    "sipendpoint": "sip-endpoints",
}


def _routes(model):
    name, v = model._meta.model_name, VIEWS[model]
    slug = SLUGS[name]
    return [
        path(f"{slug}/", v["list"].as_view(), name=f"{name}_list"),
        path(f"{slug}/add/", v["edit"].as_view(), name=f"{name}_add"),
        path(f"{slug}/delete/", v["bulk_delete"].as_view(), name=f"{name}_bulk_delete"),
        path(f"{slug}/<int:pk>/", v["detail"].as_view(), name=name),
        path(f"{slug}/<int:pk>/edit/", v["edit"].as_view(), name=f"{name}_edit"),
        path(f"{slug}/<int:pk>/delete/", v["delete"].as_view(), name=f"{name}_delete"),
        path(
            f"{slug}/<int:pk>/changelog/",
            ObjectChangeLogView.as_view(),
            name=f"{name}_changelog",
            kwargs={"model": model},
        ),
        path(f"{slug}/<int:pk>/journal/", ObjectJournalView.as_view(), name=f"{name}_journal", kwargs={"model": model}),
    ]


urlpatterns = [route for model in MODELS for route in _routes(model)]
