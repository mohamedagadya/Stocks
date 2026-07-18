import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import yfinance as yf
import json
from thefuzz import process  
import re
import pandas as pd
# ---------------------------------------------------------
st.set_page_config(page_title="Bold", page_icon="😘", layout="wide")
try:
    API_KEY = st.secrets["GROQ_API_KEY"]
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
    "العامة لاستصلاح الاراضي" : "AALR.CA",

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
    "bitcoin بيتكوين": "BTC-USD",

    # --- الدفعة الأولى المستخرجة من الموقع (A - E) ---
    "ابوقير للاسمدة": "ABUK.CA",
    "العربية لإدارة وتطوير الأصول": "ACAMD.CA",
    "Acapa Capital Holding": "ACAPA.CA",
    "Alexandria Company For Refractories": "ACFR.CA",
    "العربية لحليج الأقطان": "ACGC.CA",
    "Act Financial": "ACTF.CA",
    "أدكو": "ADCI.CA",
    "مصرف أبو ظبي الإسلامي": "ADIB.CA",
    "آراب ديري-باندا": "ADPC.CA",
    "أراب للتنمية و الاستثمار العقاري": "ADRI.CA",
    "الاهلي للتنمية والاستثمار": "AFDI.CA",
    "مطاحن ومخابز الإسكندرية": "AFMC.CA",
    "Arabia for Investment and Development": "AIDC.CA",
    "اطلس لاستصلاح الاراضى": "AIFI.CA",
    "العربية للاستثمارات": "AIH.CA",
    "اجواء": "AJWA.CA",
    "الاسكندرية لتداول الحاويات": "ALCN.CA",
    "Alexandria Cement Co.": "ALEX.CA",
    "الالومنيوم العربية": "ALUM.CA",
    "عامر جروب": "AMER.CA",
    "المركز الطبي الجديد - الإسكندرية": "AMES.CA",
    "الملتقى العربي للاستثمارات": "AMIA.CA",
    "أموك": "AMOC.CA",
    "المؤشر": "AMPI.CA",
    "ALNAHDA Industrial Co.": "ANCC.CA",
    "Advanced Pharmaceutical Packaging Co.": "APPC.CA",
    "يونيراب": "APSW.CA",
    "بورتو جروب": "ARAB.CA",
    "العربية للأسمنت": "ARCC.CA",
    "المجموعة المصرية العقارية": "AREH.CA",
    "العربية للمحابس": "ARVA.CA",
    "اسيك للتعدين": "ASCM.CA",
    "بايونيرز القابضة": "ASPI.CA",
    "ايه تي ليس": "ATLC.CA",
    "عتاقة": "ATQA.CA",
    "الاسكندرية للادوية": "AXPH.CA",
    "البدر للبلاستيك": "BIDI.CA",
    "بى اى جى للتجارة والاستثمار": "BIGP.CA",
    "بى بى اى القابضة": "BINV.CA",
    "جلاكسو سميثكلاين": "BIOC.CA",
    "Bonyan for Development and Trade": "BONY.CA",
    "بلتون المالية": "BTFH.CA",
    "القاهرة للخدمات التعليمية": "CAED.CA",
    "بنك قناة السويس": "CANA.CA",
    "القلعة للاستشارات المالية": "CCAP.CA",
    "الخليجية الكندية للاستثمار العقاري العربي": "CCRS.CA",
    "مطاحن مصر الوسطى": "CEFM.CA",
    "ريماس": "CERA.CA",
    "العرفة القابضة": "CFGH.CA",
    "سي اي كابيتال القابضة": "CICH.CA",
    "Chemical Dev Ind": "CCID.CA",
    "كريدي أجريكول": "CIEB.CA",
    "Cairo For Investment And Real Estate Developments - CIRA": "CIRA.CA",
    "مستشفى كليوباترا": "CLHO.CA",
    "Contact Financial Holding SAE": "CNFN.CA",
    "البنك التجاري الدولي": "COMI.CA",
    "العقارية للبنوك الوطنية للتنمية": "COPR.CA",
    "القاهرة للزيوت والصابون": "COSG.CA",
    "القاهرة للادوية": "CPCI.CA",
    "Catalyst Partners Middle East": "CPME.CA",
    "ليفت سلاب مصر": "CRST.CA",
    "القناة للتوكيلات الملاحية": "CSAG.CA",
    "التعمير والاستشارات الهندسية": "DAPH.CA",
    "Damietta Container and Cargo Handling": "DCCC.CA",
    "Delta Construction & Rebuilding Co.": "DCRC.CA",
    "الدلتا للتأمين": "DEIN.CA",
    "Digitize for Investment And Technology": "DGTZ.CA",
    "دومتي": "DOMT.CA",
    "دايس": "DSCW.CA",
    "دلتا للطباعة والتغليف": "DTPP.CA",
    "العربية لاستصلاح الاراضي": "EALR.CA",
    "ثمار": "EASB.CA",
    "ايسترن كومباني": "EAST.CA",
    "اصول إى إس بى للوساطة في الاوراق المالية": "EBSC.CA",
    "الجوهرة": "ECAP.CA",
    "مطاحن شرق الدلتا": "EDFM.CA",
    "العربية للصناعات الهندسية": "EEII.CA",
    "Egypt Education Platform - EEP": "EEPE.CA",
    "Egyptian Ferro All": "EFAC.CA",
    "المالية والصناعية المصرية": "EFIC.CA",
    "ايديتا": "EFID.CA",
    "e-finance for Digital and Financial Investments": "EFIH.CA",
    "مصر للالومنيوم": "EGAL.CA",
    "غاز مصر": "EGAS.CA",
    "البنك المصري الخليجي": "EGBE.CA",
    "كيما": "EGCH.CA",
    "وثائق شركة صندوق استثمار المصريين للاستثمار العقاري": "EGREF.CA",

    # --- استكمال أبرز وأهم الشركات لباقي الحروف (F - Z) ---
    "فوري لتكنولوجيا البنوك والمدفوعات الإلكترونية": "FWRY.CA",
    "جي بي كورب (غبور أوتو)": "GBCO.CA",
    "مصر الجديدة للإسكان والتعمير": "HELI.CA",
    "بنك التعمير والإسكان": "HDBK.CA",
    "مجموعة إي إف جي القابضة (هيرميس)": "HRHO.CA",
    "عز الدخيلة للصلب - الإسكندرية": "IRAX.CA",
    "ابن سينا فارما": "ISPH.CA",
    "جهينة للصناعات الغذائية": "JUFO.CA",
    "القاهرة الوطنية للاستثمار والاوراق المالية": "KWIN.CA",
    "مدينة مصر للإسكان والتعمير": "MASR.CA",
    "ماكرو جروب للمستحضرات الطبية": "MCRO.CA",
    "الشركة المصرية لمدينة الإنتاج الإعلامي": "MPRC.CA",
    "ام ام جروب للصناعة والتجارة العالمية": "MTIE.CA",
    "مستشفى النزهه الدولي": "NINH.CA",
    "السادس من أكتوبر للتنمية والاستثمار (سوديك)": "OCDI.CA",
    "أوراسكوم المالية القابضة": "OFH.CA",
    "أوراسكوم للاستثمار القابضة": "OIH.CA",
    "عبور لاند للصناعات الغذائية": "OLFI.CA",
    "أوراسكوم كونستراكشون": "ORAS.CA",
    "أوراسكوم للتنمية مصر": "ORHD.CA",
    "النساجون الشرقيون للسجاد": "ORWE.CA",
    "إيبيكو للأدوية": "PHAR.CA",
    "بايونيرز بروبرتيز للتنمية العمرانية": "PRDC.CA",
    "بنك قطر الوطني الأهلي (QNB)": "QNBA.CA",
    "راية القابضة للاستثمارات المالية": "RAYA.CA",
    "العاشر من رمضان للصناعات الدوائية (راميدا)": "RMDA.CA",
    "رمكو لإنشاء القرى السياحية": "RTVC.CA",
    "بنك البركة مصر": "SAUD.CA",
    "سبأ للأدوية": "SIPC.CA",
    "الدلتا للسكر": "SUGR.CA",
    "المصرية للاتصالات": "ETEL.CA", 
    "زهراء المعادي للاستثمار والتعمير": "ZMID.CA",
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
    
    # دمج الأخبار مع التحليل الفني في رسالة واحدة للموديل
    combined_content = f"السهم: {stock_name}\n\n{tech_data}\n\nالأخبار:\n{news_text}"
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": combined_content}
        ],
        temperature=0.3 
    )
    return completion.choices[0].message.content

