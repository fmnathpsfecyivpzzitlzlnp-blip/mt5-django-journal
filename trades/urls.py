from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import TradeViewSet, PlaybookViewSet, mt5_webhook, TradingRuleViewSet

router = DefaultRouter()
# Твои сделки
router.register(r'trades', TradeViewSet, basename='trade')
# API для Playbook
router.register(r'playbook', PlaybookViewSet, basename='playbook')
router.register(r'rules', TradingRuleViewSet, basename='rules')

urlpatterns = [
    path('', include(router.urls)),

    # 👇 НОВОЕ: Учим Django принимать данные от советника по этому адресу 👇
    path('mt5_webhook/', mt5_webhook, name='mt5_webhook'),
]