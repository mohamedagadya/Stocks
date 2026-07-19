import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import yfinance as yf
import json
from thefuzz import process  
import re
import pandas as pd
from supabase import create_client, Client
import hashlib
# ---------------------------------------------------------
st.set_page_config(page_title="Bold", page_icon="😘", layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
except:
    st.warning("مطلوب مفتاح API للعمل")
    st.stop()

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.warning("حدث خطأ في الاتصال بقاعدة البيانالت.")
    st.stop()

# ==========================================
# نظام الحسابات والبوابة الأمنية (Authentication)
# ==========================================

# دالة بسيطة لتشفير الباسورد
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# التحقق: لو اليوزر مش مسجل دخول، اعرضله شاشة الدخول ووقف الكود
if "user_id" not in st.session_state:
    st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>مرحباً بك في BOLD </h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #888;'>المنصة الذكية لتحليل الأسواق المالية</p>", unsafe_allow_html=True)
    st.divider()
    
    # تقسيم الشاشة لتبويبات (تسجيل دخول / إنشاء حساب)
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
    
    with tab1:
        st.subheader("تسجيل الدخول")
        login_user = st.text_input("اسم المستخدم", key="login_user")
        login_pass = st.text_input("كلمة المرور", type="password", key="login_pass")
        
        if st.button("دخول", use_container_width=True):
            if login_user and login_pass:
                hashed_pass = hash_password(login_pass)
                try:
                    # البحث عن المستخدم في قاعدة البيانات السحابية
                    response = supabase.table("app_users").select("*").eq("username", login_user).eq("password", hashed_pass).execute()
                    users = response.data
                    
                    if users and len(users) > 0:
                        # حفظ بيانات المستخدم في الذاكرة المؤقتة
                        st.session_state.user_id = users[0]['id']
                        st.session_state.username = users[0]['username']
                        st.success("تم تسجيل الدخول بنجاح!   ...")
                        st.rerun() # عمل ريفرش للصفحة عشان تقرأ باقي الكود
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
                except Exception as e:
                    st.error(f"حدث خطأ في الاتصال: {e}")
            else:
                st.warning("يرجى إدخال اسم المستخدم وكلمة المرور.")

    with tab2:
        st.subheader("إنشاء حساب جديد")
        reg_user = st.text_input("اسم المستخدم", key="reg_user")
        reg_pass = st.text_input("كلمة المرور", type="password", key="reg_pass")
        reg_pass_confirm = st.text_input("تأكيد كلمة المرور", type="password", key="reg_pass_confirm")
        
        if st.button("إنشاء حساب", use_container_width=True):
            if reg_user and reg_pass and reg_pass_confirm:
                if reg_pass == reg_pass_confirm:
                    hashed_pass = hash_password(reg_pass)
                    try:
                        # إدخال المستخدم الجديد في قاعدة البيانات
                        supabase.table("app_users").insert({"username": reg_user, "password": hashed_pass}).execute()
                        st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول من التبويب الأول.")
                    except Exception as e:
                        # اصطياد خطأ تكرار الاسم (لأننا عاملين unique في الداتا بيز)
                        if "duplicate" in str(e).lower() or "unique" in str(e).lower() or "23505" in str(e):
                            st.error("اسم المستخدم مسجل بالفعل، يرجى اختيار اسم آخر.")
                        else:
                            st.error(f"حدث خطأ أثناء إنشاء الحساب: {e}")
                else:
                    st.error("كلمات المرور غير متطابقة.")
            else:
                st.warning("يرجى تعبئة جميع الحقول.")
                
    # الأمر ده هو الحارس: بيمنع قراءة باقي الأبلكيشن لو اليوزر مش مسجل دخول
    st.stop()


def get_ticker_from_db(search_term):
    """
    دالة بتسحب الأسهم من Supabase وتدور على أقرب تطابق ذكي
    """
    try:
        # سحب كل الشركات من قاعدة البيانات
        response = supabase.table("stocks").select("company_name, ticker").execute()
        all_stocks = response.data
        
        if not all_stocks:
            return None, None
            
        # تحويل البيانات لقاموس عشان نستخدم البحث الذكي
        db_dict = {row['company_name']: row['ticker'] for row in all_stocks}
        
        # البحث المرن بنسبة تطابق 70%
        best_match = process.extractOne(search_term, list(db_dict.keys()), score_cutoff=70)
        
        if best_match:
            matched_name = best_match[0]
            return db_dict[matched_name], matched_name
        return None, None
        
    except Exception as e:
        st.error(f"حصل خطأ في الاتصال بقاعدة البيانات: {e}")
        return None, None

# ==========================================
# إدارة غرف المحادثة (Chat Sessions)
# ==========================================
def fetch_user_sessions(user_id):
    try:
        res = supabase.table("chat_sessions").select("id, session_title").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except:
        return []

def fetch_messages(session_id):
    try:
        res = supabase.table("chat_messages").select("role, content").eq("session_id", session_id).order("created_at").execute()
        return res.data
    except:
        return []

def create_new_session(user_id, ticker, title):
    try:
        res = supabase.table("chat_sessions").insert({
            "user_id": user_id, 
            "ticker": ticker, 
            "session_title": title
        }).execute()
        return res.data[0]['id']
    except:
        return None

def save_chat_message(session_id, role, content):
    if session_id:
        try:
            supabase.table("chat_messages").insert({
                "session_id": session_id, 
                "role": role, 
                "content": content
            }).execute()
        except:
            pass



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
    # رفعنا نسبة الشبه لـ 80% عشان نمنع العك
    best_match = process.extractOne(user_text, list(STOCK_DB.keys()), score_cutoff=80)

    if best_match:
        matched_name = best_match[0]
        ticker = STOCK_DB[matched_name]
        return ticker, matched_name
    else:
        return None, None

# ---------------------------------------------------------
#(Router)
def smart_router(messages):
    client = Groq(api_key=API_KEY)
    
    system_prompt = """
    أنت نظام توجيه ذكي (Router). مهمتك قراءة المحادثة وتحديد نية المستخدم في رسالته الأخيرة فقط بدقة.
    هام جداً: يجب أن يكون الرد بصيغة JSON فقط.
    
    القواعد الصارمة للرموز (Tickers):
    1. للأسهم المصرية: يجب إضافة ".CA" في النهاية. 
       - استخدم هذه القائمة المرجعية للأسهم المصرية للوصول للرمز الدقيق:
         (فوري: FWRY.CA)، (إي فاينانس: EFIH.CA)، (التجاري الدولي: COMI.CA)، (حديد عز: ESRS.CA)، (طلعت مصطفى: TMGH.CA)، (موبكو: MFPC.CA)، (السويدي: SWDY.CA)، (بلتون: BTLL.CA)، (بالم هيلز: PHDC.CA)، (هيرميس: HRHO.CA)، (سيدي كرير: SKPC.CA)، (أبو قير: ABUK.CA).
       - إذا سأل المستخدم عن شركة مصرية غير موجودة بالقائمة، استنتج الرمز الأقرب وأضف .CA.
       
    2. الأسهم السعودية: يجب إضافة ".SR" (مثال: 2222.SR).
    3. الأسهم الأمريكية: بدون لاحقة (مثال: AAPL, TSLA).
    
    شكل الرد المطلوب (JSON):
    - إذا كان الطلب تحليل سهم: {"action": "analyze", "ticker": "الرمز", "search_term": "اسم الشركة"}
    - إذا كان الطلب دردشة أو سؤال عن تحليل سابق: {"action": "chat"}
    """
    
    # نجهز الرسايل ونحط الـ System Prompt في الأول
    messages_to_send = [{"role": "system", "content": system_prompt}]
    
    # نبعت للموجه آخر 4 رسايل بس عشان يفهم السياق
    for msg in messages[-4:]:
        messages_to_send.append({"role": msg["role"], "content": msg["content"]})
        
    try:
        # التعديل هنا: استخدام الموديل الأكبر والأذكى للربط المنطقي
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=messages_to_send,
            temperature=0, # مهم يفضل صفر عشان يكون دقيق في الرموز وميهبدش
            response_format={"type": "json_object"}
        )
        
        decision = json.loads(completion.choices[0].message.content)
        return decision

    except Exception as e:
        return {"action": "error", "reply": f"خطأ: {str(e)}"}

