from rest_framework import serializers
from .models import Trade, PlaybookPattern, TradeScreenshot, ReviewStep, TradingRule, FAQBlock, FAQTopic


class TradeScreenshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeScreenshot
        fields = '__all__'

class ReviewStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewStep
        fields = '__all__'

class TradeSerializer(serializers.ModelSerializer):
    # 👇 ИМЕННО ЭТИ ДВЕ СТРОКИ ГОВОРЯТ DJANGO ОТДАВАТЬ КАРТИНКИ 👇
    analysis_screens = TradeScreenshotSerializer(many=True, read_only=True)
    mentor_reviews = ReviewStepSerializer(many=True, read_only=True)

    class Meta:
        model = Trade
        fields = '__all__'

class TradingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradingRule
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class FAQBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQBlock
        fields = '__all__'

class FAQTopicSerializer(serializers.ModelSerializer):
    blocks = FAQBlockSerializer(many=True, read_only=True) # Вкладываем ответы в вопрос

    class Meta:
        model = FAQTopic
        fields = '__all__'
        read_only_fields = ['user', 'created_at']