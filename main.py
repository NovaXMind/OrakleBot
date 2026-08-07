import requests
import json
import time
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
import schedule
import threading
import os
from flask import Flask

# ==========================================
# 🌐 وب‌سرور جهت زنده نگه داشتن Render
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Orakle Systems are running smoothly!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ==========================================
# 📅 تابع محاسبه تاریخ شمسی و میلادی
# ==========================================
def get_formatted_dates():
    iran_tz = timezone(timedelta(hours=3, minutes=30))
    now = datetime.now(iran_tz)
    
    gregorian_months = [
        "ژانویه", "فوریه", "مارس", "آوریل", "می", "ژوئن",
        "ژوئیه", "آگوست", "سپتامبر", "اکتبر", "نوامبر", "دسامبر"
    ]
    
    jalali_months = [
        "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"
    ]
    
    g_day = now.day
    g_month = gregorian_months[now.month - 1]
    g_year = now.year
    gregorian_str = f"📆 تقویم میلادی | {g_day} {g_month} {g_year}"
    
    gy = now.year
    gm = now.month
    gd = now.day
    
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy2 = 1 if (gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0)) else 0
        
    if gm > 2:
        jy = gy - 621
        d = g_d_m[gm - 1] + gd + gy2
    else:
        jy = gy - 622
        d = g_d_m[gm - 1] + gd

    if d <= 79:
        d += 11 if (gy % 4 == 1) else 10
        if d <= 186:
            jm = (d // 31) + 1
            jd = (d % 31)
            if jd == 0: jm -= 1; jd = 31
        else:
            d -= 186
            jm = (d // 30) + 7
            jd = (d % 30)
            if jd == 0: jm -= 1; jd = 30
    else:
        d -= 79
        if d <= 186:
            jm = (d // 31) + 1
            jd = (d % 31)
            if jd == 0: jm -= 1; jd = 31
        else:
            d -= 186
            jm = (d // 30) + 7
            jd = (d % 30)
            if jd == 0: jm -= 1; jd = 30
                
    j_month = jalali_months[jm - 1]
    jalali_str = f"📅 تقویم شمسی | {jd} {j_month} {jy}"
    
    return f"{jalali_str}\n{gregorian_str}"

# ==========================================
# ⚙️ تنظیمات و آیدی کانال‌ها
# ==========================================
AI_API_KEY = "aa-jwE1s7n4NYOpTlDXWESYYl2LIV49wEvUvGGnKTcOpidbUhrv" 
AI_BASE_URL = "https://api.avalai.ir/v1/chat/completions" 

TELEGRAM_BOT_TOKEN = "8517569208:AAG7nWMx5RCmP48yK7iTqHPr_1INQQABldU" 

MAIN_CHANNEL_ID = "@OrakleMarket"  # کانال تحلیل‌ها
LIVE_CHANNEL_ID = "@OrakleLive"    # کانال داشبورد قیمت‌ها

TEST_MODEL = "gpt-4o-mini"

# ==========================================
# 🤖 تابع هوش مصنوعی
# ==========================================
def call_ai_with_retry(model_name, system_prompt, delay=4):
    headers = {"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"}
    payload = {"model": model_name, "messages": [{"role": "system", "content": system_prompt}]}
    session = requests.Session()
    attempt = 1
    while True:
        try:
            res = session.post(AI_BASE_URL, headers=headers, json=payload, timeout=90)
            if res.status_code == 200:
                return res.json()['choices'][0]['message']['content']
        except Exception:
            pass
        attempt += 1
        time.sleep(delay)

# ==========================================
# 📰 دریافت اخبار
# ==========================================
def get_latest_market_news():
    news_titles = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    rss_urls = ["https://www.investing.com/rss/news.rss", "https://www.forexlive.com/feed/news"]
    for url in rss_urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                root = ET.fromstring(res.content)
                for item in root.findall('.//item')[:5]:
                    title = item.find('title')
                    if title is not None and title.text:
                        news_titles.append(title.text.strip())
        except Exception:
            pass
    return "\n- ".join(news_titles) if news_titles else "Market operating with standard liquidity."

# ==========================================
# 🌐 دریافت داده‌های ۵۰ دارایی برتر
# ==========================================
def get_live_prices_and_fng():
    prices = {}
    fng_data = {'value': '50', 'classification': 'Neutral'}
    headers = {'User-Agent': 'Mozilla/5.0'}

    # ۲۰ کریپتوکارنسی برتر
    crypto_map = {
        'BTC': 'BTCUSDT', 'ETH': 'ETHUSDT', 'SOL': 'SOLUSDT', 'BNB': 'BNBUSDT',
        'XRP': 'XRPUSDT', 'ADA': 'ADAUSDT', 'DOGE': 'DOGEUSDT', 'AVAX': 'AVAXUSDT',
        'LINK': 'LINKUSDT', 'TON': 'TONUSDT', 'DOT': 'DOTUSDT', 'SHIB': 'SHIBUSDT',
        'NEAR': 'NEARUSDT', 'SUI': 'SUIUSDT', 'LTC': 'LTCUSDT', 'PEPE': 'PEPEUSDT',
        'UNI': 'UNIUSDT', 'APT': 'APTUSDT', 'MATIC': 'POLUSDT', 'USDT': 'USDT'
    }
    prices['USDT'] = "$1.00"

    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price", headers=headers, timeout=5)
        if res.status_code == 200:
            data = {item['symbol']: float(item['price']) for item in res.json()}
            for key, bn_sym in crypto_map.items():
                if bn_sym in data:
                    val = data[bn_sym]
                    if key in ['SHIB', 'PEPE']:
                        prices[key] = f"${val:.6f}"
                    elif key in ['XRP', 'ADA', 'DOGE']:
                        prices[key] = f"${val:.4f}"
                    else:
                        prices[key] = f"${val:,.2f}"
    except Exception:
        pass

    for k in crypto_map.keys():
        if k not in prices: prices[k] = "N/A"

    try:
        fng_res = requests.get("https://api.alternative.me/fng/", timeout=5)
        if fng_res.status_code == 200:
            fng_data['value'] = str(fng_res.json()['data'][0]['value'])
    except Exception:
        pass

    # ۱۵ کمودیتی و دارایی کلیدی
    # ۱۵ شاخص بورس و سهام برتر
    symbols = {
        'XAUUSD': 'GC=F', 'XAGUSD': 'SI=F', 'WTI': 'CL=F', 'BRENT': 'BZ=F',
        'NG': 'NG=F', 'COPPER': 'HG=F', 'PLATINUM': 'PL=F', 'PALLADIUM': 'PA=F',
        'ALUMINUM': 'ALI=F', 'CORN': 'ZC=F', 'WHEAT': 'ZW=F', 'SOYBEAN': 'ZS=F',
        'COFFEE': 'KC=F', 'SUGAR': 'SB=F', 'COTTON': 'CT=F',
        'SPX': '^GSPC', 'NDX': '^IXIC', 'DJI': '^DJI', 'DXY': 'DX-Y.NYB',
        'VIX': '^VIX', 'AAPL': 'AAPL', 'MSFT': 'MSFT', 'NVDA': 'NVDA',
        'AMZN': 'AMZN', 'GOOGL': 'GOOGL', 'TSLA': 'TSLA', 'META': 'META',
        'NFLX': 'NFLX', 'AMD': 'AMD', 'INTC': 'INTC'
    }

    session = requests.Session()
    session.headers.update(headers)
    for key, sym in symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1d&range=1d"
            res = session.get(url, timeout=4)
            if res.status_code == 200:
                result = res.json().get('chart', {}).get('result')
                if result:
                    price = result[0]['meta'].get('regularMarketPrice')
                    prices[key] = f"${price:,.2f}" if price is not None else "N/A"
                else: prices[key] = "N/A"
            else: prices[key] = "N/A"
        except Exception:
            prices[key] = "N/A"

    return prices, fng_data

# ==========================================
# 📤 ارسال پیام به تلگرام
# ==========================================
def send_telegram_message(target_chat_id, message_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": target_chat_id, "text": message_text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code != 200:
            requests.post(url, json={"chat_id": target_chat_id, "text": message_text}, timeout=15)
    except Exception:
        pass

# ==========================================
# 📥 شنود پیام‌های ربات (خوش‌آمدگویی و هدایت)
# ==========================================
def telegram_listener():
    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    while True:
        try:
            res = requests.get(url, params={"offset": offset, "timeout": 30}, timeout=35)
            if res.status_code == 200:
                data = res.json()
                for result in data.get("result", []):
                    offset = result["update_id"] + 1
                    message = result.get("message", {})
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    
                    if chat_id and text == "/start":
                        welcome_msg = """💎 **به مجموعه هوشمند ORAKLE MARKET خوش آمدید**

─── ⋆ 💎 ⋆ ───

به عنوان معامله‌گر و سرمایه‌گذار در بازارهای بین‌المللی، می‌توانید از خدمات تخصصی و مجزای مجموعه ما استفاده کنید:

📊 **۱. کانال تحلیل‌های اختصاصی و ژئوپلیتیک:**
جهت دسترسی به بولتن‌های تحلیلی کلان، بررسی‌های بنیادی، روان‌شناسی بازار و شاخص ترس و طمع:
🏛✦  t.me/OrakleMarket  ✦🏛

⚡️ **۲. کانال زنده قیمت‌ها (Orakle Live):**
جهت دریافت لحظه‌ای و ۳ ساعته نرخ ۵۰ دارایی برتر جهان (کریپتو، کمودیتی و سهام):
⚡️✦  t.me/OrakleLive  ✦⚡️

🌐 **پرتال رسمی مجموعه:**
🌐✦  OrakleMarket.com  ✦🌐

─── ⋆ 💎 ⋆ ───
✨ **با ما یک گام از مارکت جلوتر باشید**"""
                        send_telegram_message(chat_id, welcome_msg)
        except Exception:
            pass
        time.sleep(2)

# ==========================================
# 📮 تولید متن ۵۰ دارایی برای کانال قیمت
# ==========================================
def generate_price_dashboard_text():
    date_header = get_formatted_dates()
    p, _ = get_live_prices_and_fng()
    return f"""⚡️ **ORAKLE LIVE | داشبورد زنده قیمت‌ها**
─── ⋆ ⚡️ ⋆ ───

{date_header}

🏆 **۲۰ ارز دیجیتال برتر بازار:**
• 🪙 **بیت‌کوین (BTC):** `{p.get('BTC')}` | 🔹 **اتریوم (ETH):** `{p.get('ETH')}`
• 🟣 **سولانا (SOL):** `{p.get('SOL')}` | 🟡 **بایننس کوین (BNB):** `{p.get('BNB')}`
• 🪙 **ریپل (XRP):** `{p.get('XRP')}` | 💎 **تون‌کوین (TON):** `{p.get('TON')}`
• 🔷 **کاردانو (ADA):** `{p.get('ADA')}` | 🐕 **دوج‌کوین (DOGE):** `{p.get('DOGE')}`
• 🔴 **آوالانچ (AVAX):** `{p.get('AVAX')}` | 🔗 **چین‌لینک (LINK):** `{p.get('LINK')}`
• 🔴 **پولکادات (DOT):** `{p.get('DOT')}` | 🐕 **شیبا (SHIB):** `{p.get('SHIB')}`
• 🟢 **نیر (NEAR):** `{p.get('NEAR')}` | 💧 **سویی (SUI):** `{p.get('SUI')}`
• 🪙 **لایت‌کوین (LTC):** `{p.get('LTC')}` | 🐸 **پپه (PEPE):** `{p.get('PEPE')}`
• 🦄 **یونی‌سواپ (UNI):** `{p.get('UNI')}` | 🧬 **آپتوس (APT):** `{p.get('APT')}`
• 🟣 **پولیگان (POL):** `{p.get('MATIC')}` | 💵 **تتر (USDT):** `{p.get('USDT')}`

💰 **۱۵ کمودیتی و دارایی کلیدی:**
• 🟡 **طلا (XAU):** `{p.get('XAUUSD')}` | ⚪️ **نقره (XAG):** `{p.get('XAGUSD')}`
• 🛢 **نفت WTI:** `{p.get('WTI')}` | ⛽️ **نفت برنت:** `{p.get('BRENT')}`
• 🔥 **گاز طبیعی:** `{p.get('NG')}` | 🧱 **مس:** `{p.get('COPPER')}`
• ◽️ **پلاتین:** `{p.get('PLATINUM')}` | 🪙 **پالادیوم:** `{p.get('PALLADIUM')}`
• ⚙️ **آلومینیوم:** `{p.get('ALUMINUM')}` | 🌽 **ذرت:** `{p.get('CORN')}`
• 🌾 **گندم:** `{p.get('WHEAT')}` | 🫘 **سویا:** `{p.get('SOYBEAN')}`
• ☕️ **قهوه:** `{p.get('COFFEE')}` | 🍬 **شکر:** `{p.get('SUGAR')}`
• 🧵 **پنبه:** `{p.get('COTTON')}`

🏢 **۱۵ شاخص بورس و سهام برتر:**
• 📈 **اس‌اندپی (S&P 500):** `{p.get('SPX')}` | 💻 **ناسداک:** `{p.get('NDX')}`
• 🏛 **داوجونز:** `{p.get('DJI')}` | 💵 **شاخص دلار (DXY):** `{p.get('DXY')}`
• 📊 **شاخص نوسان (VIX):** `{p.get('VIX')}` | 🍎 **اپل:** `{p.get('AAPL')}`
• 💻 **مایکروسافت:** `{p.get('MSFT')}` | 🟢 **ان‌ویدیا:** `{p.get('NVDA')}`
• 📦 **آمازون:** `{p.get('AMZN')}` | 🔍 **گوگل:** `{p.get('GOOGL')}`
• 🚗 **تسلا:** `{p.get('TSLA')}` | ♾ **متا:** `{p.get('META')}`
• 🎬 **نتفلیکس:** `{p.get('NFLX')}` | 🔴 **ای‌ام‌دی (AMD):** `{p.get('AMD')}`
• 🟦 **اینتل (INTC):** `{p.get('INTC')}`

─── ⋆ ⚡️ ⋆ ───
🌐✦  OrakleMarket.com  ✦🌐
⚡️✦  t.me/OrakleLive  ✦⚡️"""

# ==========================================
# 📮 توابع پست‌های کانال اصلی
# ==========================================
def job_post_2():
    date_header = get_formatted_dates()
    _, fng_data = get_live_prices_and_fng()
    val = fng_data['value']
    system_prompt = f"""
    You are 'Orakle Market'. Create Post 2 in Persian analyzing the Crypto Fear & Greed Index.
    Current Index Value: {val} out of 100.
    
    STRICT FORMATTING RULE: ALL main headings and titles MUST BE BOLD (wrapped in double asterisks).

    Format:
    😱📊 **ORAKLE MARKET | تحلیل شاخص ترس و طمع**
    ─── ⋆ 💎 ⋆ ───

    {date_header}

    ─── ⋆ 📌 ⋆ ───
    📌 **وضعیت کنونی شاخص:**
    🎯 **امتیاز عددی شاخص:**  🔥 `[ {val} / 100 ]` 🔥
    • 🎭 **موقعیت روانی بازار:** [ترجمه فارسی وضعیت]

    ─── ⋆ 💡 ⋆ ───
    🧠 **تحلیل رفتارشناسی و روان‌شناسی معامله‌گران:**
    [تحلیل مفصل و روان‌شناختی بازار]

    💡 **توصیه استراتژیک مدیریت ریسک:**
    [توصیه حرفه‌ای معامله‌گری]

    ─── ⋆ 💎 ⋆ ───
    🌐✦  OrakleMarket.com  ✦🌐
    🏛✦  t.me/OrakleMarket  ✦🌐
    """
    content = call_ai_with_retry(TEST_MODEL, system_prompt)
    send_telegram_message(MAIN_CHANNEL_ID, content)

def job_post_3():
    date_header = get_formatted_dates()
    latest_news = get_latest_market_news()
    system_prompt = f"""
    You are 'Orakle Market', a top-tier macroeconomics and geopolitical strategist.
    News Today: {latest_news}

    Write a high-level Macroeconomic & Geopolitical Analysis in Persian for global markets today.
    STRICT FORMATTING RULE: ALL main headings and titles MUST BE BOLD.

    Format:
    🔮 **ORAKLE MARKET | بولتن تحلیلی تخصصی**
    ─── ⋆ 💎 ⋆ ───

    {date_header}

    ─── ⋆ 🌐 ⋆ ───
    🌐 **تحلیل جامع کلان و ژئوپلیتیک**
    • 🧭 **جهت‌گیری کلی بازار:** [صعودی / نزولی / خنثی]
    • 📊 **شاخص سنتیمنت (Sentiment Index):** [عددی بین ۱۰- تا ۱۰+]

    • 📖 **روایت اصلی بازار (Core Narrative):** 
    [تحلیل مفصل، عمیق و روان بر اساس اخبار، تورم، نرخ بهره و ریسک‌های ژئوپلیتیک]

    ─── ⋆ 📊 ⋆ ───
    📊 **ارزیابی تفکیکی و تخصصی بازارهای جهانی**
    • 💵 **شاخص دلار و جفت‌ارزهای فارکس (DXY & Forex):** [تحلیل]
    • 🟡 **انس جهانی طلا و فلزات (Gold & Commodities):** [تحلیل]
    • 🪙 **بازار کریپتوکارنسی (Crypto Market):** [تحلیل]

    ─── ⋆ 🎯 ⋆ ───
    🎯 **سناریوهای محتمل معامله‌گری**
    • 🟢 **سناریوی اصلی:** [توضیح]
    • 🔴 **سناریوی جایگزین:** [توضیح]

    ─── ⋆ 📌 ⋆ ───
    📌 **خلاصه و جمع‌بندی تحلیلی (Quick Summary):**
    [۳ بند کوتاه]

    ─── ⋆ 💎 ⋆ ───
    🌐✦  OrakleMarket.com  ✦🌐
    🏛✦  t.me/OrakleMarket  ✦🌐
    """
    content = call_ai_with_retry(TEST_MODEL, system_prompt)
    send_telegram_message(MAIN_CHANNEL_ID, content)

def send_price_to_live_channel():
    """ارسال داشبورد قیمت‌ها به کانال OrakleLive هر ۳ ساعت"""
    price_text = generate_price_dashboard_text()
    print(f"📢 [{datetime.now().strftime('%H:%M:%S')}] ارسال ۵۰ قیمت به کانال @OrakleLive...")
    send_telegram_message(LIVE_CHANNEL_ID, price_text)

# ==========================================
# ⏰ تنظیم زمان‌بندی
# ==========================================

# ۱. ارسال ۵۰ قیمت زنده به کانال OrakleLive (هر ۳ ساعت یک‌بار)
schedule.every(3).hours.do(send_price_to_live_channel)

# ۲. ارسال تحلیل‌های متنی AI به کانال اصلی OrakleMarket (روزی یک‌بار)
schedule.every().day.at("09:00").do(job_post_2)
schedule.every().day.at("09:05").do(job_post_3)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    threading.Thread(target=telegram_listener, daemon=True).start()
    
    print("🚀 سیستم‌های Orakle Market با موفقیت راه اندازی شدند.")
    print("📌 کانال اصلی (@OrakleMarket): مخصوص تحلیل‌های هوش مصنوعی (ساعت ۰۹:۰۰)")
    print("⚡️ کانال قیمت (@OrakleLive): مخصوص ۵0 قیمت زنده (هر ۳ ساعت)")
    
    # تست اولیه در زمان استارت
    send_price_to_live_channel()

    while True:
        schedule.run_pending()
        time.sleep(10)