@st.cache_data(ttl=900)
def get_market_news(query):
    url = f"https://news.google.com/rss/search?q={query}&hl=ar&gl=EG&ceid=EG:ar"
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all("item")
        
        if not items: return None
        
        # الاكتفاء بأهم 15 عنوان إخباري فقط لتوفير التوكنز وتسريع الرد
        return "\n".join([f"- {item.title.text}" for item in items[:25]])
        
    except Exception as e:
        return None
@st.cache_data(ttl=300) # كاش لمدة 5 دقايق بس عشان نحافظ على تحديث السعر اللحظي
def scrape_egx_mubasher(ticker):
    """
    سكرابر مخصص للسوق المصري بيسحب السعر اللحظي وأحدث الأخبار من مباشر
    """
    # التأكد إن السهم مصري أولاً
    if not ticker.endswith(".CA"):
        return None
        
    # تجهيز رمز السهم للبحث في موقع مباشر
    symbol = ticker.replace(".CA", "")
    url = f"https://www.mubasher.info/markets/EGX/stocks/{symbol}"
    
    # استخدام User-Agent عشان الموقع ميعملش Block للـ Request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. استخراج السعر اللحظي 
        # (نستخدم Regular Expressions لاصطياد الكلاسات اللي بتحتوي على كلمة price)
        price_elem = soup.find(class_=re.compile("market-summary__price", re.I))
        current_price = price_elem.text.strip() if price_elem else None
        
        # 2. استخراج أحدث 3 أخبار حصرية للسهم من صفحته مباشرة
        news_elements = soup.find_all("a", class_=re.compile("article-card__title", re.I))
        stock_news = []
        
        for news in news_elements[:3]:
            title = news.text.strip()
            # تجهيز رابط الخبر لو حبينا نعرضه
            link = "https://www.mubasher.info" + news['href'] if news.has_attr('href') else ""
            stock_news.append(f"- {title}")
            
        news_text = "\n".join(stock_news) if stock_news else "مفيش أخبار حصرية حديثة للسهم ده على مباشر."
        
        return {
            "price": current_price,
            "news": news_text
        }
        
    except Exception as e:
        print(f"Scraping Error: {e}")
        return None


