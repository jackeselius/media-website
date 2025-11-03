from rest_framework import viewsets, permissions
from media.models import File
from .serializers import FileSerializer


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all().order_by('-id')
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        # Limit to current user's files by default
        user = self.request.user
        if user and user.is_authenticated:
            return qs.filter(owner=user.username)
        return qs.none()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['request'] = self.request
        return ctx
