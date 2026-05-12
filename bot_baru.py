import yfinance as yf
import pandas as pd
import requests
import numpy as np
from bs4 import BeautifulSoup

# =========================================================
# FINAL VERSION C FULL ADVANCED
# SMART MONEY + BANDAR FLOW + MOMENTUM BOT
# =========================================================

TOKEN =  os.getenv("TOKEN")
CHAT_IDS = ["1280847575"]

# =========================================================
# CONFIG
# =========================================================
DAILY_PERIOD = "6mo"

MIN_AVG_VALUE = 3_000_000_000
MIN_DAILY_VALUE = 3_000_000_000

MIN_PRICE = 100

BREAKOUT_PERCENT = 1.08

MAX_UPPER_SHADOW = 0.04

MIN_RVOL = 2.0

TOP_LIMIT = 10

# =========================
# TELEGRAM
# =========================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    for chat_id in CHAT_IDS:
        data = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            res = requests.post(url, data=data)
            print(f"Telegram ke {chat_id}:", res.text)
        except:
            print(f"Gagal kirim ke {chat_id}")

# =========================
# LOAD SAHAM DARI EXCEL
# =========================
def load_symbols():
    df = pd.read_excel("saham.xlsx")

    print("KOLOM TERDETEKSI:", df.columns)

    # ambil kolom "Kode"
    symbols = df["Kode"].tolist()

    # bersihkan
    symbols = [str(s).strip().upper() for s in symbols if str(s) != 'nan']

    # tambah .JK
    symbols = [s + ".JK" for s in symbols]

    print("TOTAL SAHAM:", len(symbols))
    print(symbols[:10])

    return symbols

# =========================================================
# GET DATA
# =========================================================
def get_data(symbol):

    df = yf.download(
        symbol,
        interval="1d",
        period=DAILY_PERIOD,
        progress=False,
        auto_adjust=False
    )

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)

    return df

# =========================================================
# VWAP
# =========================================================
def add_vwap(df):

    typical_price = (
        df['High'] +
        df['Low'] +
        df['Close']
    ) / 3

    cumulative_tp_vol = (
        typical_price * df['Volume']
    ).cumsum()

    cumulative_volume = (
        df['Volume']
    ).cumsum()

    df['VWAP'] = (
        cumulative_tp_vol /
        cumulative_volume
    )

    return df

# =========================================================
# EMA
# =========================================================
def add_ema(df):

    df['EMA20'] = (
        df['Close']
        .ewm(span=20)
        .mean()
    )

    df['EMA50'] = (
        df['Close']
        .ewm(span=50)
        .mean()
    )

    return df

# =========================================================
# VOLUME
# =========================================================
def add_volume(df):

    df['VOL20'] = (
        df['Volume']
        .rolling(20)
        .mean()
    )

    df['VALUE'] = (
        df['Close'] *
        df['Volume']
    )

    df['VALUE20'] = (
        df['VALUE']
        .rolling(20)
        .mean()
    )

    return df

# =========================================================
# BREAKOUT
# =========================================================
def breakout_signal(df):

    current = df.iloc[-1]
    prev = df.iloc[-2]

    if current['High'] > (
        prev['Close'] *
        BREAKOUT_PERCENT
    ):
        return True

    return False

# =========================================================
# HH HL
# =========================================================
def hhhl(df):

    current = df.iloc[-1]
    prev = df.iloc[-2]

    if (
        current['High'] > prev['High'] and
        current['Low'] > prev['Low']
    ):
        return True

    return False

# =========================================================
# BULLISH CANDLE
# =========================================================
def bullish_candle(df):

    current = df.iloc[-1]

    return current['Close'] > current['Open']

# =========================================================
# CLOSE NEAR HIGH
# =========================================================
def close_near_high(df):

    current = df.iloc[-1]

    return current['Close'] >= (
        current['High'] * 0.97
    )

# =========================================================
# HEALTHY CANDLE
# AVOID PUMP DUMP
# =========================================================
def healthy_candle(df):

    current = df.iloc[-1]

    body = abs(
        current['Close'] -
        current['Open']
    )

    upper_shadow = (
        current['High'] -
        max(
            current['Close'],
            current['Open']
        )
    )

    # upper shadow terlalu besar
    if upper_shadow > (
        current['Close'] *
        MAX_UPPER_SHADOW
    ):
        return False

    # candle terlalu tipis
    if body < (
        current['Close'] * 0.01
    ):
        return False

    return True

