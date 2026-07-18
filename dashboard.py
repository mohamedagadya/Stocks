import streamlit as st
import requests
from bs4 import BeautifulSoup
from groq import Groq
import yfinance as yf
import json
from thefuzz import process  

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
    أنت نظام توجيه ذكي (Router). مهمتك قراءة المحادثة وتحديد نية المستخدم في رسالته **الأخيرة فقط** بدقة.
    هام جداً: يجب أن يكون الرد بصيغة JSON فقط.
    
    القواعد الصارمة:
    1. إذا كانت الرسالة الأخيرة تطلب تحليل سهم، أو تذكر اسم شركة بشكل مباشر (مثل: "فوري"، "التجاري الدولي"، "أبل")، اختر "analyze" واستخرج الرمز:
    {
        "action": "analyze",
        "ticker": "الرمز هنا",
        "search_term": "اسم الشركة"
    }
    
    قواعد بناء الرموز (Tickers):
    - الأسهم المصرية: يجب إضافة ".CA" (مثال: COMI.CA, FWRY.CA, ESRS.CA, MFPC.CA)
    - الأسهم السعودية: يجب إضافة ".SR" (مثال: 2222.SR, 1120.SR)
    - الأسهم الأمريكية: بدون لاحقة (مثال: AAPL, TSLA)
    - العملات الرقمية: تنتهي بـ "-USD" (مثال: BTC-USD)
    
    2. إذا كانت الرسالة الأخيرة عبارة عن سؤال استكمالي، استفسار عن التحليل السابق، أو دردشة (مثل: "اشرح أكثر"، "ما رأيك؟"، "هل أشتري؟")، اختر "chat":
    {
        "action": "chat"
    }
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

@st.cache_data(ttl=900) # الاحتفاظ بالبيانات في الذاكرة لمدة 15 دقيقة
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
    
    system_prompt = """
    أنت محلل مالي خبير ومستشار استثماري محترف. مهمتك تحليل الأخبار المقدمة لك واستخراج الخلاصة بشكل منظم واحترافي.
    
    قواعد الرد:
    1. قدم ملخصاً عاماً عن وضع السهم (إيجابي، سلبي، محايد) بناءً على الأخبار.
    2. استخرج أهم 7 إلى 10 نقاط محورية تؤثر على سعر السهم، مع تجاهل الأخبار المكررة أو غير المهمة.
    3. حدد مستوى المخاطرة (عالي، متوسط، منخفض) مع توضيح السبب .
    4. قدم رؤيتك الاستثمارية بحيادية (هل السهم جذاب للمتابعة أم يحتاج حذر؟).
    5. استخدم لغة عربية فصحى واضحة، ونسق الرد باستخدام العناوين العريضة والنقاط (Bullet points).
    6. استعرض ارقام السهم والشركة بشكل مفصل 
    7. اضف اشياء من عندك لو هناك اشياء اخرى
    """
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"السهم: {stock_name}\n\nالأخبار:\n{news_text}"}
        ],
        temperature=0.2 
    )
    return completion.choices[0].message.content

@st.cache_data(ttl=900)        
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
            source = decision.get("source", "AI")  

            
            st.info(f"🤖 : **{name}** (الرمز: `{ticker}`)")

            # الرسم البياني
            chart_data = get_stock_chart(ticker)
            if chart_data is not None and not chart_data.empty:
                st.line_chart(chart_data['Close'], color="#FF4B4B")
                st.metric("السعر الحالي", round(chart_data['Close'].iloc[-1], 2))
            else:
                st.warning(f"مش لاقي بيانات للرمز {ticker}")

            # الأخبار والتحليل
            with st.spinner('جاري التحليل واستخراج البيانات...'):
                news = get_market_news(name)
                if news:
                    analysis = analyze_stock_news(news, name)
                    st.markdown("### اتفضل التقرير:")
                    display_rtl(analysis)
                    
                    # === التعديل الأساسي: حفظ التحليل في الذاكرة عشان الموديل يفتكره ===
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
                for msg in st.session_state.messages[-8:]:
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
                    st.error(f"حصل خطأ أثناء الدردشة: {str(e)}")
                    
        elif decision.get("action") == "error":
            st.error(decision.get("reply"))
