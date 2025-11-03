"""
Legacy Django forms for server-rendered uploads are no longer used.
Uploads are handled via the REST API (multipart/form-data) at /api/media/files/.
"""

from django.core.exceptions import ImproperlyConfigured

class FileForm:  # stub to guard accidental imports
    def __init__(self, *args, **kwargs):
        raise ImproperlyConfigured(
            "media.forms.FileForm is retired. Use the REST API from the SPA instead."
        )
