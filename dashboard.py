import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import yfinance as yf
import json
from thefuzz import process  # دي المكتبة الجديدة

# ---------------------------------------------------------
# إعدادات الصفحة
# ---------------------------------------------------------
st.set_page_config(page_title="LAVa", page_icon="😘", layout="wide")
# بدل ما نكتب المفتاح في الكود، بنقوله هاته من الخزنة السرية للسيرفر
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    # السطر ده عشان لو شغال على جهازك وما لقلش المفتاح
    st.warning("مطلوب مفتاح API للعمل")
    st.stop()

# ---------------------------------------------------------
# 1. قاعدة بيانات الأسهم (دليل التليفونات) 📒
# ---------------------------------------------------------
# ضيف هنا أي سهم انت عاوزه عشان يتعرف عليه بسرعة ودقة
STOCK_DB = {
    # مصر
    "البنك التجاري الدولي cib": "COMI.CA",
    "فوري fawry": "FWRY.CA",
    "حديد عز ezz steel": "ESRS.CA",
    "مجموعة طلعت مصطفى tmg": "TMGH.CA",
    "السويدي إليكتريك elsewedy": "SWDY.CA",
    "إي فاينانس e-finance": "EFIH.CA",
    "بلتون المالية beltone": "BTLL.CA",
    "بالم هيلز palm hills": "PHDC.CA",
    "هيرميس efg hermes": "HRHO.CA",
    "موبكو mopco": "MFPC.CA",
    "أبو قير للأسمدة": "ABUK.CA",
    "سيدي كرير للبتروكيماويات sidpec": "SKPC.CA",

    # السعودية
    "أرامكو aramco": "2222.SR",
    "مصرف الراجحي al rajhi": "1120.SR",
    "سابك sabic": "2010.SR",
    "الأهلي السعودي snb": "1180.SR",
    "الكهرباء السعودية": "5110.SR",

    # أمريكا
    "apple أبل": "AAPL",
    "tesla تسلا": "TSLA",
    "nvidia إنفيديا": "NVDA",
    "google جوجل": "GOOGL"
}


# ---------------------------------------------------------
# 2. وظيفة البحث الذكي (Fuzzy Search) 🕵️‍♂️
# ---------------------------------------------------------
def find_ticker_smart(user_text):
    """
    بيدور في القاموس بتاعنا على أقرب كلمة للي المستخدم كتبه
    """
    # بنستخدم process.extractOne عشان نجيب "أقرب" اسم في القائمة
    # score_cutoff=60: يعني لازم نسبة الشبه تكون فوق 60% عشان نقبله
    best_match = process.extractOne(user_text, list(STOCK_DB.keys()), score_cutoff=50)

    if best_match:
        matched_name = best_match[0]
        ticker = STOCK_DB[matched_name]
        return ticker, matched_name
    else:
        return None, None


# ---------------------------------------------------------
# 3. العقل المدبر (Router)
# ---------------------------------------------------------
def smart_router(user_input):
    client = Groq(api_key=API_KEY)

    # 1. البحث في القاموس أولاً (Database Check)
    ticker, name = find_ticker_smart(user_input)

    # لو ملقيناهوش في القاموس، نسأل الذكاء الاصطناعي
    if not ticker:
        system_prompt = """
        استخرج رمز السهم (Ticker) واسم الشركة من الجملة.
        - الأسهم المصرية يجب أن تنتهي بـ .CA (مثال: COMI.CA)
        - الأسهم السعودية بـ .SR
        الرد JSON فقط: {"action": "analyze", "ticker": "...", "search_term": "..."}
        لو دردشة عادية: {"action": "chat", "reply": "..."}
        """
        try:
            completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            decision = json.loads(completion.choices[0].message.content)
        except:
            return {"action": "error", "reply": "حدث خطأ في الاتصال"}
    else:
        # لو لقيناه في القاموس، نجهز الرد بنفس شكل الموديل
        decision = {
            "action": "analyze",
            "ticker": ticker,
            "search_term": name
        }

    # ---------------------------------------------------------
    # 🔧 التعديل السحري (Auto-Fixer):
    # ده الجزء اللي هيصلح الشارت لو الرمز بايظ
    # ---------------------------------------------------------
    if decision.get("action") == "analyze":
        raw_ticker = decision.get("ticker", "").upper().strip()

        # لو الرمز مفيهوش نقطة (زي COMI بس)، هنعتبره مصري ونضيفله .CA
        if raw_ticker and "." not in raw_ticker:
            # لو هو أرقام بس (زي 2222) غالباً سعودي
            if raw_ticker.isdigit():
                decision["ticker"] = f"{raw_ticker}.SR"
            # لو حروف (زي ESRS) غالباً مصري
            else:
                decision["ticker"] = f"{raw_ticker}.CA"

    return decision


# ---------------------------------------------------------
# باقي الوظائف (الأخبار والشارت) - زي ما هي
# ---------------------------------------------------------
def get_market_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=ar&gl=EG&ceid=EG:ar"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        if not items: return None
        return "\n".join([f"- {item.title.text}" for item in items[:200]])
    except:
        return None


def analyze_stock_news(news_text, stock_name):
    client = Groq(api_key=API_KEY)
    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "لخص وضع السهم (إيجابي/سلبي) في 10 نقاط."},
            {"role": "user", "content": f"السهم: {stock_name}\n\nالأخبار:\n{news_text}"}
        ]
    )
    return completion.choices[0].message.content


def get_stock_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        return hist
    except:
        return None


# ---------------------------------------------------------
# الواجهة
# ---------------------------------------------------------
st.title("تسلم الايادي(الزنجار الاصلي مابيخونش)")
st.caption("اكتب يا باشا السهم و هقولك تعمل ايه")

if "messages" not in st.session_state: st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("اكتب اسم السهم..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('زوجونا'):
            decision = smart_router(prompt)  # هنا السحر الجديد

        if decision.get("action") == "analyze":
            ticker = decision.get("ticker")
            name = decision.get("search_term")
            source = decision.get("source", "AI")  # عشان نعرف جابه منين

            if source == "database":
                st.success(f"✅ : **{name}** (الرمز: `{ticker}`)")
            else:
                st.info(f"🤖 : **{name}** (الرمز: `{ticker}`)")

            # الرسم البياني
            chart_data = get_stock_chart(ticker)
            if chart_data is not None and not chart_data.empty:
                st.line_chart(chart_data['Close'], color="#FF4B4B")
                st.metric("السعر الحالي", round(chart_data['Close'].iloc[-1], 2))
            else:
                st.warning(f"مش لاقي بيانات للرمز {ticker}")

            # الأخبار
            with st.spinner('جاري التحليل...'):
                news = get_market_news(name)
                if news:
                    analysis = analyze_stock_news(news, name)
                    st.info(analysis)
                else:
                    st.error("مفيش أخبار. اكتب حاجة عدلة")

        elif decision.get("action") == "chat":
            st.markdown(decision["reply"])
            st.session_state.messages.append({"role": "assistant", "content": decision["reply"]})