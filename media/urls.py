"""
Legacy server-rendered routes for the media app have been retired in favor of
the JSON API under /api/media/ ... provided by media.api.urls.

This module is intentionally left with an empty urlpatterns to avoid exposure
of outdated HTML endpoints.
"""

from django.urls import path

urlpatterns = []
