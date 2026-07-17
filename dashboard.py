import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import yfinance as yf
import json
from thefuzz import process  


# ---------------------------------------------------------
st.set_page_config(page_title="تسلم الأيادي", page_icon="😘", layout="wide")
try:
    API_KEY = st.secrets["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"]
except:
    st.warning("مطلوب مفتاح API للعمل")
    st.stop()

# Data base
STOCK_DB = {
    # Egypt
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

    # Suadi Arabia
    "أرامكو aramco": "2222.SR",
    "مصرف الراجحي al rajhi": "1120.SR",
    "سابك sabic": "2010.SR",
    "الأهلي السعودي snb": "1180.SR",
    "الكهرباء السعودية": "5110.SR",

    # USA
    "apple أبل": "AAPL",
    "tesla تسلا": "TSLA",
    "microsoft مايكروسوفت": "MSFT",
    "google جوجل": "GOOGL",
    "amazon أمازون": "AMZN",
    "meta فيسبوك": "META",
    "nvidia إنفيديا": "NVDA",
    "gold ذهب": "GC=F", 
    "bitcoin بيتكوين": "BTC-USD" 
}

def display_rtl(text):
    """
    وظيفة لإجبار النص يظهر من اليمين للشمال مع تنسيق مريح للعين
    """
    st.markdown(
        f"""
        <div style="direction: rtl; text-align: right; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #101114; padding: 20px; border-radius: 10px; border-right: 5px solid #ff4b4b;">
            {text.replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )
# ---------------------------------------------------------
# (Fuzzy Search) 
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
#(Router)
def smart_router(user_input):
    client = Groq(api_key=API_KEY)
    
    # 1. البحث في القاموس أولاً
    ticker, name = find_ticker_smart(user_input)
    if ticker:
        return {
            "action": "analyze",
            "ticker": ticker,
            "search_term": name,
            "source": "database"
        }
    
    system_prompt = """
    أنت خبير أسواق مالية. استخرج رمز السهم (Yahoo Finance Ticker) واسم الشركة بدقة.
    
    القواعد الصارمة للرموز:
    1. الأسهم المصرية (Egypt): يجب إضافة ".CA" في النهاية (مثال: COMI.CA).
    2. الأسهم السعودية (Saudi): يجب إضافة ".SR" في النهاية (مثال: 2222.SR).
    3. الأسهم الأمريكية (US): بدون لاحقة (مثال: AAPL, TSLA, NVDA).
    4. العملات الرقمية: تنتهي بـ "-USD" (مثال: BTC-USD).
    
    الرد JSON فقط:
    {
        "action": "analyze",
        "ticker": "الرمز الصحيح باللاحقة",
        "search_term": "اسم الشركة بالعربي"
    }
    
    لو الكلام دردشة عادية: {"action": "chat", "reply": "..."}
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
       
        return decision

    except Exception as e:
        return {"action": "error", "reply": f"خطأ: {str(e)}"}


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
            {"role": "system", "content": "لخص وضع السهم (إيجابي/سلبي) في 10 نقاط وانصح في الاخر بنسبة المخاطرة و هل احط فيها حاجة ولا لا و قولي اهم الاخبار من ال 200 خبر."},
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


# Interface
st.title("BOLD")
st.caption("Write a company")

if "messages" not in st.session_state: st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("اكتب اسم السهم..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('جاري العمل'):
            decision = smart_router(prompt)  
        if decision.get("action") == "analyze":
            ticker = decision.get("ticker")
            name = decision.get("search_term")
            source = decision.get("source", "AI")  

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
                    st.markdown("### اتفضل:")
                    display_rtl(analysis)
                else:
                    st.error("مفيش أخبار.")

        elif decision.get("action") == "chat":
            st.markdown(decision["reply"])

            st.session_state.messages.append({"role": "assistant", "content": decision["reply"]})





