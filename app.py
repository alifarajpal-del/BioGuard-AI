import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# 1. إعدادات الهوية البصرية المتقدمة (Glassmorphism & Cyberpunk Theme)
st.set_page_config(page_title="BioGuard AI | Pro Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* تحويل الخلفية إلى فضاء رقمي متدرج */
    .stApp {
        background: radial-gradient(circle at top right, #0d1b2a 0%, #010409 100%);
        color: #e6edf3;
        font-family: 'Inter', sans-serif;
    }
    
    /* تصميم الحاويات الزجاجية (Glass Cards) */
    .glass-panel {
        background: rgba(23, 32, 42, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 30px;
        border: 1px solid rgba(0, 242, 255, 0.2);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
        margin-bottom: 25px;
    }

    /* أزرار الأكشن المتوهجة */
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #00f2ff 0%, #0072ff 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px;
        font-weight: 800;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 242, 255, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0, 242, 255, 0.5);
    }

    /* مؤشرات الحالة الصحية */
    .status-badge {
        padding: 10px 20px;
        border-radius: 50px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
    }
    .safe { background: rgba(16, 185, 129, 0.2); color: #10b981; border: 1px solid #10b981; }
    .critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; }
    
    /* تصميم حقل الرفع */
    .stFileUploader {
        border: 2px dashed rgba(0, 242, 255, 0.3);
        border-radius: 20px;
        background: rgba(255, 255, 255, 0.02);
    }
</style>
""", unsafe_allow_html=True)

# 2. نظام الاتصال الذكي (إصلاح الـ 404 نهائياً)
def initialize_ai():
    try:
        genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI")
        # استخدام النسخة المستقرة بشكل صريح
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.error(f"AI Engine Failure: {str(e)}")
        return None

model = initialize_ai()

# 3. واجهة المستخدم (كل الخيارات التي ناقشناها)
with st.container():
    col_header, col_profile = st.columns([2, 1])
    with col_header:
        st.markdown("<h1 style='color: #00f2ff; margin-bottom: 0;'>🛡️ BioGuard AI</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Advanced Bio-Nutritional Intelligence</p>", unsafe_allow_html=True)
    
    with col_profile:
        # دمج "البروفايل الحيوي" الذي ناقشناه
        with st.expander("👤 بروفايل المستخدم"):
            user_condition = st.multiselect("الحالات الصحية:", ["ضغط دم مرتفع", "سكري", "حساسية لاكتوز"], default=["ضغط دم مرتفع"])
            lang = st.radio("اللغة / Language", ["العربية", "English", "Français"], horizontal=True)

# مساحة العمل الرئيسية
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
    st.subheader("📸 فحص المنتج")
    uploaded_file = st.file_uploader("قم بسحب صورة المنتج أو جدول المكونات هنا", type=["jpg", "png", "jpeg", "webp"])
    
    # خيارات إضافية ناقشناها سابقاً (Simulation)
    st.toggle("تفعيل الإشعارات الذكية", value=True)
    st.toggle("ربط مباشر بالكاميرا", value=False)
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    with col_left:
        st.image(img, use_container_width=True, caption="الصورة التي سيتم تحليلها")
    
    with col_right:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        if st.button("ANALYSE INTELIGENTE | ابدأ التحليل"):
            with st.spinner("🧠 جاري التفكير بعمق في المكونات والآثار الحيوية..."):
                # برومبت صارم لاستخراج JSON دقيق
                prompt = f"""
                You are a senior bio-chemist. Analyze this food product based on these user conditions: {user_condition}.
                Return ONLY a JSON object:
                {{
                  "name": "Product Name",
                  "calories": "Number",
                  "health_score": "safe/warning/critical",
                  "blood_pressure_impact": "High/Low/Medium",
                  "risky_additives": ["list items"],
                  "arabic_summary": "Short 2 sentence advice in Arabic",
                  "healthy_alternative": "Name of a real healthy alternative"
                }}
                """
                try:
                    response = model.generate_content([prompt, img])
                    # تنظيف الاستجابة من أي كود ماركداون
                    raw_data = response.text.replace('```json', '').replace('```', '').strip()
                    data = json.loads(raw_data)
                    
                    # عرض النتائج بطريقة سينمائية
                    status_class = "safe" if data['health_score'] == "safe" else "critical"
                    st.markdown(f"<div class='status-badge {status_class}'>الحالة: {data['health_score'].upper()}</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"## 📦 {data['name']}")
                    
                    c1, c2 = st.columns(2)
                    c1.metric("🔥 السعرات", data['calories'])
                    c2.metric("💓 تأثير الضغط", data['blood_pressure_impact'])
                    
                    st.markdown("### 🚨 الإضافات المرصودة:")
                    for item in data['risky_additives']:
                        st.markdown(f"- `{item}`")
                    
                    st.info(data['arabic_summary'])
                    
                    # ميزة "البديل الصحي" التي ناقشناها
                    st.success(f"💡 البديل المقترح: **{data['healthy_alternative']}**")
                    if st.button("🛒 اطلب البديل الآن (ربح عمولة)"):
                        st.balloons()
                        st.write("يتم الآن توجيهك لمتجر الشركاء...")
                        
                except Exception as e:
                    st.error("⚠️ خطأ في معالجة البيانات. يرجى التأكد من وضوح جدول المكونات.")
                    st.write(f"تفاصيل تقنية للبرمج: {str(e)}")
        st.markdown('</div>', unsafe_allow_html=True)
else:
    with col_right:
        st.markdown('<div class="glass-panel" style="text-align:center; padding:100px 20px;">', unsafe_allow_html=True)
        st.markdown("<h2 style='color: #475569;'>بانتظار الصورة...</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #475569;'>قم برفع صورة المنتج لبدء التحليل الحيوي المتقدم</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
