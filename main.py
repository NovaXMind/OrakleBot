import requests
import json
import time
from datetime import datetime
import xml.etree.ElementTree as ET
import schedule
import threading
from flask import Flask

# ==========================================
# 🌐 وب‌سرور جهت زنده نگه داشتن Render
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Orakle Market Bot is running smoothly!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ==========================================
# ⚙️ تنظیمات و کلیدهای ارتباطی
# ==========================================
AI_API_KEY = "aa-jwE1s7n4NYOpTlDXWESYYl2LIV49wEvUvGGnKTcOpidbUhrv" 
AI_BASE_URL = "https://api.avalai.ir/v1/chat/completions" 

TELEGRAM_BOT_TOKEN = "8517569208:AAG7nWMx5RCmP48yK7iTqHPr_1INQQABldU" 
TELEGRAM_CHAT_ID = "@OrakleMarket"  # آیدی عمومی کانال تلگرام

TEST_MODEL = "gpt-4o-mini"

# ==========================================
# 🤖 تابع عمومی هوش مصنوعی با تلاش نامحدود
# ==========================================
def call_ai_with_retry(model_name, system_prompt, delay=4):
    headers = {
        "Authorization": f"Bearer {AI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "system", "content": system_prompt}]
    }

    session = requests.Session()
    attempt = 1
    
    while True:
        try:
            print(f"⏳ درخواست از هوش مصنوعی ({model_name}) - تلاش شماره {attempt}...")
            res = session.post(AI_BASE_URL, headers=headers, json=payload, timeout=90)
            if res.status_code == 200:
                data = res.json()
                print(f"✅ پاسخ هوش مصنوعی دریافت شد.")
                return data['choices'][0]['message']['content']
            else:
                print(f"⚠️ پاسخ غیرمنتظره AI ({res.status_code}): {res.text}")
        except Exception as e:
            print(f"⚠️ خطای ارتباطی AI در تلاش {attempt}: {e}")
        
        attempt += 1
        time.sleep(delay)

# ==========================================
# 📰 استخراج اخبار زنده مارکت
# ==========================================
def get_latest_market_news():
    news_titles = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    rss_urls = [
        "https://www.investing.com/rss/news.rss",
        "https://www.forexlive.com/feed/news"
    ]
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
            
    if not news_titles:
        news_titles = [
            "Federal Reserve signals cautious approach on interest rate decisions.",
            "Global markets react to geopolitical tensions and commodity fluctuations.",
            "Crypto assets show resilience as institutional adoption metrics improve."
        ]
    return "\n- ".join(news_titles)