def analyze_stock_news(news_text, stock_name, tech_data=""):
    client = Groq(api_key=API_KEY)
    
    system_prompt = """
    أنت محلل مالي خبير ومستشار استثماري. مهمتك تقديم تحليل شامل بناءً على الأخبار الأساسية والمؤشرات الفنية المقدمة لك.
    
    توجيهات التحليل:
    - ابدأ بملخص يدمج بين المزاج العام للأخبار والوضع الفني للسهم (مثال: السهم إيجابي مالياً ولكنه متشبع بالشراء فنياً).
    - وضح دلالة المؤشرات الفنية (RSI والمتوسطات المتحركة) بشكل مبسط.
    - اسرد أهم الأخبار المؤثرة.
    - قيم مستوى المخاطرة بناءً على المعطيات المدمجة.
    - قدم رؤية استثمارية موضوعية (هل السعر الحالي نقطة دخول جيدة أم ننتظر تصحيح؟).
    """
    
    combined_content = f"السهم: {stock_name}\n\n{tech_data}\n\nالأخبار:\n{news_text}"
    
    try:
        completion = client.chat.completions.create(
            # تغيير الموديل لتخطي الليميت المقفول
            model="llama-3.1-8b-instant", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_content}
            ],
            temperature=0.3 
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        error_msg = str(e)
        # اصطياد الإيرور عشان الأبلكيشن ميضربش
        if "Rate limit" in error_msg or "429" in error_msg:
            return "عذراً، انتهت الباقة المجانية للذكاء الاصطناعي (Rate Limit). يرجى الانتظار قليلاً أو تجربة سهم آخر لاحقاً."
        else:
            return f"حدث خطأ أثناء التحليل: {error_msg}"
