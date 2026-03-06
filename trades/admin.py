from django.contrib import admin
from .models import Trade, PlaybookPattern


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    # Какие колонки видеть в списке
    list_display = ('time', 'symbol', 'type', 'volume', 'entry_price', 'profit', 'strategy_name')

    # Фильтры справа (удобно фильтровать по парам или стратегиям)
    list_filter = ('symbol', 'type', 'strategy_name')

    # Поиск по тикету или комментарию
    search_fields = ('ticket', 'symbol', 'comment')

    # Сортировка (сначала новые)
    ordering = ('-time',)
# НОВОЕ: Регистрируем Playbook, чтобы он появился в админке
@admin.register(PlaybookPattern)
class PlaybookPatternAdmin(admin.ModelAdmin):
    list_display = ('title', 'setup_name', 'timeframe', 'created_at')
    list_filter = ('setup_name', 'timeframe')