from django.db import models


class Trade(models.Model):
    """Model for politician stock trades"""
    ACTION_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    politician_name = models.CharField(max_length=200)
    ticker = models.CharField(max_length=20)
    action = models.CharField(max_length=4, choices=ACTION_CHOICES)
    trade_date = models.DateField()
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    disclosure_date = models.DateField(null=True, blank=True)
    
    # Optional metadata
    asset_description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-trade_date', '-created_at']
    
    def __str__(self):
        return f"{self.politician_name} - {self.action} {self.ticker} on {self.trade_date}"
