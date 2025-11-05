from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeViewSet, SyncStatusView

router = DefaultRouter()
router.register(r'trades', TradeViewSet, basename='trade')

urlpatterns = [
    path('', include(router.urls)),
    path('status/', SyncStatusView.as_view(), name='trading-status'),
]
