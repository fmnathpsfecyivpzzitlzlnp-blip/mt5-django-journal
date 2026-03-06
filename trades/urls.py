from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TradeViewSet, PlaybookViewSet, register_user, mt5_webhook

router = DefaultRouter()
router.register(r'trades', TradeViewSet, basename='trade')
router.register(r'playbook', PlaybookViewSet, basename='playbook')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('mt5_webhook/', mt5_webhook, name='mt5_webhook'), # 👈 Добавили маршрут
]