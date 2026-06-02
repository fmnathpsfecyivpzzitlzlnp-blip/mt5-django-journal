import yfinance as yf
import pandas as pd
import torch
import warnings
warnings.filterwarnings('ignore') # Отключаем лишний спам в консоли

from model import Kronos, KronosTokenizer, KronosPredictor

print("1. Скачиваем свежие котировки Золота (XAUUSD)...")
gold_data = yf.download(tickers="GC=F", interval="5m", period="5d", progress=False)

# 👇 ИСПРАВЛЕНИЕ: Убираем двойные заголовки (MultiIndex) из нового yfinance
if isinstance(gold_data.columns, pd.MultiIndex):
    gold_data.columns = gold_data.columns.get_level_values(0)

df = gold_data.reset_index()

# В зависимости от версии yfinance, колонка времени может называться Date или Datetime
if 'Date' in df.columns:
    df.rename(columns={'Date': 'timestamps'}, inplace=True)
if 'Datetime' in df.columns:
    df.rename(columns={'Datetime': 'timestamps'}, inplace=True)

df.rename(columns={'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'}, inplace=True)
df['timestamps'] = pd.to_datetime(df['timestamps']).dt.tz_localize(None)

lookback = 400
pred_len = 12 # Прогноз на 12 свечей вперед (1 час)

# Берем последние 400 свечей для анализа
x_df = df.iloc[-lookback:][['open', 'high', 'low', 'close', 'volume']].reset_index(drop=True)

# Принудительно делаем тип данных float, чтобы Питон не ругался на математику
for col in ['open', 'high', 'low', 'close', 'volume']:
    x_df[col] = x_df[col].astype(float)

x_timestamp = df.iloc[-lookback:]['timestamps'].reset_index(drop=True)

# Генерируем время для будущих свечей
last_time = x_timestamp.iloc[-1]
y_timestamp = pd.Series([last_time + pd.Timedelta(minutes=5 * i) for i in range(1, pred_len + 1)])

print("2. Загружаем ИИ-ядро Kronos...")
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Используем устройство: {device.upper()}")

tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
model = Kronos.from_pretrained("NeoQuasar/Kronos-small").to(device)
predictor = KronosPredictor(model, tokenizer, max_context=512)

print("3. ИИ думает... Генерируем прогноз!")
pred_df = predictor.predict(
    df=x_df,
    x_timestamp=x_timestamp,
    y_timestamp=y_timestamp,
    pred_len=pred_len,
    T=1.0,
    top_p=0.9,
    sample_count=1
)

print("\n=== ГОТОВО! ПРОГНОЗ KRONOS НА БЛИЖАЙШИЙ ЧАС ===")
print(pred_df[['open', 'high', 'low', 'close']])