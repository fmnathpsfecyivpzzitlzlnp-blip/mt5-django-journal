import os
import urllib.request
import re
from urllib.parse import unquote

import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render
from rest_framework import viewsets, serializers, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db.models import Sum, Q, Count
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from xhtml2pdf import pisa

from .models import Trade, PlaybookPattern, TradeScreenshot, ReviewStep, FAQBlock, FAQTopic, UserQuizProgress, Question, \
    AnswerChoice, Quiz, DailyBacktest
import csv
from datetime import datetime, timedelta
import pytz
import base64
from .serializers import TradeSerializer, FAQBlockSerializer, FAQTopicSerializer, \
    QuestionSerializer, QuizSerializer  # <--- ДОБАВИТЬ ЭТУ СТРОКУ
import random
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from .models import TradingRule
from .serializers import TradingRuleSerializer
from .models import DailyBacktest
import json

from django.http import HttpResponse
from django.template.loader import get_template

# Импорты для подмены шрифтов в ядре
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from xhtml2pdf.default import DEFAULT_FONT # 👈 Вот секретный ключ!
from rest_framework import filters


BROKER_TZ = pytz.timezone('Europe/Helsinki')



@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password: return Response({"error": "Укажите логин и пароль"},
                                                     status=status.HTTP_400_BAD_REQUEST)
    if User.objects.filter(username=username).exists(): return Response({"error": "Этот логин уже занят!"},
                                                                        status=status.HTTP_400_BAD_REQUEST)
    user = User.objects.create_user(username=username, password=password)
    return Response({"message": "Аккаунт успешно создан!"}, status=status.HTTP_201_CREATED)


class PlaybookSerializer(serializers.ModelSerializer):
    class Meta: model = PlaybookPattern; fields = '__all__'


class PlaybookViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]  # 👈 ДОБАВИТЬ ЭТУ СТРОК

    def list(self, request):
        patterns = PlaybookPattern.objects.filter(user=request.user).order_by('-created_at')
        data = [{
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "market_trend": p.market_trend,
            "entry_logic": p.entry_logic,
            "image_url": p.ideal_screenshot.url if p.ideal_screenshot else ""
        } for p in patterns]
        return Response(data)

    def create(self, request):
        try:
            image_file = request.FILES.get('image')
            image_url = request.data.get('image_url')

            # 👇 Используем нашу новую функцию для скачивания по ссылке
            if image_url and not image_file:
                downloaded_file, error_msg = download_tv_image(image_url)
                if error_msg:
                    return Response({"error": error_msg}, status=400)
                image_file = downloaded_file

            if not image_file:
                return Response({"error": "Нет ни файла, ни рабочей ссылки."}, status=400)

            # 👇 Сохраняем надежным способом через .save()
            p = PlaybookPattern(
                user=request.user,
                title=request.data.get('title'),
                description=request.data.get('description', ''),
                market_trend=request.data.get('market_trend', 'Лонговый'),
                entry_logic=request.data.get('entry_logic', 'По тренду')
            )
            # Привязываем скачанный файл к полю
            p.ideal_screenshot.save(image_file.name, image_file, save=False)
            p.save()

            return Response({"status": "Успешно добавлено!"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def destroy(self, request, pk=None):
        PlaybookPattern.objects.filter(id=pk, user=request.user).delete()
        return Response({"message": "Удалено из Playbook"}, status=204)

class TradeViewSet(viewsets.ModelViewSet):
    serializer_class = TradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def copy_trade(self, request, pk=None):
        import random
        orig_trade = self.get_object()

        # Генерируем новый тикет для копии
        new_ticket = f"Копия_{orig_trade.ticket}_{random.randint(100, 999)}"

        # 1. Создаем копию самой сделки
        new_trade = Trade.objects.create(
            user=orig_trade.user,
            ticket=new_ticket,
            symbol=orig_trade.symbol,
            type=orig_trade.type,
            volume=orig_trade.volume,
            entry_price=orig_trade.entry_price,
            profit=orig_trade.profit,
            time=orig_trade.time,
            strategy_name=orig_trade.strategy_name,
            setup_grade=orig_trade.setup_grade,
            market_trend=orig_trade.market_trend,
            entry_logic=orig_trade.entry_logic,
            confluence_factors=orig_trade.confluence_factors,
            comment=orig_trade.comment,
            psychology=orig_trade.psychology,
            is_processed=orig_trade.is_processed,
            magic_number=orig_trade.magic_number,
            mt5_comment=orig_trade.mt5_comment,
            screenshot_exit=orig_trade.screenshot_exit,
            auto_screen_m1=orig_trade.auto_screen_m1,
            auto_screen_m5=orig_trade.auto_screen_m5,
            auto_screen_m15=orig_trade.auto_screen_m15,
            auto_screen_h1=orig_trade.auto_screen_h1,
            auto_screen_h4=orig_trade.auto_screen_h4,
            auto_screen_d1=orig_trade.auto_screen_d1,
        )

        # 2. Копируем твои скрины анализа
        for screen in orig_trade.analysis_screens.all():
            TradeScreenshot.objects.create(
                trade=new_trade, timeframe=screen.timeframe,
                image=screen.image, description=screen.description
            )

        # 3. Копируем разборы RS
        for review in orig_trade.mentor_reviews.all():
            ReviewStep.objects.create(
                trade=new_trade, step_order=review.step_order,
                timeframe=review.timeframe, image=review.image,
                mentor_comment=review.mentor_comment, error_type=review.error_type
            )

        return Response({"message": "Сделка и разбор успешно скопированы!"}, status=201)

    @action(detail=False, methods=['post'])
    def cleanup_empty_trades(self, request):
        try:
            # Ищем пустые сделки ТОЛЬКО для текущего пользователя
            trades_to_delete = Trade.objects.filter(user=request.user).exclude(
                entry_logic='Чужая сделка'
            ).annotate(
                mentor_count=Count('mentor_reviews'),
                my_screens_count=Count('analysis_screens')
            ).filter(
                mentor_count=0,
                my_screens_count=0
            )

            count = trades_to_delete.count()

            if count == 0:
                return Response({"message": "База уже чиста! Пустых сделок не найдено."})

            # Удаляем их
            trades_to_delete.delete()

            return Response({"message": f"✅ Успешно очищено! Удалено пустых сделок: {count} шт."})

        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        import os
        from urllib.parse import quote
        from django.conf import settings
        from django.http import HttpResponse
        from django.template.loader import get_template
        from xhtml2pdf import pisa
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from xhtml2pdf.default import DEFAULT_FONT

        trade = self.get_object()

        # 👇 1. Подключаем идеальный шрифт для кириллицы (DejaVuSans)
        font_path = os.path.join(str(settings.BASE_DIR), 'fonts', 'DejaVuSans.ttf')
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            DEFAULT_FONT['sans-serif'] = 'DejaVu'
            DEFAULT_FONT['helvetica'] = 'DejaVu'
            DEFAULT_FONT['arial'] = 'DejaVu'
        except Exception as e:
            print(f"Ошибка загрузки шрифта: {e}")

        context = {
            'trade': trade,
            'user': request.user,
        }

        response = HttpResponse(content_type='application/pdf')

        # 👇 2. Формируем безопасную дату (заменяем : на - для Windows)
        date_str = trade.time.strftime('%d.%m.%Y_%H-%M')

        # 👇 3. Собираем красивое и безопасное имя файла
        file_name = f"Тикет_{trade.ticket}_Дата_{date_str}.pdf"

        # 👇 4. Отдаем браузеру в правильной кодировке (RFC 5987), чтобы русские буквы не сломались
        response['Content-Disposition'] = f"attachment; filename*=utf-8''{quote(file_name)}"

        template = get_template('trade_pdf_template.html')
        html = template.render(context)

        # 👇 5. Генерируем PDF (используем тот же link_callback, что и в FAQ)
        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            link_callback=link_callback,
            encoding='utf-8'
        )

        if pisa_status.err:
            return HttpResponse('Ошибка при создании PDF', status=500)
        return response

    def get_queryset(self):
        qs = Trade.objects.filter(user=self.request.user).order_by('-time')

        is_processed = self.request.query_params.get('is_processed')
        if is_processed is not None:
            qs = qs.filter(is_processed=(is_processed.lower() == 'true'))

        # 👇 ВОТ НАШ КВАНТОВЫЙ ПОИСК (ПО ЧАСТИ СЛОВА) 👇
        search_query = self.request.query_params.get('search')
        if search_query:
            qs = qs.filter(
                Q(ticket__icontains=search_query) |
                Q(symbol__icontains=search_query) |
                Q(comment__icontains=search_query) |
                Q(mt5_comment__icontains=search_query) |
                Q(analysis_screens__description__icontains=search_query) |
                Q(mentor_reviews__mentor_comment__icontains=search_query)
            ).distinct()  # 👈 Важно: distinct() гарантирует, что сделка не задвоится!

        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def upload_history(self, request):
        if 'file' not in request.FILES: return Response({"error": "Файл не найден"}, status=400)
        try:
            broker_offset_hours = int(request.POST.get('broker_offset', 3))
        except ValueError:
            broker_offset_hours = 3

        try:
            # Учитываем, что разделитель может быть точкой с запятой (как в твоем примере)
            decoded_file = request.FILES['file'].read().decode('utf-8').splitlines()
            # Пробуем определить разделитель (запятая или точка с запятой)
            dialect = csv.Sniffer().sniff(decoded_file[0]) if decoded_file else csv.excel
            reader = csv.DictReader(decoded_file, dialect=dialect)

            count = 0
            for row in reader:
                # В CSV из тестера названия колонок могут отличаться. Ищем варианты.
                ticket = row.get('Ticket') or row.get('Ticket ') or row.get('\ufeffTicket')  # \ufeff - это BOM маркер

                # Если тикета нет, пропускаем строку
                if not ticket: continue

                if not Trade.objects.filter(ticket=ticket, user=request.user).exists():

                    time_str = row.get('OpenTime') or row.get('Time')
                    try:
                        # В твоем примере формат "2026.04.01 01:08"
                        time_str = time_str.replace('.', '-')
                        naive_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                    except ValueError:
                        # Фолбэк на старый формат, если он с секундами
                        naive_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

                    utc_time = (naive_time - timedelta(hours=broker_offset_hours)).replace(tzinfo=pytz.UTC)

                    profit_str = row.get('Profit_USD') or row.get('Profit') or "0"

                    Trade.objects.create(
                        user=request.user,
                        ticket=ticket,
                        symbol=row.get('Symbol', 'UNKNOWN'),
                        type=row.get('Type', 'BUY'),
                        volume=float(row.get('Volume', 0)),
                        entry_price=float(row.get('OpenPrice') or row.get('Price', 0)),
                        profit=float(profit_str),
                        time=utc_time,

                        # 👇 ВОТ ГЛАВНАЯ МАГИЯ 👇
                        strategy_name="Прогон из тестера",
                        entry_logic="Сделка от робота",  # 👈 Теперь Аналитика их точно увидит!

                        magic_number=row.get('Magic', ''),
                        # 👈 Приклеиваем огромный ярлык [ТЕСТЕР] к комментарию, чтобы легко удалить
                        mt5_comment="[ТЕСТЕР] " + str(row.get('Comment', '')),

                        is_processed=True
                    )
                    count += 1
            return Response({"message": f"Успешно импортировано {count} тестовых сделок!"})
        except Exception as e:
            return Response({"error": f"Ошибка обработки файла: {str(e)}"}, status=400)

    @action(detail=False, methods=['post'])
    def bulk_process(self, request):
        trade_ids = request.data.get('trade_ids', [])
        comment = request.data.get('comment', '')
        psychology = request.data.get('psychology', '')
        strategy_name = request.data.get('strategy_name', '')
        setup_grade = request.data.get('setup_grade', '')
        confluence_factors = request.data.get('confluence_factors', '')

        # 👇 Достаем новые поля 👇
        market_trend = request.data.get('market_trend', '')
        entry_logic = request.data.get('entry_logic', '')

        if not trade_ids: return Response({"error": "Сделки не выбраны"}, status=400)
        trades = Trade.objects.filter(id__in=trade_ids, user=request.user)
        for trade in trades:
            if comment: trade.comment = comment
            if psychology: trade.psychology = psychology
            if strategy_name: trade.strategy_name = strategy_name
            if setup_grade: trade.setup_grade = setup_grade
            if confluence_factors: trade.confluence_factors = confluence_factors

            # 👇 Сохраняем новые поля 👇
            if market_trend: trade.market_trend = market_trend
            if entry_logic: trade.entry_logic = entry_logic

            trade.is_processed = True
            trade.save()
        return Response({"message": f"Успешно обработано {trades.count()} сделок!"})

    @action(detail=False, methods=['get'])
    def stats(self, request):
        try:
            tz_offset = int(request.query_params.get('tz_offset', 0))
        except ValueError:
            tz_offset = 0

        # 📊 НОВАЯ ЛОГИКА: Считаем сделки для меню
        inbox_count = Trade.objects.filter(user=self.request.user, is_processed=False).count()

        # 👇 ИСКЛЮЧАЕМ И ТЕСТЫ, И ЧУЖИЕ СДЕЛКИ ИЗ ВСЕХ РАСЧЕТОВ 👇
        trades_qs = Trade.objects.filter(user=self.request.user, is_processed=True).exclude(
            entry_logic__in=['Тест/Ошибка', 'Чужая сделка'])

        total_trades = trades_qs.count()

        if total_trades == 0:
            return Response({
                "message": "Нет сделок",
                "overview": {
                    "inbox_count": inbox_count, "journal_count": 0, "total_trades": 0,
                    "winrate_percent": 0, "total_pnl": 0, "avg_win": 0, "avg_loss": 0,
                    "rr_ratio": 0, "max_win_streak": 0, "max_loss_streak": 0
                },
                # Пустые заглушки, чтобы фронтенд не ломался
                "by_setup": [], "by_timeframe": [], "by_hour": [], "by_psychology": [],
                "chart_data": {"dates": [], "equity": []}, "logic_stats": []
            })

        winning_trades = trades_qs.filter(profit__gt=0).count()
        losing_trades = trades_qs.filter(profit__lt=0).count()
        winrate = (winning_trades / total_trades) * 100
        total_profit = trades_qs.aggregate(Sum('profit'))['profit__sum'] or 0

        trades_list = list(trades_qs.order_by('time'))
        wins = [t.profit for t in trades_list if t.profit > 0]
        losses = [t.profit for t in trades_list if t.profit < 0]
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        max_win_streak = max_loss_streak = curr_streak = 0
        curr_type = None
        hourly_pnl = {i: 0 for i in range(24)}

        # 👇 ДОБАВЛЕНО ДЛЯ НОВОГО ГРАФИКА ЭКВИТИ 👇
        daily_pnl = trades_qs.annotate(date=TruncDate('time')).values('date').annotate(
            daily_profit=Sum('profit')).order_by('date')
        dates = []
        equity_curve = []
        current_equity = 0
        for day in daily_pnl:
            if day['date']:
                dates.append(day['date'].strftime('%Y-%m-%d'))
                current_equity += day['daily_profit']
                equity_curve.append(round(current_equity, 2))
        # 👆 КОНЕЦ ВСТАВКИ ДЛЯ ЭКВИТИ 👆

        for t in trades_list:
            if t.profit > 0:
                if curr_type == 'win':
                    curr_streak += 1
                else:
                    curr_type = 'win';
                    curr_streak = 1
                max_win_streak = max(max_win_streak, curr_streak)
            elif t.profit < 0:
                if curr_type == 'loss':
                    curr_streak += 1
                else:
                    curr_type = 'loss';
                    curr_streak = 1
                max_loss_streak = max(max_loss_streak, curr_streak)
            if t.time:
                shifted_time = t.time + timedelta(hours=tz_offset)
                hourly_pnl[shifted_time.hour] += t.profit

        setups_data = trades_qs.values('strategy_name').annotate(pnl=Sum('profit')).order_by('-pnl')
        tf_data = trades_qs.values('timeframe').annotate(pnl=Sum('profit')).order_by('-pnl')
        hourly_data = [{"hour": f"{k:02d}:00", "pnl": round(v, 2)} for k, v in hourly_pnl.items()]
        psy_data = trades_qs.values('psychology').annotate(pnl=Sum('profit')).order_by('-pnl')
        formatted_psy = [{'psychology': p['psychology'] or 'Без метки', 'pnl': round(p['pnl'], 2)} for p in psy_data]

        # 👇 ДОБАВЛЕНО ДЛЯ ГРАФИКА ЛОГИКИ ВХОДА 👇
        logic_data = trades_qs.values('entry_logic').annotate(count=Count('id'), pnl=Sum('profit')).order_by('-pnl')
        formatted_logic = [
            {'entry_logic': l['entry_logic'] or 'Без логики', 'count': l['count'], 'total_profit': round(l['pnl'], 2)}
            for l in logic_data]

        return Response({
            "overview": {
                "inbox_count": inbox_count,
                "journal_count": total_trades,
                "total_trades": total_trades,
                "winrate_percent": round(winrate, 2),  # Оставил твое название ключа
                "total_pnl": round(total_profit, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "rr_ratio": round(rr_ratio, 2),
                "max_win_streak": max_win_streak,
                "max_loss_streak": max_loss_streak
            },
            "by_setup": list(setups_data),
            "by_timeframe": list(tf_data),
            "by_hour": hourly_data,
            "by_psychology": formatted_psy,

            # 👇 НОВЫЕ БЛОКИ ДЛЯ CHART.JS 👇
            "chart_data": {
                "dates": dates,
                "equity": equity_curve
            },
            "logic_stats": formatted_logic
        })

    @action(detail=True, methods=['post'])
    def add_analysis_screen(self, request, pk=None):
        trade = self.get_object()
        timeframe = request.data.get('timeframe', 'M1')
        description = request.data.get('description', '')

        image = request.FILES.get('image')
        image_url = request.data.get('image_url')

        # Если прислали ссылку, притворяемся браузером Chrome и качаем
        if image_url and not image:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                resp = requests.get(image_url.strip(), headers=headers, timeout=10)
                if resp.status_code == 200:
                    image = ContentFile(resp.content, name=f"tv_my_{trade.ticket}_{timeframe}.png")
                else:
                    return Response({
                                        "error": f"TradingView заблокировал скачивание (Код: {resp.status_code}). Попробуй вставить скриншот через Ctrl+V."},
                                    status=400)
            except Exception as e:
                return Response({"error": f"Ошибка соединения с TradingView: {str(e)}"}, status=400)

        if not image:
            return Response({"error": "Нужен скриншот или рабочая ссылка!"}, status=400)

        TradeScreenshot.objects.create(
            trade=trade, timeframe=timeframe, description=description, image=image
        )
        return Response({"message": "Твой анализ добавлен!"})

    @action(detail=True, methods=['post'])
    def add_mentor_review(self, request, pk=None):
        trade = self.get_object()
        error_type = request.data.get('error_type', 'LOGIC_FAIL')
        mentor_comment = request.data.get('mentor_comment', '')
        timeframe = request.data.get('timeframe', 'Общее')

        image = request.FILES.get('image')
        image_url = request.data.get('image_url')

        # Аналогично для разбора RS
        if image_url and not image:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                resp = requests.get(image_url.strip(), headers=headers, timeout=10)
                if resp.status_code == 200:
                    image = ContentFile(resp.content, name=f"tv_rs_{trade.ticket}.png")
                else:
                    return Response({"error": f"TradingView заблокировал скачивание (Код: {resp.status_code})."},
                                    status=400)
            except Exception as e:
                return Response({"error": f"Ошибка соединения с TradingView: {str(e)}"}, status=400)

        last_step = trade.mentor_reviews.order_by('-step_order').first()
        next_order = (last_step.step_order + 1) if last_step else 1

        ReviewStep.objects.create(
            trade=trade, step_order=next_order, error_type=error_type,
            mentor_comment=mentor_comment, image=image, timeframe=timeframe
        )
        return Response({"message": "Вердикт RS добавлен!"})

    @action(detail=False, methods=['delete'])
    def delete_feed_item(self, request):
        item_type = request.query_params.get('type')
        item_id = request.query_params.get('id')
        if item_type == 'my':
            TradeScreenshot.objects.filter(id=item_id, trade__user=request.user).delete()
        elif item_type == 'rs':
            ReviewStep.objects.filter(id=item_id, trade__user=request.user).delete()
        return Response({"message": "Успешно удалено!"})

    @action(detail=False, methods=['post'])
    def add_manual(self, request):
        data = request.data

        # Забираем автора из формы
        author = data.get('author', 'RS').strip()
        date_str = data.get('date')

        # 👇 НОВОЕ: Забираем условный профит из формы 👇
        profit_val = float(data.get('profit', 0.0))

        import random
        # Генерируем красивый именной тикет (напр: Регина_1482)
        ticket = f"{author}_{random.randint(1000, 9999)}"

        from django.utils import timezone
        from datetime import datetime

        if date_str:
            try:
                # Нам не нужно точное время, ставим просто 12:00 указанного дня
                trade_time = timezone.make_aware(datetime.strptime(f"{date_str} 12:00:00", "%Y-%m-%d %H:%M:%S"))
            except ValueError:
                trade_time = timezone.now()
        else:
            trade_time = timezone.now()

        try:
            trade = Trade.objects.create(
                user=request.user,
                ticket=ticket,
                symbol=data.get('symbol', 'XAUUSD').upper(),
                type=data.get('type', 'SELL'),
                volume=0.0,
                entry_price=0.0,
                profit=profit_val,  # 👈 ТЕПЕРЬ СТАВИМ РЕЗУЛЬТАТ (1 ИЛИ -1) ИЗ ФОРМЫ
                time=trade_time,
                strategy_name="Разбор чужой сделки",
                entry_logic="Чужая сделка",  # 👈 Гарантирует, что сделка не попадет в твою стату!
                is_processed=False  # Во Входящие
            )
            return Response({"message": "Чужая сделка добавлена!", "id": trade.id}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=False, methods=['post'])
    def bulk_delete(self, request):
        trade_ids = request.data.get('trade_ids', [])
        if not trade_ids:
            return Response({"error": "Сделки не выбраны"}, status=400)

        deleted_count, _ = Trade.objects.filter(id__in=trade_ids, user=request.user).delete()
        return Response({"message": f"Успешно удалено {deleted_count} сделок."})


@api_view(['POST'])
@permission_classes([AllowAny])
def mt5_webhook(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)

    if not user: return Response({"error": "Неверный логин или пароль MT5"}, status=401)

    ticket = request.data.get('ticket')
    symbol = request.data.get('symbol')
    trade_type = request.data.get('type')
    volume = request.data.get('volume')
    entry_price = request.data.get('entry_price')
    profit = request.data.get('profit')
    time_str = request.data.get('time')
    broker_offset_seconds = request.data.get('broker_offset', 10800)

    # 👇 Убрали коварные запятые в конце 👇
    magic_number = request.data.get('magic', '')
    mt5_comment = request.data.get('mt5_comment', '')

    # Достаем все 5 картинок из запроса
    screenshot_exit = request.data.get('screenshot_exit')
    screen_m1 = request.data.get('auto_screen_m1')
    screen_m5 = request.data.get('auto_screen_m5')
    screen_m15 = request.data.get('auto_screen_m15')
    screen_h1 = request.data.get('auto_screen_h1')
    screen_h4 = request.data.get('auto_screen_h4')  # НОВОЕ
    screen_d1 = request.data.get('auto_screen_d1')  # НОВОЕ

    if ticket is None or symbol is None or trade_type is None or volume is None or entry_price is None or profit is None or time_str is None:
        return Response({"error": "Неполные данные от MT5"}, status=400)

    if Trade.objects.filter(ticket=ticket, user=user).exists():
        return Response({"message": "Сделка уже есть в базе"}, status=200)

    try:
        naive_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        utc_time = naive_time - timedelta(seconds=int(broker_offset_seconds))
        utc_time = utc_time.replace(tzinfo=pytz.UTC)

        trade = Trade.objects.create(
            user=user, ticket=ticket, symbol=symbol, type=trade_type,
            volume=float(volume), entry_price=float(entry_price), profit=float(profit),
            time=utc_time, strategy_name="Новая из MT5", is_processed=False,

            # 👇 ПЕРЕДАЕМ ПЕРЕМЕННЫЕ ПРЯМО В БАЗУ 👇
            magic_number=magic_number,
            mt5_comment=mt5_comment
        )

        # Вспомогательная функция для сохранения base64 картинок
        def save_b64_image(b64_str, field, filename):
            if b64_str:
                try:
                    img_data = base64.b64decode(b64_str)
                    field.save(filename, ContentFile(img_data), save=False)
                except Exception as e:
                    print(f"Ошибка сохранения {filename}: {e}")

        # Сохраняем все картинки
        save_b64_image(screenshot_exit, trade.screenshot_exit, f"exit_{ticket}.png")
        save_b64_image(screen_m1, trade.auto_screen_m1, f"m1_{ticket}.png")
        save_b64_image(screen_m5, trade.auto_screen_m5, f"m5_{ticket}.png")
        save_b64_image(screen_m15, trade.auto_screen_m15, f"m15_{ticket}.png")
        save_b64_image(screen_h1, trade.auto_screen_h1, f"h1_{ticket}.png")
        save_b64_image(screen_h4, trade.auto_screen_h4, f"h4_{ticket}.png")
        save_b64_image(screen_d1, trade.auto_screen_d1, f"d1_{ticket}.png")

        trade.save()  # Записываем все изменения в БД

        return Response({"message": "Сделка и скриншоты успешно загружены!"}, status=201)
    except Exception as e:
        return Response({"error": str(e)}, status=400)

class TradingRuleViewSet(viewsets.ModelViewSet):
    serializer_class = TradingRuleSerializer
    permission_classes = [permissions.IsAuthenticated]

    # 👇 ВОТ ЭТИ ДВЕ СТРОЧКИ ДЕЛАЮТ МАГИЮ ПОИСКА 👇
    filter_backends = [filters.SearchFilter]
    search_fields = ['ticket', 'symbol', 'comment', 'analysis_screens__description', 'mentor_reviews__mentor_comment']

    def get_queryset(self):
        return TradingRule.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

def faq_view(request):
    return render(request, 'faq.html')


def link_callback(uri, rel):
    """Теперь это ищет только картинки, шрифты мы сюда больше не пускаем"""
    uri = unquote(uri)
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(str(settings.MEDIA_ROOT), uri.replace(settings.MEDIA_URL, ""))
        path = os.path.abspath(path)
        if os.path.isfile(path):
            return path
    return uri

def get_russian_font():
    """Автоматически скачивает и регистрирует 100% рабочий шрифт DejaVu Sans"""
    font_dir = os.path.join(settings.BASE_DIR, 'fonts')
    os.makedirs(font_dir, exist_ok=True)
    font_path = os.path.join(font_dir, 'DejaVuSans.ttf')

    # Если шрифта еще нет - скачиваем его
    if not os.path.exists(font_path):
        print("Скачиваем идеальный шрифт DejaVu Sans...")
        url = "https://github.com/prawnpdf/prawn/blob/master/data/fonts/DejaVuSans.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
            print("Шрифт успешно скачан!")
        except Exception as e:
            print(f"Ошибка скачивания шрифта: {e}")

    # Регистрируем шрифт в движке PDF
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))


