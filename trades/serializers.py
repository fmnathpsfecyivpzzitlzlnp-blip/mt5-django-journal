from rest_framework import serializers
from .models import Trade, PlaybookPattern, TradeScreenshot, ReviewStep

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