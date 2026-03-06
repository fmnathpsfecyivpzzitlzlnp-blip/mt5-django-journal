import MetaTrader5 as mt5
import requests
from datetime import datetime, timedelta

WEBHOOK_URL = "http://127.0.0.1:8000/api/mt5_webhook/"
USER_DATA = {'username': 'trader1', 'password': '1qaz2wsxZX!@'}


def load_history():
    if not mt5.initialize():
        print("❌ MT5 не запущен!")
        return

    # 👇 МАГИЯ: Берем время с запасом на 1 день вперед, чтобы избежать конфликтов часовых поясов брокера и ПК
    future_date = datetime.now() + timedelta(days=1)

    # Берем историю с начала 2023 года по "завтра"
    history = mt5.history_deals_get(datetime(2023, 1, 1), future_date)
    count = 0

    if history:
        print(f"🔄 Найдено ВСЕГО операций в терминале: {len(history)} (Входы, Выходы, Баланс).")
        for deal in history:
            # Нам нужны только ВЫХОДЫ (когда фиксируется PnL)
            if deal.entry == mt5.DEAL_ENTRY_OUT or deal.entry == mt5.DEAL_ENTRY_INOUT:
                symbol = deal.symbol

                # Мы убрали фильтр по золоту. Теперь грузятся ЛЮБЫЕ пары!

                trade_payload = {
                    "username": USER_DATA['username'],
                    "password": USER_DATA['password'],
                    "ticket": str(deal.ticket),  # Тикет сделки выхода
                    "symbol": symbol,
                    "type": "BUY" if deal.type == mt5.DEAL_TYPE_SELL else "SELL",
                    "volume": deal.volume,
                    "entry_price": deal.price,
                    "profit": deal.profit,
                    "time": datetime.fromtimestamp(deal.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "broker_offset": "10800"
                }

                try:
                    # Добавили timeout=5, чтобы скрипт не мог зависнуть физически
                    res = requests.post(WEBHOOK_URL, json=trade_payload, timeout=5)

                    if res.status_code == 201:
                        print(f"✅ НОВАЯ: #{deal.ticket} ({symbol}) | PnL: ${deal.profit}")
                        count += 1
                    elif res.status_code == 200:
                        # Теперь он будет писать в консоль, что пропустил сделку
                        print(f"⏭️ Пропуск #{deal.ticket} (уже есть в базе)")
                    else:
                        print(f"❌ Ошибка #{deal.ticket}: {res.text}")
                except requests.exceptions.ReadTimeout:
                    print(f"⏳ Сервер долго думает над #{deal.ticket}, пропускаем...")
                except Exception as e:
                    print(f"❌ Ошибка сети: {e}")

    mt5.shutdown()
    print(f"🏁 УРА! Историческая загрузка завершена. Добавлено НОВЫХ сделок: {count} шт.")


if __name__ == "__main__":
    load_history()