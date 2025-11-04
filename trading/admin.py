from django.contrib import admin
from .models import Trade


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('politician_name', 'ticker', 'action', 'trade_date', 'amount', 'disclosure_date')
    list_filter = ('action', 'trade_date', 'disclosure_date')
    search_fields = ('politician_name', 'ticker', 'asset_description')
    date_hierarchy = 'trade_date'
    ordering = ('-trade_date', '-created_at')
