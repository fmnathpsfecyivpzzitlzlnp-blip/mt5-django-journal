from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views
from .views import TradeViewSet, PlaybookViewSet, mt5_webhook, TradingRuleViewSet, MT5DirectExecuteView, AIForecastView

router = DefaultRouter()
# Твои сделки
router.register(r'trades', TradeViewSet, basename='trade')
# API для Playbook
router.register(r'playbook', PlaybookViewSet, basename='playbook')
router.register(r'rules', TradingRuleViewSet, basename='rules')
router.register(r'faq_topics', views.FAQTopicViewSet, basename='faq-topics')
router.register(r'faq_blocks', views.FAQBlockViewSet, basename='faq-blocks')

urlpatterns = [
    path('', include(router.urls)),

    # 👇 НОВОЕ: Учим Django принимать данные от советника по этому адресу 👇
    path('mt5_webhook/', mt5_webhook, name='mt5_webhook'),
    path('faq/', views.faq_view, name='faq'),
    path('api/quizzes/', views.get_quizzes),
    path('api/quizzes/<int:quiz_id>/question/', views.get_quiz_question),
    path('api/quizzes/<int:quiz_id>/submit/', views.submit_answer),
    # 1. Путь для самой страницы (Без слова api!)
    path('backtest/', views.backtest_page, name='backtest'),

    # 2. Путь для сохранения и загрузки данных (API)
    path('api/backtest/', views.backtest_grid_api),

    path('forecast/', views.forecast_page, name='forecast'),
    path('api/kronos_forecast/', views.get_kronos_forecast, name='api_kronos_forecast'),
    path('api/ai_forecast/', AIForecastView.as_view(), name='ai_forecast'),
]