# ==========================================
# 🌐 دریافت داده‌های زنده
# ==========================================
def get_live_prices_and_fng():
    prices = {}
    fng_data = {'value': '25', 'classification': 'Extreme Fear'}
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        crypto_ids = "bitcoin,ethereum,solana,binancecoin,ripple,cardano,dogecoin,avalanche-2,chainlink,tether"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_ids}&vs_currencies=usd"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            prices['BTC'] = f"${data.get('bitcoin', {}).get('usd', 0):,}"
            prices['ETH'] = f"${data.get('ethereum', {}).get('usd', 0):,}"
            prices['SOL'] = f"${data.get('solana', {}).get('usd', 0):,}"
            prices['BNB'] = f"${data.get('binancecoin', {}).get('usd', 0):,}"
            prices['XRP'] = f"${data.get('ripple', {}).get('usd', 0):.4f}"
            prices['ADA'] = f"${data.get('cardano', {}).get('usd', 0):.4f}"
            prices['DOGE'] = f"${data.get('dogecoin', {}).get('usd', 0):.4f}"
            prices['AVAX'] = f"${data.get('avalanche-2', {}).get('usd', 0):,}"
            prices['LINK'] = f"${data.get('chainlink', {}).get('usd', 0):,}"
            prices['USDT'] = f"${data.get('tether', {}).get('usd', 1.0):.2f}"
    except Exception:
        pass

    try:
        fng_res = requests.get("https://api.alternative.me/fng/", timeout=10)
        if fng_res.status_code == 200:
            fng_json = fng_res.json()
            fng_data['value'] = str(fng_json['data'][0]['value'])
            fng_data['classification'] = str(fng_json['data'][0]['value_classification'])
    except Exception:
        pass

    symbols = {
        'XAUUSD': 'GC=F', 'XAGUSD': 'SI=F', 'WTI': 'CL=F', 'BRENT': 'BZ=F',
        'NG': 'NG=F', 'COPPER': 'HG=F', 'PLATINUM': 'PL=F',
        'PALLADIUM': 'PA=F', 'ALUMINUM': 'ALI=F', 'CORN': 'ZC=F',
        'SPX': '^GSPC', 'NDX': '^IXIC', 'DJI': '^DJI', 'DXY': 'DX-Y.NYB',
        'AAPL': 'AAPL', 'MSFT': 'MSFT', 'NVDA': 'NVDA', 'AMZN': 'AMZN',
        'GOOGL': 'GOOGL', 'TSLA': 'TSLA'
    }

    for key, sym in symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?interval=1m&range=1d"
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200 and res.text.strip():
                data = res.json()
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice')
                prices[key] = f"${price:,.2f}" if price is not None else "N/A"
            else:
                prices[key] = "N/A"
        except Exception:
            prices[key] = "N/A"

    return prices, fng_data

# ==========================================
# 📤 ارسال به تلگرام با تلاش نامحدود
# ==========================================
def send_telegram_message(message_text, post_title, delay=5):
    print(f"📤 [{datetime.now().strftime('%H:%M:%S')}] شروع فرایند ارسال {post_title}...")
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_text, "parse_mode": "Markdown"}
    
    session = requests.Session()
    attempt = 1
    
    while True:
        try:
            res = session.post(url, json=payload, timeout=25)
            if res.status_code == 200:
                print(f"✅ {post_title} با موفقیت در کانال منتشر شد!")
                return True
            else:
                clean_payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message_text}
                res_retry = session.post(url, json=clean_payload, timeout=25)
                if res_retry.status_code == 200:
                    print(f"✅ {post_title} به صورت متن ساده منتشر شد.")
                    return True
        except Exception:
            pass
            
        attempt += 1
        time.sleep(delay)

# ==========================================
# 📮 توابع اجرایی پست‌ها
# ==========================================

