from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from trading.models import Trade
from .serializers import TradeSerializer


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for politician trades.
    Future: add POST for copy trading feature.
    """
    queryset = Trade.objects.all()
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
