"""
Legacy server-rendered media views have been retired.

All file operations are handled by the DRF viewset in media.api.views:
  - GET/POST /api/media/files/
  - DELETE   /api/media/files/:id/

This module remains to avoid import errors if referenced accidentally, but
intentionally exposes no views.
"""

from django.core.exceptions import ImproperlyConfigured

def _retired(*args, **kwargs):
    raise ImproperlyConfigured(
        "media.views legacy endpoints are retired. Use the JSON API under /api/media/."
    )