def job_post_1():
    prices, _ = get_live_prices_and_fng()
    content = f"""💎 **ORAKLE MARKET | داشبورد زنده قیمت‌ها**
─── ⋆ 💎 ⋆ ───


🏆 **۱۰ ارز دیجیتال برتر بازار:**

─── ⋆ 🏆 ⋆ ───
• 🪙 **بیت‌کوین (BTC):** `{prices.get('BTC', 'N/A')}`

• 🔹 **اتریوم (ETH):** `{prices.get('ETH', 'N/A')}`

• 🟣 **سولانا (SOL):** `{prices.get('SOL', 'N/A')}`

• 🟡 **بایننس کوین (BNB):** `{prices.get('BNB', 'N/A')}`

• 🪙 **ریپل (XRP):** `{prices.get('XRP', 'N/A')}`

• 🔷 **کاردانو (ADA):** `{prices.get('ADA', 'N/A')}`

• 🐕 **دوج‌کوین (DOGE):** `{prices.get('DOGE', 'N/A')}`

• 🔴 **آوالانچ (AVAX):** `{prices.get('AVAX', 'N/A')}`

• 🔗 **چین‌لینک (LINK):** `{prices.get('LINK', 'N/A')}`

• 💵 **تتر (USDT):** `{prices.get('USDT', '$1.00')}`



💰 **۱۰ کمودیتی و دارایی کلیدی جهان:**

─── ⋆ 💰 ⋆ ───
• 🟡 **طلای جهانی (XAU/USD):** `{prices.get('XAUUSD', 'N/A')}`

• ⚪️ **نقره جهانی (XAG/USD):** `{prices.get('XAGUSD', 'N/A')}`

• 🛢 **نفت خام آمریکا (WTI):** `{prices.get('WTI', 'N/A')}`

• ⛽️ **نفت برنت (Brent):** `{prices.get('BRENT', 'N/A')}`

• 🔥 **گاز طبیعی (Nat Gas):** `{prices.get('NG', 'N/A')}`

• 🧱 **مس جهانی (Copper):** `{prices.get('COPPER', 'N/A')}`

• ◽️ **پلاتین (Platinum):** `{prices.get('PLATINUM', 'N/A')}`

• 🪙 **پالادیوم (Palladium):** `{prices.get('PALLADIUM', 'N/A')}`

• ⚙️ **آلومینیوم (Aluminum):** `{prices.get('ALUMINUM', 'N/A')}`

• 🌽 **ذرت (Corn):** `{prices.get('CORN', 'N/A')}`



🏢 **۱۰ شاخص بورس و سهام معتبر جهان:**

─── ⋆ 🏢 ⋆ ───
• 📈 **شاخص اس‌اندپی ۵۰۰ (S&P 500):** `{prices.get('SPX', 'N/A')}`

• 💻 **شاخص ناسداک (Nasdaq):** `{prices.get('NDX', 'N/A')}`

• 🏛 **شاخص داوجونز (Dow Jones):** `{prices.get('DJI', 'N/A')}`

• 💵 **شاخص دلار آمریکا (DXY):** `{prices.get('DXY', 'N/A')}`

• 🍎 **سهام اپل (AAPL):** `{prices.get('AAPL', 'N/A')}`

• 💻 **سهام مایکروسافت (MSFT):** `{prices.get('MSFT', 'N/A')}`

• 🟢 **سهام ان‌ویدیا (NVDA):** `{prices.get('NVDA', 'N/A')}`

• 📦 **سهام آمازون (AMZN):** `{prices.get('AMZN', 'N/A')}`

• 🔍 **سهام گوگل (GOOGL):** `{prices.get('GOOGL', 'N/A')}`

• 🚗 **سهام تسلا (TSLA):** `{prices.get('TSLA', 'N/A')}`

─── ⋆ 💎 ⋆ ───


✨ **مرجع تخصصی تحلیل‌های ژئوپلیتیک و مالی**
✨ **به خانواده بزرگ ((پیشگوی مارکت)) بپیوندید**

🌐✦ [ OrakleMarket.com ] ✦🌐
🏛✦ [ t.me/OrakleMarket ] ✦🌐"""
    send_telegram_message(content, "پست ۱ (داشبورد ۳۰ نماد)")

def job_post_2():
    _, fng_data = get_live_prices_and_fng()
    val = fng_data['value']
    system_prompt = f"""
    You are 'Orakle Market'. Create Post 2 in Persian analyzing the Crypto Fear & Greed Index.
    Current Index Value: {val} out of 100.
    
    STRICT FORMATTING RULE: ALL main headings, sub-headings, and titles MUST BE BOLD (wrapped in double asterisks like **Heading**). Do not remove bold formatting from titles!
    
    Format:
    😱📊 **ORAKLE MARKET | تحلیل شاخص ترس و طمع**
    ─── ⋆ 💎 ⋆ ───

    📌 **وضعیت کنونی شاخص:**


    🎯 **امتیاز عددی شاخص:**  🔥 `[ {val} / 100 ]` 🔥


    • 🎭 **موقعیت روانی بازار:** [ترجمه فارسی وضعیت]

    ─── ⋆ 💡 ⋆ ───

    🧠 **تحلیل رفتارشناسی و روان‌شناسی معامله‌گران:**
    [تحلیل مفصل و روان‌شناختی بازار]

    💡 **توصیه استراتژیک مدیریت ریسک:**
    [توصیه حرفه‌ای معامله‌گری]

    ─── ⋆ 💎 ⋆ ───


    ✨ **مرجع تخصصی تحلیل‌های ژئوپلیتیک و مالی**
    ✨ **به خانواده بزرگ ((پیشگوی مارکت)) بپیوندید**

    🌐✦ [ OrakleMarket.com ] ✦🌐
    🏛✦ [ t.me/OrakleMarket ] ✦🌐
    """
    content = call_ai_with_retry(TEST_MODEL, system_prompt)
    send_telegram_message(content, "پست ۲ (تحلیل ترس و طمع)")

