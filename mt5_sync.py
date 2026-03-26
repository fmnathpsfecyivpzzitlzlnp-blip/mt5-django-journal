import os
import MetaTrader5 as mt5
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем пароли из скрытого файла .env
load_dotenv()

# Настройки сайта
WEBHOOK_URL = "http://127.0.0.1:8000/api/mt5_webhook/"
SITE_USER = os.getenv("SITE_USER")
SITE_PASS = os.getenv("SITE_PASS")

# Настройки MT5
MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
MT5_PASSWORD = os.getenv("MT5_PASSWORD")
MT5_SERVER = os.getenv("MT5_SERVER")

def load_history():
    if not MT5_LOGIN or not MT5_PASSWORD:
        print("❌ Ошибка: В файле .env не заполнены данные MT5!")
        return

    print(f"Подключаемся к терминалу и счету {MT5_LOGIN}...")

    # Авторизация в MT5
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print(f"❌ Ошибка подключения к MT5! Код ошибки: {mt5.last_error()}")
        return

    print("✅ Успешно подключились! Начинаем сбор истории...")

    future_date = datetime.now() + timedelta(days=1)
    history = mt5.history_deals_get(datetime(2023, 1, 1), future_date)
    count = 0
    errors = 0

    if history:
        print(f"🔄 Найдено ВСЕГО операций в терминале: {len(history)}")

        for deal in history:
            # Нам нужны только выходы (закрытые позиции)
            if deal.entry == mt5.DEAL_ENTRY_OUT or deal.entry == mt5.DEAL_ENTRY_INOUT:

                # Отсекаем пополнения баланса и комиссии
                if deal.type not in [mt5.DEAL_TYPE_BUY, mt5.DEAL_TYPE_SELL] or not deal.symbol or deal.volume <= 0:
                    continue

                magic_number = deal.magic if deal.magic is not None else 0
                comment = deal.comment if deal.comment is not None else ""

                # 👇 ВОТ ТУТ МЫ ВЕРНУЛИ 'entry_price', ЧТОБЫ УШЛА ОШИБКА 400 👇
                trade_payload = {
                    "username": SITE_USER,
                    "password": SITE_PASS,
                    "ticket": str(deal.ticket),
                    "symbol": deal.symbol,
                    "type": "BUY" if deal.type == mt5.DEAL_TYPE_SELL else "SELL",
                    "volume": deal.volume,
                    "entry_price": deal.price,  # <--- ВОТ ЭТО ПОЛЕ
                    "profit": deal.profit,
                    "time": datetime.fromtimestamp(deal.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "broker_offset": "10800",
                    "magic": str(magic_number),
                    "mt5_comment": comment
                }

                try:
                    res = requests.post(WEBHOOK_URL, json=trade_payload, timeout=10)

                    if res.status_code == 201:
                        print(f"✅ ДОБАВЛЕНА: #{deal.ticket} ({deal.symbol}) | PnL: ${deal.profit}")
                        count += 1
                    elif res.status_code == 200:
                        pass # Сделка уже есть, молчим
                    else:
                        print(f"❌ Ошибка #{deal.ticket}: {res.status_code} | {res.text}")
                        errors += 1
                except requests.exceptions.ReadTimeout:
                    print(f"⏳ Таймаут на #{deal.ticket}, сервер долго думает...")
                    errors += 1
                except Exception as e:
                    print(f"❌ Ошибка сети: {e}")
                    errors += 1
    else:
        print("⚠️ История пуста.")

    mt5.shutdown()
    print(f"\n🏁 ЗАВЕРШЕНО. Добавлено: {count} шт. Ошибок: {errors} шт.")

if __name__ == "__main__":
    load_history()