from django.contrib.auth.models import User
from django.db import models


class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ticket = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    type = models.CharField(max_length=10)
    volume = models.FloatField()
    entry_price = models.FloatField()
    profit = models.FloatField()
    time = models.DateTimeField()

    # ICT поля
    # Макро-контекст для фильтрации

    timeframe = models.CharField(max_length=10, blank=True, null=True)
    strategy_name = models.CharField(max_length=100, blank=True, null=True)
    setup_grade = models.CharField(max_length=5, blank=True, null=True)  # A+, B, C
    market_trend = models.CharField(max_length=50, blank=True, null=True)  # Лонг, Шорт, Боковик
    entry_logic = models.CharField(max_length=50, blank=True, null=True)  # По тренду, Разворот (Контр-тренд)

    confluence_factors = models.CharField(max_length=255, blank=True, null=True)

    comment = models.TextField(blank=True, null=True)
    psychology = models.CharField(max_length=100, blank=True, null=True)
    is_processed = models.BooleanField(default=False)

    # Старые поля пока оставляем, чтобы не сломать импорт, потом уберем
    screenshot_entry = models.ImageField(upload_to='trades/', blank=True, null=True)
    screenshot_exit = models.ImageField(upload_to='trades/', blank=True, null=True)
    # Автоматические скриншоты из MT5
    auto_screen_m1 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)
    auto_screen_m5 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)
    auto_screen_m15 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)
    auto_screen_h1 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)
    auto_screen_h4 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)  # НОВОЕ
    auto_screen_d1 = models.ImageField(upload_to='trades/auto/', blank=True, null=True)  # НОВОЕ

    def __str__(self):
        return f"{self.ticket} - {self.symbol}"


# 👇 НОВАЯ МОДЕЛЬ: Твои скриншоты по разным ТФ
class TradeScreenshot(models.Model):
    trade = models.ForeignKey(Trade, related_name='analysis_screens', on_delete=models.CASCADE)
    timeframe = models.CharField(max_length=10)  # H1, M15, M5, M1
    image = models.ImageField(upload_to='trades/analysis/')
    description = models.TextField(blank=True, null=True)  # Твои мысли: "Тут я видел слом"


# 👇 НОВАЯ МОДЕЛЬ: Лента разбора от RS
class ReviewStep(models.Model):
    trade = models.ForeignKey(Trade, related_name='mentor_reviews', on_delete=models.CASCADE)
    step_order = models.PositiveIntegerField(default=1)  # Порядок: 1, 2, 3...
    timeframe = models.CharField(max_length=10, blank=True, null=True)  # На каком ТФ RS нашел ошибку
    image = models.ImageField(upload_to='trades/reviews/', blank=True, null=True)

    mentor_comment = models.TextField(verbose_name="Что сказал RS")

    ERROR_CHOICES = [
        ('BIAS_ERROR', 'Против контекста HTF'),
        ('FAKE_BOS', 'Фейк-слом'),
        ('RANGE_MIDDLE', 'Вход в середине боковика'),
        ('LIQUIDITY_GAP', 'Игнор ликвидности'),
        ('EARLY_ENTRY', 'Спешка (не дождался закрытия)'),
        ('LOGIC_FAIL', 'Галлюцинация / Пиво')
    ]
    error_type = models.CharField(max_length=20, choices=ERROR_CHOICES, blank=True, null=True)

    class Meta:
        ordering = ['step_order']


class PlaybookPattern(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    setup_name = models.CharField(max_length=100)
    timeframe = models.CharField(max_length=10)
    ideal_screenshot = models.ImageField(upload_to='playbook/')
    created_at = models.DateTimeField(auto_now_add=True)