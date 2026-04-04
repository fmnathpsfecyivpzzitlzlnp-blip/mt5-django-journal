from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField


class Trade(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ticket = models.CharField(max_length=50)
    symbol = models.CharField(max_length=20)
    type = models.CharField(max_length=10)
    volume = models.FloatField()
    entry_price = models.FloatField()
    profit = models.FloatField()
    time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True, null=True)

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

    # 👇 НОВЫЕ ПОЛЯ ДЛЯ MT5 👇
    magic_number = models.CharField("Magic Number", max_length=50, blank=True, null=True)
    mt5_comment = models.CharField("MT5 Комментарий", max_length=255, blank=True, null=True)

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

    # Наши 4 квадранта
    market_trend = models.CharField(max_length=50, blank=True, null=True)  # Лонговый / Шортовый
    entry_logic = models.CharField(max_length=50, blank=True, null=True)  # По тренду / Разворот

    ideal_screenshot = models.ImageField(upload_to='playbook/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.market_trend} | {self.entry_logic} - {self.title}"


class TradingRule(models.Model):
    CATEGORY_CHOICES = [
        # Категории для Дзена Трейдера (Плейбук)
        ('mantra', '📜 Мантра'),
        ('rule', '💎 Золотое правило'),
        ('warning', '⚠️ Признак тильта'),

        # 👇 НОВЫЕ КАТЕГОРИИ ДЛЯ КОНСТИТУЦИИ (Дневник) 👇
        ('rev_entry', '🔄 Вход: Разворот'),
        ('trend_entry', '✅ Вход: По тренду'),
        ('psy_base', '🛑 Психология и База')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField("Категория", max_length=20, choices=CATEGORY_CHOICES, default='rule')
    text = models.TextField("Текст правила")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_category_display()} - {self.user.username}"

class FAQTopic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField("Рубрика", max_length=100)
    question = models.CharField("Вопрос / Тема", max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question

class FAQBlock(models.Model):
    topic = models.ForeignKey(FAQTopic, related_name='blocks', on_delete=models.CASCADE)
    text = models.TextField("Текст ответа", blank=True, null=True)
    image = models.ImageField("Скриншот", upload_to='faq/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

# 👇 МОДЕЛИ ДЛЯ СИСТЕМЫ ТЕСТИРОВАНИЯ 👇
class Quiz(models.Model):
    title = models.CharField("Название теста", max_length=200)
    description = models.TextField("Описание", blank=True, null=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, related_name='questions', on_delete=models.CASCADE)
    text = models.TextField("Текст вопроса")
    order = models.PositiveIntegerField("Порядок (номер вопроса)", default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.quiz.title} - Вопрос {self.order}"

class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField("Вариант ответа", max_length=255)
    is_correct = models.BooleanField("Это правильный ответ?", default=False)

    def __str__(self):
        return self.text

class UserQuizProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    current_question_index = models.IntegerField(default=0)
    correct_answers_count = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    last_accessed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title} (Прогресс: {self.current_question_index})"


class DailyBacktest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField("Дата бэктеста")
    yesterday_close = models.TextField("Вчерашнее закрытие", blank=True, null=True)
    today_plan = models.TextField("План на сегодня", blank=True, null=True)

    # 👇 НОВОЕ ПОЛЕ ДЛЯ СКРИНШОТА ГРАФИКА 👇
    chart_image = models.ImageField(upload_to='backtest_screens/', blank=True, null=True)

    grid_data = JSONField("Матрица ТФ", default=dict)

    class Meta:
        unique_together = ('user', 'date')

    def __str__(self):
        return f"Бэктест {self.user.username} - {self.date}"