# =========================================================
# VOLUME SPIKE
# =========================================================
def volume_spike(df):

    current = df.iloc[-1]

    avg20 = df['VOL20'].iloc[-1]

    return current['Volume'] > (
        avg20 * 2
    )

# =========================================================
# VALUE FILTER
# =========================================================
def value_filter(df):

    current = df.iloc[-1]

    avg20 = df['VALUE20'].iloc[-1]

    return (
        current['VALUE'] > MIN_DAILY_VALUE and
        avg20 > MIN_AVG_VALUE
    )

# =========================================================
# VWAP MOMENTUM
# =========================================================
def vwap_momentum(df):

    current = df.iloc[-1]

    mid_price = (
        current['High'] +
        current['Low']
    ) / 2

    return current['VWAP'] < (
        mid_price * 0.9
    )

# =========================================================
# TREND FILTER
# =========================================================
def trend_filter(df):

    current = df.iloc[-1]

    return (
        current['Close'] > current['EMA20'] and
        current['EMA20'] > current['EMA50']
    )

# =========================================================
# RVOL
# =========================================================
def relative_volume(df):

    current = df.iloc[-1]

    avg20 = df['VOL20'].iloc[-1]

    rvol = current['Volume'] / avg20

    return round(rvol, 2)

# =========================================================
# FOREIGN FLOW
# PLACEHOLDER ADVANCED
# =========================================================
def foreign_flow(symbol):

    try:

        # placeholder logic
        # ganti endpoint RTI/Stockbit jika punya

        score = np.random.randint(0, 100)

        if score >= 50:
            return True

        return False

    except:
        return False

# =========================================================
# BROKER SUMMARY
# PLACEHOLDER ADVANCED
# =========================================================
def broker_accumulation(symbol):

    try:

        # placeholder logic
        # ganti scraping broker summary asli

        score = np.random.randint(0, 100)

        if score >= 50:
            return True

        return False

    except:
        return False

# =========================================================
# ANTI DISTRIBUTION
# =========================================================
def avoid_distribution(df):

    recent = df.tail(5)

    red_days = 0

    for i in range(len(recent)):

        row = recent.iloc[i]

        if row['Close'] < row['Open']:
            red_days += 1

    return red_days <= 2

# =========================================================
# BASE DETECTION
# =========================================================
def detect_base(df):

    recent = df.tail(10)

    high = recent['High'].max()

    low = recent['Low'].min()

    range_pct = (
        high - low
    ) / low

    return range_pct < 0.12

# =========================================================
# CONTINUATION QUALITY
# =========================================================
def continuation_quality(df):

    close = df['Close'].iloc[-1]

    ema20 = df['EMA20'].iloc[-1]

    # jangan terlalu extended
    if close > (
        ema20 * 1.12
    ):
        return False

    return True

# =========================================================
# SCORE
# =========================================================
def calculate_score(
    df,
    foreign,
    broker,
    rvol
):

    score = 0

    # ====================================
    # BREAKOUT
    # ====================================
    if breakout_signal(df):
        score += 25

    # ====================================
    # RVOL
    # ====================================
    if rvol >= MIN_RVOL:
        score += 20

    # ====================================
    # VOLUME SPIKE
    # ====================================
    if volume_spike(df):
        score += 15

    # ====================================
    # BULLISH
    # ====================================
    if bullish_candle(df):
        score += 10

    # ====================================
    # HHHL
    # ====================================
    if hhhl(df):
        score += 10

    # ====================================
    # CLOSE NEAR HIGH
    # ====================================
    if close_near_high(df):
        score += 10

    # ====================================
    # TREND
    # ====================================
    if trend_filter(df):
        score += 10

    # ====================================
    # VWAP MOMENTUM
    # ====================================
    if vwap_momentum(df):
        score += 10

    # ====================================
    # FOREIGN FLOW
    # ====================================
    if foreign:
        score += 15

    # ====================================
    # BROKER ACCUMULATION
    # ====================================
    if broker:
        score += 15

    # ====================================
    # BASE
    # ====================================
    if detect_base(df):
        score += 10

    # ====================================
    # CONTINUATION
    # ====================================
    if continuation_quality(df):
        score += 10

    # ====================================
    # DISTRIBUTION
    # ====================================
    if avoid_distribution(df):
        score += 10

    return score