@st.cache_data(ttl=900)        
def get_stock_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        # سحب بيانات سنة بدل 6 شهور عشان حسابات المتوسطات الطويلة تكون أدق
        hist = stock.history(period="1y") 
        
        if hist.empty:
            return None
            
        # 1. المتوسطات المتحركة البسيطة (SMA)
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        
        # 2. المتوسطات المتحركة الأسية (EMA) - أسرع في الاستجابة
        hist['EMA_9'] = hist['Close'].ewm(span=9, adjust=False).mean()
        hist['EMA_20'] = hist['Close'].ewm(span=20, adjust=False).mean()
        
        # 3. مؤشر القوة النسبية (RSI 14)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI_14'] = 100 - (100 / (1 + rs))
        
        # 4. مؤشر الماكد (MACD) - لقياس الزخم وتأكيد الاتجاه
        ema_12 = hist['Close'].ewm(span=12, adjust=False).mean()
        ema_26 = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = ema_12 - ema_26
        hist['MACD_Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        
        # 5. بولينجر باندز (Bollinger Bands) - لقياس التذبذب والانفجار السعري
        std = hist['Close'].rolling(window=20).std()
        hist['BB_Upper'] = hist['SMA_20'] + (std * 2)
        hist['BB_Lower'] = hist['SMA_20'] - (std * 2)
        
        # 6. متوسط المدى الحقيقي (ATR) - لقياس معدل المخاطرة وحركة السهم اليومية
        high_low = hist['High'] - hist['Low']
        high_close = (hist['High'] - hist['Close'].shift()).abs()
        low_close = (hist['Low'] - hist['Close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        hist['ATR_14'] = true_range.rolling(14).mean()
        
        # نرجع بآخر 6 شهور بس للرسم البياني عشان الشاشة متكونش زحمة
        return hist.tail(130) # حوالي 6 شهور تداول
    except:
        return None



# ---------------------------------------------------------
# ---------------------------------------------------------
# Sidebar
with st.sidebar:
    st.write(f"👤 مرحباً بك، **{st.session_state.username}**")
    if st.button("تسجيل خروج", use_container_width=True, type="primary"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    # --- قسم غرف المحادثة ---
    st.header("💬 محادثاتي السابقة")
    
    # زرار لفتح شات جديد أبيض
    if st.button("➕ تحليل سهم جديد", use_container_width=True):
        st.session_state.current_session_id = None
        st.session_state.messages = []
        st.rerun()
        
    # عرض الغرف المحفوظة في الداتا بيز
    user_sessions = fetch_user_sessions(st.session_state.user_id)
    for sess in user_sessions:
        if st.button(f"📊 {sess['session_title']}", key=f"session_{sess['id']}", use_container_width=True):
            # لو ضغط على غرفة، نحمل رسايلها
            st.session_state.current_session_id = sess['id']
            db_msgs = fetch_messages(sess['id'])
            st.session_state.messages = [{"role": msg["role"], "content": msg["content"]} for msg in db_msgs]
            st.rerun()

    st.divider()
    
    # --- حاسبة الاستثمار التراكمي (DCA) ---
    st.header("🧮 حاسبة الاستثمار (DCA)")
    st.write("احسب متوسط سعرك بعد ضخ مبلغ الشراء الجديد.")
    owned_shares = st.number_input("عدد الأسهم اللي معاك حالياً", min_value=0.0, value=0.0, step=1.0)
    average_price = st.number_input("متوسط السعر الحالي", min_value=0.0, value=0.0, step=1.0)
    new_investment = st.number_input("المبلغ اللي هتستثمره", min_value=0.0, value=500.0, step=100.0)
    current_market_price = st.number_input("سعر السهم الحالي على الشاشة", min_value=1.0, value=50.0, step=1.0)
    
    if st.button("احسب المتوسط الجديد", use_container_width=True):
        if current_market_price > 0:
            current_total_value = owned_shares * average_price
            new_shares_bought = new_investment / current_market_price
            total_shares = owned_shares + new_shares_bought
            total_invested = current_total_value + new_investment
            new_average = total_invested / total_shares if total_shares > 0 else 0.0
            
            st.success(f" متوسط السعر الجديد: **{new_average:.2f}**")
            st.info(f" إجمالي الأسهم: **{total_shares:.2f}**")
            st.info(f" إجمالي التكلفة: **{total_invested:.2f}**")
        else:
            st.error("سعر السوق لا يمكن أن يكون صفراً.")
# Interface
# Interface
st.title("BOLD")
st.caption("المنصة الذكية لتحليل الأسواق المالية")

# تعريف الذاكرة المبدئية
if "messages" not in st.session_state: 
    st.session_state.messages = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("اكتب اسم السهم أو اسألني عن التحليل..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # لو إحنا فاتحين غرفة قديمة، نحفظ سؤالك في الداتا بيز فوراً
    if st.session_state.current_session_id:
        save_chat_message(st.session_state.current_session_id, "user", prompt)

    with st.chat_message("assistant"):
        with st.spinner('جاري العمل...'):
            decision = smart_router(st.session_state.messages)  
            
        if decision.get("action") == "analyze":
            search_term = decision.get("search_term")
            db_ticker, db_name = get_ticker_from_db(search_term)
            ticker = db_ticker if db_ticker else decision.get("ticker")
            name = db_name if db_ticker else search_term

            # لو دي أول رسالة ومفيش غرفة، نكريت الغرفة باسم السهم
            if not st.session_state.current_session_id:
                new_sess = create_new_session(st.session_state.user_id, ticker, f"تحليل {name}")
                st.session_state.current_session_id = new_sess
                save_chat_message(new_sess, "user", prompt)

            # ... مسار السوق المصري والعالمي (نفس الكود القديم) ...
            if ticker.endswith(".CA"):
                st.caption("🇪🇬 جاري سحب الأسعار اللحظية والأخبار من السوق المصري...")
                with st.spinner('جاري جلب بيانات الجلسة...'):
                    egx_data = scrape_egx_mubasher(ticker)
                    if egx_data and egx_data["price"]:
                        st.metric("السعر اللحظي (مباشر)", egx_data["price"])
                        news = egx_data["news"]
                    else:
                        st.warning("تعذر سحب البيانات اللحظية، سيتم استخدام المصادر البديلة.")
                        news = get_market_news(name)
            else:
                st.caption("🌐 جاري سحب البيانات من الأسواق العالمية...")
                news = get_market_news(name)

            chart_data = get_stock_chart(ticker)
            tech_text = "" 
            
            if chart_data is not None and not chart_data.empty:
                st.line_chart(chart_data['Close'], color="#FF4B4B")
                latest = chart_data.iloc[-1]
                st.markdown("#### 📊 المؤشرات الفنية اللحظية")
                cols1 = st.columns(4)
                cols1[0].metric("السعر الحالي", f"{latest['Close']:.2f}")
                
                if pd.notna(latest['RSI_14']):
                    cols1[1].metric("RSI (القوة النسبية)", f"{latest['RSI_14']:.2f}")
                    macd_status = "إيجابي 🟢" if latest['MACD'] > latest['MACD_Signal'] else "سلبي 🔴"
                    cols1[2].metric("MACD (الزخم)", macd_status)
                    cols1[3].metric("ATR (معدل التذبذب)", f"{latest['ATR_14']:.2f}")
                    
                    cols2 = st.columns(4)
                    cols2[0].metric("EMA 9 (سريع)", f"{latest['EMA_9']:.2f}")
                    cols2[1].metric("SMA 20 (قصير)", f"{latest['SMA_20']:.2f}")
                    cols2[2].metric("SMA 50 (متوسط)", f"{latest['SMA_50']:.2f}")
                    bb_status = "اختراق علوي 🔥" if latest['Close'] > latest['BB_Upper'] else ("كسر سفلي ❄️" if latest['Close'] < latest['BB_Lower'] else "مستقر ⚖️")
                    cols2[3].metric("Bollinger Bands", bb_status)

                    tech_text = f"""
                    البيانات الفنية الحالية الدقيقة للسهم:
                    - إغلاق السعر: {latest['Close']:.2f}
                    - مؤشر القوة النسبية (RSI): {latest['RSI_14']:.2f} (فوق 70 تشبع شرائي، تحت 30 تشبع بيعي).
                    - مؤشر الماكد (MACD): {latest['MACD']:.2f} وخط الإشارة: {latest['MACD_Signal']:.2f} (الحالة: {macd_status}).
                    - المتوسطات السريعة والبطيئة: EMA9 ({latest['EMA_9']:.2f})، SMA20 ({latest['SMA_20']:.2f})، SMA50 ({latest['SMA_50']:.2f}).
                    - نطاق بولينجر: الحد العلوي ({latest['BB_Upper']:.2f})، الحد السفلي ({latest['BB_Lower']:.2f}).
                    - معدل التذبذب (ATR): {latest['ATR_14']:.2f}.
                    بناءً على هذه الأرقام، قم بدمج الرؤية الفنية مع الأخبار الأساسية لتقديم توصية متكاملة.
                    """
            else:
                st.warning(f"عفواً، لا توجد بيانات تاريخية للرسم البياني لرمز {ticker}")

            with st.spinner('جاري قراءة الأخبار والبيانات الفنية لاستخراج التقرير...'):
                if news:
                    analysis = analyze_stock_news(news, name, tech_text)
                    st.markdown("### اتفضل التقرير:")
                    display_rtl(analysis)
                    
                    # حفظ رد الموديل في الذاكرة وفي الداتا بيز
                    assistant_reply = f"تم تحليل سهم {name}:\n\n{analysis}"
                    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
                    save_chat_message(st.session_state.current_session_id, "assistant", assistant_reply)
                else:
                    st.error("مفيش أخبار متاحة حالياً.")

        elif decision.get("action") == "chat":
            with st.spinner('جاري الرد...'):
                # لو بيتكلم دردشة عامة ومفيش غرفة، نكريت واحدة
                if not st.session_state.current_session_id:
                    new_sess = create_new_session(st.session_state.user_id, "GENERAL", "دردشة عامة")
                    st.session_state.current_session_id = new_sess
                    save_chat_message(new_sess, "user", prompt)

                client = Groq(api_key=API_KEY)
                chat_messages = [{"role": "system", "content": "أنت مساعد مالي ذكي. جاوب على أسئلة المستخدم بناءً على السياق."}]
                for msg in st.session_state.messages[-4:]:
                    chat_messages.append({"role": msg["role"], "content": msg["content"]})
                
                try:
                    chat_completion = client.chat.completions.create(
                        model="llama-3.1-8b-instant",
                        messages=chat_messages,
                        temperature=0.5
                    )
                    reply = chat_completion.choices[0].message.content
                    st.markdown(reply)
                    
                    # حفظ في الذاكرة والداتا بيز
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    save_chat_message(st.session_state.current_session_id, "assistant", reply)
                    
                except Exception as e:
                    if "429" in str(e) or "Rate limit" in str(e):
                        st.error("انتهت الباقة المجانية مؤقتاً (Rate Limit).")
                    else:
                        st.error(f"حصل خطأ أثناء الدردشة: {str(e)}")
                    
        elif decision.get("action") == "error":
            st.error(decision.get("reply"))