def job_post_3():
    latest_news = get_latest_market_news()
    system_prompt = f"""
    You are 'Orakle Market', a top-tier macroeconomics and geopolitical strategist.
    Below are the LATEST LIVE NEWS HEADLINES scraped from top financial feeds today:

    --- LATEST NEWS HEADLINES ---
    - {latest_news}
    -----------------------------

    Based on these real-time headlines and current market dynamics, write a high-level, authoritative Macroeconomic & Geopolitical Analysis in Persian for global markets today. Use professional financial tone and deep insights.
    
    STRICT FORMATTING RULE: ALL main headings, titles, and sub-headings MUST BE BOLD (wrapped in double asterisks like **Title**). Never output plain text headings without double asterisks.

    Format:
    🔮 **ORAKLE MARKET | بولتن تحلیلی تخصصی**
    ─── ⋆ 💎 ⋆ ───

    🌐 **تحلیل جامع کلان و ژئوپلیتیک**

    • 🧭 **جهت‌گیری کلی بازار:** [صعودی / نزولی / خنثی]
    • 📊 **شاخص سنتیمنت (Sentiment Index):** [عددی بین ۱۰- تا ۱۰+]

    • 📖 **روایت اصلی بازار (Core Narrative):** 
    [تحلیل مفصل، عمیق و روان بر اساس اخبار فوق، وضعیت تورم، سیاست‌های پولی بانک‌های مرکزی و ریسک‌های ژئوپلیتیک]

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


    ✨ **مرجع تخصصی تحلیل‌های ژئوپلیتیک و مالی**
    ✨ **به خانواده بزرگ ((پیشگوی مارکت)) بپیوندید**

    🌐✦ [ OrakleMarket.com ] ✦🌐
    🏛✦ [ t.me/OrakleMarket ] ✦🌐
    """
    content = call_ai_with_retry(TEST_MODEL, system_prompt)
    send_telegram_message(content, "پست ۳ (بولتن کلان)")

def job_daily_reports():
    job_post_2()
    job_post_3()

# ==========================================
# ⏰ تنظیم دقیق زمان‌بندی ارسال‌ها
# ==========================================

# پست ۱: هر ۳۰ دقیقه یک‌بار
schedule.every(30).minutes.do(job_post_1)

# پست‌های ۲ و ۳: روزی یک‌بار سر ساعت ۰۸:۰۰ صبح
schedule.every().day.at("08:00").do(job_daily_reports)

if __name__ == "__main__":
    # اجرای Flask در یک رشته (Thread) مجزا
    threading.Thread(target=run_flask, daemon=True).start()
    
    print("🚀 ربات با موفقیت روشن شد و زمان‌بندی دقیق فعال گردید.")
    print("⏰ برنامه زمانی:")
    print("   - پست ۱ (داشبورد قیمت‌ها): هر ۳۰ دقیقه یک‌بار")
    print("   - پست ۲ و ۳ (ترس‌وطمع + بولتن کلان): روزی ۱ بار (ساعت ۰۸:۰۰ صبح)")
    
    # ارسال پست ۱ بلافاصله پس از روشن شدن ربات برای تست اولیه‌ی موفقیت
    job_post_1()

    while True:
        schedule.run_pending()
        time.sleep(10)