@st.cache_data(ttl=900)        
def get_stock_chart(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return None
            
        # حساب المتوسطات المتحركة (Moving Averages)
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        
        # حساب مؤشر القوة النسبية (RSI 14)
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI_14'] = 100 - (100 / (1 + rs))
        
        return hist
    except:
        return None



# ---------------------------------------------------------
# (DCA Calculator - Sidebar)
with st.sidebar:
    st.header("🧮 حاسبة الاستثمار التراكمي (DCA)")
    st.write("احسب متوسط سعرك بعد ضخ مبلغ الشراء الجديد.")
    
    st.divider()
    
    # 1. بيانات المحفظة الحالية
    st.subheader("وضعك الحالي")
    owned_shares = st.number_input("عدد الأسهم اللي معاك حالياً", min_value=0.0, value=0.0, step=1.0)
    average_price = st.number_input("متوسط السعر الحالي", min_value=0.0, value=0.0, step=1.0)
    
    st.divider()
    
    # 2. تفاصيل الشراء الجديد
    st.subheader("الشراء الجديد")
    new_investment = st.number_input("المبلغ اللي هتستثمره", min_value=0.0, value=500.0, step=100.0)
    current_market_price = st.number_input("سعر السهم الحالي على الشاشة", min_value=1.0, value=50.0, step=1.0)
    
    if st.button("احسب المتوسط الجديد", use_container_width=True):
        if current_market_price > 0:
            # العمليات الحسابية
            current_total_value = owned_shares * average_price
            new_shares_bought = new_investment / current_market_price
            
            total_shares = owned_shares + new_shares_bought
            total_invested = current_total_value + new_investment
            
            # تجنب القسمة على صفر
            if total_shares > 0:
                new_average = total_invested / total_shares
            else:
                new_average = 0.0
            
            # عرض النتائج بشكل منظم
            st.success(f" متوسط السعر الجديد: **{new_average:.2f}**")
            st.info(f" إجمالي الأسهم بعد الشراء: **{total_shares:.2f}** سهم")
            st.info(f" إجمالي التكلفة المدفوعة: **{total_invested:.2f}**")
        else:
            st.error("سعر السوق لا يمكن أن يكون صفراً.")

# Interface
st.title("BOLD")
st.caption("Write a company")

if "messages" not in st.session_state: 
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("اكتب اسم السهم أو اسألني عن التحليل..."):
    # إضافة رسالة المستخدم للتاريخ
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner('جاري العمل...'):
            decision = smart_router(st.session_state.messages)  
            
        if decision.get("action") == "analyze":
            ticker = decision.get("ticker")
            name = decision.get("search_term")
            
            st.info(f"🤖 تم استخراج السهم: **{name}** (الرمز: `{ticker}`)")

            # مسار السوق المصري (بيانات لحظية من مباشر)
            if ticker.endswith(".CA"):
                st.caption("🇪🇬 جاري سحب الأسعار اللحظية والأخبار من السوق المصري...")
                with st.spinner('جاري جلب بيانات الجلسة...'):
                    egx_data = scrape_egx_mubasher(ticker)
                    
                    if egx_data and egx_data["price"]:
                        # عرض السعر اللحظي للسوق المصري
                        st.metric("السعر اللحظي (مباشر)", egx_data["price"])
                        news = egx_data["news"]
                    else:
                        st.warning("تعذر سحب البيانات اللحظية، سيتم استخدام المصادر البديلة.")
                        news = get_market_news(name)
                        
            # مسار الأسواق الأمريكية والسعودية
            else:
                st.caption("🌐 جاري سحب البيانات من الأسواق العالمية...")
                news = get_market_news(name)

            # الرسم البياني (استخدام YFinance دايماً للرسم لأنه بيجيب تاريخ 6 شهور)
            # الرسم البياني والمؤشرات الفنية
            chart_data = get_stock_chart(ticker)
            tech_text = "" # نص المؤشرات اللي هيروح للموديل
            
            if chart_data is not None and not chart_data.empty:
                st.line_chart(chart_data['Close'], color="#FF4B4B")
                
                # استخراج أحدث قيم للمؤشرات
                latest_close = chart_data['Close'].iloc[-1]
                latest_sma20 = chart_data['SMA_20'].iloc[-1]
                latest_sma50 = chart_data['SMA_50'].iloc[-1]
                latest_rsi = chart_data['RSI_14'].iloc[-1]
                
                # عرض المؤشرات في أعمدة منظمة
                cols = st.columns(4)
                cols[0].metric("السعر الحالي", f"{latest_close:.2f}")
                
                # التأكد إن القيم مش NaN قبل عرضها
                if pd.notna(latest_rsi):
                    cols[1].metric("RSI (14)", f"{latest_rsi:.2f}")
                    cols[2].metric("SMA 20", f"{latest_sma20:.2f}")
                    cols[3].metric("SMA 50", f"{latest_sma50:.2f}")
                    
                    # تجهيز النص الفني للذكاء الاصطناعي
                    tech_text = f"البيانات الفنية الحالية:\n- السعر: {latest_close:.2f}\n- مؤشر القوة النسبية (RSI): {latest_rsi:.2f}\n- متوسط متحرك 20 يوم: {latest_sma20:.2f}\n- متوسط متحرك 50 يوم: {latest_sma50:.2f}"
            else:
                st.warning(f"عفواً، لا توجد بيانات تاريخية للرسم البياني لرمز {ticker}")

            # التحليل بواسطة الذكاء الاصطناعي
            with st.spinner('جاري قراءة الأخبار والبيانات الفنية لاستخراج التقرير...'):
                if news:
                    # تمرير الأخبار مع البيانات الفنية
                    analysis = analyze_stock_news(news, name, tech_text)
                    st.markdown("### اتفضل التقرير:")
                    display_rtl(analysis)
                    
                    # حفظ التحليل في الذاكرة
                    st.session_state.messages.append({"role": "assistant", "content": f"تم تحليل سهم {name}:\n\n{analysis}"})
                else:
                    st.error("مفيش أخبار متاحة حالياً.")

        elif decision.get("action") == "chat":
            with st.spinner('جاري الرد...'):
                client = Groq(api_key=API_KEY)
                
                # بناء سياق المحادثة المخصص للدردشة
                chat_messages = [
                    {"role": "system", "content": "أنت مساعد مالي ذكي ومحترف. مهمتك الإجابة على استفسارات المستخدم ومناقشته بناءً على سياق المحادثة السابق. إذا سألك عن شركة قمت بتحليلها سابقاً، استخدم هذا التحليل للرد بعمق."}
                ]
                
                # تمرير آخر 8 رسائل من الذاكرة للموديل عشان يفهم السياق 
                for msg in st.session_state.messages[-4:]:
                    chat_messages.append({"role": msg["role"], "content": msg["content"]})
                
                try:
                    # استخدام موديل 70b للدردشة عشان يكون أذكى في الردود
                    chat_completion = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=chat_messages,
                        temperature=0.5
                    )
                    reply = chat_completion.choices[0].message.content
                    
                    # عرض الرد وحفظه
                    st.markdown(reply)
                    st.session_state.messages.append({"role": "assistant", "content": reply})
                    
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "Rate limit" in error_msg:
                        st.error("(Rate Limit) ")
                    else:
                        st.error(f"حصل خطأ أثناء الدردشة: {error_msg}")
                    
        elif decision.get("action") == "error":
            st.error(decision.get("reply"))
