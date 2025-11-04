from rest_framework import serializers
from trading.models import Trade


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = [
            'id',
            'politician_name',
            'ticker',
            'action',
            'trade_date',
            'amount',
            'disclosure_date',
            'asset_description',
            'notes',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
