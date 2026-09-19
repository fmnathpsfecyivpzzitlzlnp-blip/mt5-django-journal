from django.contrib import admin
from .models import Trade, PlaybookPattern
from django.db import models
from tinymce.widgets import TinyMCE
from .models import CatalogCategory, CatalogItem, ItemVersion

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
    # 👇 Заменили старые поля на новые 👇
    list_display = ('title', 'market_trend', 'entry_logic', 'created_at')
    list_filter = ('market_trend', 'entry_logic')


# 1. Создаем встраиваемый блок (Inline) для Версий
class ItemVersionInline(admin.StackedInline):
    model = ItemVersion
    extra = 1  # По умолчанию открывать одну пустую форму для загрузки

    # Автоматически заменяем обычные текстовые поля на HTML-редактор TinyMCE
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 15})},
    }


# 2. Настраиваем главную карточку ресурса
class CatalogItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'category')

    # Встраиваем блок загрузки файлов и скриншотов ПРЯМО СЮДА
    inlines = [ItemVersionInline]

    # Для главного описания ресурса тоже включаем TinyMCE
    formfield_overrides = {
        models.TextField: {'widget': TinyMCE(attrs={'cols': 80, 'rows': 10})},
    }


# Регистрируем в админке
admin.site.register(CatalogCategory)
admin.site.register(CatalogItem, CatalogItemAdmin)
admin.site.register(ItemVersion)  # Отдельная ссылка пусть останется для удобства