class FAQTopicViewSet(viewsets.ModelViewSet):
    serializer_class = FAQTopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def export_pdf(self, request, pk=None):
        topic = self.get_object()
        blocks = topic.blocks.all()

        # 👇 МАГИЯ: Жестко подменяем стандартные шрифты библиотеки на твой DejaVu 👇
        # МАГИЯ: Жестко подменяем стандартные шрифты библиотеки на твой DejaVu
        # 1. Задаем пути к файлам шрифтов (обычный и жирный)
        font_path = os.path.join(str(settings.BASE_DIR), 'fonts', 'DejaVuSans.ttf')
        font_path_bold = os.path.join(str(settings.BASE_DIR), 'fonts', 'DejaVuSans-Bold.ttf')  # 👈 ПУТЬ К ЖИРНОМУ

        try:
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            # 3. Регистрируем жирный шрифт под именем 'DejaVu-Bold' 👈 ВОТ ОНО!
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_path_bold))

            # Говорим xhtml2pdf использовать наш шрифт по умолчанию
            DEFAULT_FONT['sans-serif'] = 'DejaVu'
            DEFAULT_FONT['helvetica'] = 'DejaVu'
            DEFAULT_FONT['arial'] = 'DejaVu'
        except Exception as e:
            print(f"Ошибка загрузки шрифта: {e}")

        context = {
            'topic': topic,
            'blocks': blocks,
            'user': request.user,
        }

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="FAQ_{topic.id}.pdf"'

        template = get_template('faq_pdf_template.html')
        html = template.render(context)

        pisa_status = pisa.CreatePDF(
            html,
            dest=response,
            link_callback=link_callback,
            encoding='utf-8'
        )

        if pisa_status.err:
            return HttpResponse('Ошибка при создании PDF', status=500)
        return response

    def get_queryset(self):
        return FAQTopic.objects.filter(user=self.request.user).order_by('created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)



class FAQBlockViewSet(viewsets.ModelViewSet):
    serializer_class = FAQBlockSerializer
    queryset = FAQBlock.objects.all()

    def create(self, request):
        try:
            topic_id = request.data.get('topic_id')
            text = request.data.get('text', '')
            image_file = request.FILES.get('image')
            image_url = request.data.get('image_url')

            # 👇 ТЕПЕРЬ FAQ ТОЖЕ ИСПОЛЬЗУЕТ НАШ УМНЫЙ ЗАГРУЗЧИК 👇
            if image_url and not image_file:
                downloaded_file, error_msg = download_tv_image(image_url)
                if error_msg:
                    return Response({"error": error_msg}, status=400)
                image_file = downloaded_file

            # Создаем блок ответа
            block = FAQBlock(topic_id=topic_id, text=text)

            # Если картинка успешно скачалась, привязываем её
            if image_file:
                block.image.save(image_file.name, image_file, save=False)

            block.save()
            return Response({'status': 'Блок добавлен', 'id': block.id})

        except Exception as e:
            return Response({'error': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quizzes(request):
    quizzes = Quiz.objects.all()
    data = []
    for q in quizzes:
        progress, _ = UserQuizProgress.objects.get_or_create(user=request.user, quiz=q)
        q_data = QuizSerializer(q).data
        q_data['progress'] = {
            'current_index': progress.current_question_index,
            'correct_count': progress.correct_answers_count,
            'is_completed': progress.is_completed
        }
        data.append(q_data)
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_quiz_question(request, quiz_id):
    progress = UserQuizProgress.objects.get(user=request.user, quiz_id=quiz_id)
    questions = Question.objects.filter(quiz_id=quiz_id).order_by('order')

    if progress.is_completed or progress.current_question_index >= questions.count():
        if not progress.is_completed:
            progress.is_completed = True
            progress.save()
        return Response({"completed": True, "score": progress.correct_answers_count, "total": questions.count()})

    current_q = questions[progress.current_question_index]
    return Response({
        "completed": False,
        "question": QuestionSerializer(current_q).data,
        "total_questions": questions.count(),
        "current_index": progress.current_question_index
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request, quiz_id):
    answer_id = request.data.get('answer_id')
    progress = UserQuizProgress.objects.get(user=request.user, quiz_id=quiz_id)

    try:
        answer = AnswerChoice.objects.get(id=answer_id)
        if answer.is_correct:
            progress.correct_answers_count += 1

        progress.current_question_index += 1
        progress.save()
        return Response({"is_correct": answer.is_correct, "next_index": progress.current_question_index})
    except AnswerChoice.DoesNotExist:
        return Response({"error": "Ответ не найден"}, status=400)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def backtest_grid_api(request):
    date_str = request.GET.get('date') or request.data.get('date')

    if request.method == 'GET':
        if not date_str:
            # Получаем все бэктесты
            history = DailyBacktest.objects.filter(user=request.user).order_by('-date')

            # Находим даты, когда были реальные сделки (не Тесты)
            trade_dates = Trade.objects.filter(
                user=request.user
            ).exclude(entry_logic='Тест/Ошибка').values_list('time__date', flat=True).distinct()

            real_trade_dates = [d.strftime("%Y-%m-%d") for d in trade_dates if d]

            data = []
            for h in history:
                curr_date = h.date.strftime("%Y-%m-%d")
                day_res = h.grid_data.get('day_result', '') if isinstance(h.grid_data, dict) else ''
                data.append({
                    "date": curr_date,
                    "result": day_res,
                    "has_real_trades": curr_date in real_trade_dates  # Флаг активности
                })
            return Response(data)

        # Отдача данных конкретного дня
        obj = DailyBacktest.objects.filter(user=request.user, date=date_str).first()
        if obj:
            data = {"yesterday_close": obj.yesterday_close or "", "today_plan": obj.today_plan or "",
                    "grid_data": obj.grid_data}
            if obj.chart_image: data["chart_image_url"] = obj.chart_image.url
            return Response(data)
        return Response({})

    elif request.method == 'POST':
        if not date_str: return Response({"error": "No date"}, status=400)
        grid_data_str = request.data.get('grid_data', '{}')
        grid_data = json.loads(grid_data_str) if isinstance(grid_data_str, str) else grid_data_str
        obj, _ = DailyBacktest.objects.update_or_create(
            user=request.user, date=date_str,
            defaults={'yesterday_close': request.data.get('yesterday_close', ''),
                      'today_plan': request.data.get('today_plan', ''), 'grid_data': grid_data}
        )
        if 'chart_image' in request.FILES:
            obj.chart_image = request.FILES['chart_image']
            obj.save()
        return Response({"message": "✅ Сохранено!"})

def backtest_page(request):
    return render(request, 'backtest.html') # Имя файла, куда ты сохранил HTML с таблицей бэктеста


def download_tv_image(url):
    """Умный парсер картинок TradingView"""
    url = url.strip()
    if not url.startswith('http'): url = 'https://' + url

    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200: return None, "Ошибка скачивания"

        # Если TV отдает HTML, ищем прямую ссылку на картинку внутри
        if 'text/html' in resp.headers.get('Content-Type', ''):
            match = re.search(r'property="og:image"\s+content="([^"]+)"', resp.text)
            if match:
                resp = requests.get(match.group(1), headers=headers, timeout=10)
            else:
                return None, "Не нашел картинку на странице"

        file_name = f"tv_playbook_{random.randint(1000, 9999)}.png"
        return ContentFile(resp.content, name=file_name), None
    except Exception as e:
        return None, str(e)

def guide_page(request):
    return render(request, 'guide.html')