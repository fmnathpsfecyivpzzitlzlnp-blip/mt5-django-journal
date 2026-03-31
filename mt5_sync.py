import os
import re
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

    # Берем историю с 2023 года по завтра
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
                pos_id = deal.position_id

                entry_comment = ""

                # 1. Ищем коммент в исходном ОРДЕРЕ (Надежнее всего для Хеджинга)
                pos_orders = mt5.history_orders_get(position=pos_id)
                if pos_orders:
                    # Сортируем ордера по времени, берем самый первый (вход)
                    first_order = sorted(pos_orders, key=lambda x: x.time_setup)[0]
                    entry_comment = first_order.comment if first_order.comment else ""

                # 2. Если в ордере пусто, ищем во входящей СДЕЛКЕ
                if not entry_comment:
                    pos_deals = mt5.history_deals_get(position=pos_id)
                    if pos_deals:
                        for pd in pos_deals:
                            if pd.entry == mt5.DEAL_ENTRY_IN:
                                entry_comment = pd.comment if pd.comment else ""
                                break

                # 3. Берем коммент из текущей сделки (Выхода)
                exit_comment = deal.comment if deal.comment else ""

                # 4. УМНАЯ СКЛЕЙКА (Regex)
                final_comment = entry_comment.strip()

                # Вырезаем только куски с [sl...] или [tp...] или просто sl/tp с цифрами
                match = re.search(r'(\[sl.*?\]|\[tp.*?\]|sl\s*[\d\.]+|tp\s*[\d\.]+)', exit_comment, re.IGNORECASE)

                if match:
                    exit_tag = match.group(1).strip()
                    # Добавляем тег, только если брокер еще не вклеил его в original_comment
                    if exit_tag.lower() not in final_comment.lower():
                        final_comment += f" {exit_tag}"
                elif exit_comment and exit_comment.lower() not in final_comment.lower():
                    # Если тега нет, но есть какой-то текст (напр. partial close)
                    final_comment += f" {exit_comment.strip()}"

                trade_payload = {
                    "username": SITE_USER,
                    "password": SITE_PASS,
                    "ticket": str(deal.ticket),
                    "symbol": deal.symbol,
                    "type": "BUY" if deal.type == mt5.DEAL_TYPE_SELL else "SELL",
                    "volume": deal.volume,
                    "entry_price": deal.price,
                    "profit": deal.profit,
                    "time": datetime.fromtimestamp(deal.time).strftime("%Y-%m-%d %H:%M:%S"),
                    "broker_offset": "10800",
                    "magic": str(magic_number),
                    "mt5_comment": final_comment.strip()  # 👈 ИДЕАЛЬНЫЙ КОММЕНТ
                }

                try:
                    res = requests.post(WEBHOOK_URL, json=trade_payload, timeout=10)

                    if res.status_code == 201:
                        print(f"✅ ДОБАВЛЕНА: #{deal.ticket} | Коммент: '{final_comment.strip()}'")
                        count += 1
                    elif res.status_code == 200:
                        pass  # Сделка уже есть
                    else:
                        print(f"❌ Ошибка #{deal.ticket}: {res.status_code} | {res.text}")
                        errors += 1
                except requests.exceptions.ReadTimeout:
                    print(f"⏳ Таймаут на #{deal.ticket}")
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