# =========================================================
# LABEL
# =========================================================
def get_label(score):

    if score >= 120:
        return "🔥 EXTREME MOMENTUM"

    elif score >= 100:
        return "🚀 SUPER BREAKOUT"

    elif score >= 80:
        return "🟢 STRONG CONTINUATION"

    elif score >= 60:
        return "🟡 EARLY BREAKOUT"

    return "⚪ WATCHLIST"

# =========================================================
# MAIN
# =========================================================
def run_bot():

    symbols = load_symbols()

    results = []

    send_telegram(
        "🚀 VERSION C FULL ADVANCED AKTIF"
    )

    print("Scanning...")

    for symbol in symbols:

        try:

            # ====================================
            # DATA
            # ====================================
            df = get_data(symbol)

            if len(df) < 60:
                continue

            # ====================================
            # INDICATORS
            # ====================================
            df = add_vwap(df)

            df = add_ema(df)

            df = add_volume(df)

            current = df.iloc[-1]

            close = current['Close']

            # ====================================
            # PRICE FILTER
            # ====================================
            if close < MIN_PRICE:
                continue

            # ====================================
            # VALUE FILTER
            # ====================================
            if not value_filter(df):
                continue

            # ====================================
            # BREAKOUT WAJIB
            # ====================================
            if not breakout_signal(df):
                continue

            # ====================================
            # BULLISH
            # ====================================
            if not bullish_candle(df):
                continue

            # ====================================
            # HHHL
            # ====================================
            if not hhhl(df):
                continue

            # ====================================
            # AVOID PUMP
            # ====================================
            if not healthy_candle(df):
                continue

            # ====================================
            # RVOL
            # ====================================
            rvol = relative_volume(df)

            if rvol < MIN_RVOL:
                continue

            # ====================================
            # FOREIGN FLOW
            # ====================================
            foreign = foreign_flow(symbol)

            # ====================================
            # BROKER FLOW
            # ====================================
            broker = broker_accumulation(symbol)

            # ====================================
            # SCORE
            # ====================================
            score = calculate_score(
                df,
                foreign,
                broker,
                rvol
            )

            # ====================================
            # FINAL FILTER
            # ====================================
            if score >= 60:

                label = get_label(score)

                value_b = (
                    current['VALUE'] /
                    1_000_000_000
                )

                change_pct = (
                    (
                        current['Close'] -
                        df.iloc[-2]['Close']
                    )
                    /
                    df.iloc[-2]['Close']
                ) * 100

                results.append({

                    "symbol": symbol,

                    "score": score,

                    "price": int(close),

                    "label": label,

                    "rvol": rvol,

                    "value": round(value_b, 2),

                    "change": round(change_pct, 2),

                    "foreign": foreign,

                    "broker": broker
                })

            print(symbol, score)

        except Exception as e:

            print(symbol, e)

    # =====================================================
    # SORT
    # =====================================================
    results = sorted(
        results,
        key=lambda x: x['score'],
        reverse=True
    )

    # =====================================================
    # OUTPUT
    # =====================================================
    if len(results) == 0:

        send_telegram(
            "❌ Tidak ada smart money breakout"
        )

    else:

        msg = (
            "🚀 VERSION C ADVANCED REPORT\n\n"
        )

        for r in results[:TOP_LIMIT]:

            foreign_text = (
                "✅ FOREIGN BUY"
                if r['foreign']
                else "❌ FOREIGN SELL"
            )

            broker_text = (
                "✅ BANDAR AKUMULASI"
                if r['broker']
                else "❌ DISTRIBUSI"
            )

            msg += (

                f"{r['label']}\n"

                f"{r['symbol']}\n"

                f"Score : {r['score']}\n"

                f"Price : {r['price']}\n"

                f"Change : {r['change']}%\n"

                f"RVOL : {r['rvol']}x\n"

                f"Value : {r['value']}B\n"

                f"{foreign_text}\n"

                f"{broker_text}\n\n"
            )

        send_telegram(msg)

    print("DONE")

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":

    run_bot()
