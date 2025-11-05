from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
import os
import json
from trading.models import Trade
from .serializers import TradeSerializer


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for politician trades.
    Future: add POST for copy trading feature.
    """
    queryset = Trade.objects.all().order_by('-trade_date', '-id')
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]


class SyncStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Try reading status file written by sync command
        status_path = os.path.join(getattr(settings, 'MEDIA_ROOT', '.'), 'sync', 'trading_status.json')
        payload = {}
        try:
            if os.path.exists(status_path):
                with open(status_path, 'r', encoding='utf-8') as f:
                    payload = json.load(f)
        except Exception:
            payload = {}

        # Fallbacks if file missing or incomplete
        last_updated_from_db = Trade.objects.order_by('-updated_at').values_list('updated_at', flat=True).first()
        if not payload.get('last_attempt_at'):
            payload['last_attempt_at'] = (last_updated_from_db or timezone.now()).isoformat()
        if not payload.get('last_success_at') and last_updated_from_db:
            payload['last_success_at'] = last_updated_from_db.isoformat()
        if 'total' not in payload:
            payload['total'] = Trade.objects.count()

        return Response(payload)
