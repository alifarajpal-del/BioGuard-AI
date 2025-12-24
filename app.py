import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- إعدادات الواجهة الاحترافية (Custom CSS ليتطابق مع صورك) ---
st.set_page_config(page_title="BioGuard AI", layout="centered")

st.markdown("""
<style>
    /* تغيير الخلفية لتكون داكنة مع تدرج كما في صورتك */
    .stApp {
        background: radial-gradient(circle at center, #1a2a3a 0%, #0a0e14 100%);
        color: white;
    }
    /* تصميم بطاقات النتائج الشفافة (Glassmorphism) */
    .result-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(0, 242, 255, 0.2);
        margin-top: 20px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    /* تصميم زر التحليل المتوهج */
    .stButton>button {
        background: linear-gradient(90deg, #00f2ff, #0072ff);
        color: white;
        border: none;
        border-radius: 50px;
        padding: 10px 40px;
        font-weight: bold;
        text-transform: uppercase;
        box-shadow: 0 0 15px rgba(0, 242, 255, 0.4);
    }
    /* بطاقة التحذير (الأحمر) */
    .alert-critical { border: 2px solid #ff4d4d; background: rgba(255, 77, 77, 0.05); }
    /* بطاقة الأمان (الأخضر) */
    .alert-safe { border: 2px solid #00ff88; background: rgba(0, 255, 136, 0.05); }
    
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #00f2ff !important; }
</style>
""", unsafe_allow_html=True)

# --- حل مشكلة الـ API نهائياً (إجبار الموديل المستقر) ---
# تم تحديث طريقة الربط لتجنب v1beta نهائياً
try:
    genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI")
    # استخدام الموديل المستقر مباشرة
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Connection Setup Error")

# --- واجهة المستخدم ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.title("🛡️ BioGuard AI")
st.markdown("<p style='color: #94a3b8;'>Your Health, Our Mission</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, use_column_width=True, caption="Product Scanned")
    
    if st.button("ANALYSE INTELIGENTE"):
        with st.spinner("جاري التحليل العميق..."):
            prompt = """Analyze this food product. 
            Return ONLY a valid JSON object:
            {"name": "string", "calories": "string", "status": "safe" OR "critical", "msg": "Detailed explanation in Arabic"}"""
            
            try:
                # محاولة توليد المحتوى
                response = model.generate_content([prompt, img])
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                data = json.loads(res_text)
                
                # عرض النتيجة بالواجهة الجذابة
                card_class = "alert-safe" if data['status'] == "safe" else "alert-critical"
                status_icon = "✅" if data['status'] == "safe" else "⚠️"
                
                st.markdown(f"""
                <div class="result-card {card_class}">
                    <h2>{status_icon} {data['name']}</h2>
                    <h3 style='color: white !important;'>🔥 {data['calories']} Calories</h3>
                    <hr style='opacity: 0.1'>
                    <p style='font-size: 1.2em; line-height: 1.6;'>{data['msg']}</p>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.error("خطأ: يرجى التأكد من أن صورة المكونات واضحة.")
