import threading
import MetaTrader5 as mt5
from django.conf import settings

# Глобальный блокировщик для предотвращения конфликтов в COM-интерфейсе
_mt5_lock = threading.Lock()


class MT5Bridge:
    @staticmethod
    def execute_market_order(symbol, action_type, volume, comment=""):
        """
        Прямое открытие сделки по рынку с локального ПК.
        action_type: "BUY" или "SELL"
        """
        with _mt5_lock:
            # 1. Инициализация подключения к терминалу
            if not mt5.initialize():
                return {"status": "error", "message": f"MT5 Init Failed: {mt5.last_error()}"}

            # 2. Проверка доступности символа
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                mt5.shutdown()
                return {"status": "error", "message": f"Символ {symbol} не найден в терминале."}

            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    mt5.shutdown()
                    return {"status": "error", "message": f"Не удалось активировать символ {symbol}"}

            # 3. Определение направления и цены
            order_type = mt5.ORDER_TYPE_BUY if action_type == "BUY" else mt5.ORDER_TYPE_SELL
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                mt5.shutdown()
                return {"status": "error", "message": "Не удалось получить текущий тик (цену)."}

            price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid

            # 4. Формирование структуры запроса для MetaQuotes API
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": order_type,
                "price": price,
                "deviation": 20,  # Допустимое проскальзывание в пунктах
                "comment": f"Django: {comment}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Исполнить или отменить
            }

            # 5. Отправка приказа на сервер брокера
            result = mt5.order_send(request)

            # Обязательно закрываем сессию подключения
            mt5.shutdown()

            # 6. Анализ ответа кода возврата (Retcode)
            if result is None:
                return {"status": "error", "message": "Терминал не вернул ответ."}

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    "status": "error",
                    "code": result.retcode,
                    "message": f"Брокер отклонил ордер: {result.comment} (Код: {result.retcode})"
                }

            # Успех
            return {
                "status": "ok",
                "ticket": result.order,
                "price": result.price,
                "volume": result.volume
            }