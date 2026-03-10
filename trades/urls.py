from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeViewSet, PlaybookViewSet

router = DefaultRouter()
# Твои сделки
router.register(r'trades', TradeViewSet, basename='trade')
# 👇 НОВОЕ: API для Playbook
router.register(r'playbook', PlaybookViewSet, basename='playbook')

urlpatterns = [
    path('', include(router.urls)),
]