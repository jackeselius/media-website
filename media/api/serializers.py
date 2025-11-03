from rest_framework import serializers
from media.models import File


class FileSerializer(serializers.ModelSerializer):
    icon = serializers.ImageField(required=False, allow_null=True, use_url=True)
    file = serializers.FileField(use_url=True)

    class Meta:
        model = File
        fields = [
            'id',
            'filename',
            'description',
            'owner',
            'icon',
            'file',
        ]
        read_only_fields = ['owner']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['owner'] = request.user.username
        # Default filename to uploaded file name if not provided
        if not validated_data.get('filename') and validated_data.get('file') is not None:
            validated_data['filename'] = validated_data['file'].name
        return super().create(validated_data)
