import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# --- إعدادات الواجهة الاحترافية (Glassmorphism) ---
st.set_page_config(page_title="BioGuard AI", layout="centered")

# تطبيق التصميم الداكن والبطاقات الشفافة كما في صورك
st.markdown("""
<style>
    .stApp {
        background: radial-gradient(circle at top, #1a2a3a 0%, #0a0e14 100%);
        color: white;
    }
    /* تصميم بطاقات النتائج الشفافة */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: 20px;
        text-align: center;
    }
    /* تصميم أزرار الرفع */
    .stFileUploader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 20px;
        border: 2px dashed rgba(0, 242, 255, 0.3);
    }
    /* تصميم الـ Alerts الملونة من صورك */
    .alert-safe { border-left: 5px solid #00ff88; background: rgba(0, 255, 136, 0.05); }
    .alert-warning { border-left: 5px solid #ffbb00; background: rgba(255, 187, 0, 0.05); }
    .alert-critical { border-left: 5px solid #ff4d4d; background: rgba(255, 77, 77, 0.05); }
    
    h1, h2, h3 { color: #00f2ff !important; font-family: 'Segoe UI', sans-serif; }
</style>
""", unsafe_allow_html=True)

# --- حل مشكلة الـ API 404 نهائياً ---
# استخدام الإصدار المستقر v1 وتحديد الموديل بشكل صحيح
API_KEY = "AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI"
genai.configure(api_key=API_KEY)

# استخدام دالة توليد ذكية تتعامل مع أخطاء الإصدارات
def get_analysis(image):
    try:
        # تحديد الموديل المستقر (Flash)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Analyze this food product image. 
        You MUST return ONLY a valid JSON object with:
        {
          "product_name": "string",
          "calories": "number",
          "ingredients": ["list of strings"],
          "health_status": "safe" OR "warning" OR "critical",
          "reason": "Detailed health explanation in Arabic"
        }
        """
        response = model.generate_content([prompt, image])
        # استخراج الـ JSON فقط من رد الموديل
        json_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(json_text)
    except Exception as e:
        return {"error": str(e)}

# --- بناء واجهة المستخدم ---
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.title("🛡️ BioGuard AI")
st.markdown("Your Health, Our Mission")
st.markdown("</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Drag & Drop or Click to Upload Image", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, use_column_width=True, caption="Product Scanned")
    
    with st.spinner("Analyzing with Intelligent Vision..."):
        result = get_analysis(img)
        
        if "error" in result:
            st.error(f"⚠️ API Connection Error: {result['error']}")
        else:
            # عرض النتائج داخل بطاقات الـ Glassmorphism
            status_class = f"alert-{result['health_status']}"
            
            st.markdown(f"""
            <div class="glass-card {status_class}">
                <h2>{result['product_name']}</h2>
                <h3 style='color: white !important;'>🔥 {result['calories']} Calories</h3>
                <hr style='opacity: 0.1'>
                <p style='font-size: 1.1em;'>{result['reason']}</p>
                <div style='display: flex; flex-wrap: wrap; justify-content: center;'>
                    {' '.join([f"<span style='background:rgba(0,242,255,0.1); padding:5px 10px; border-radius:10px; margin:5px; font-size:0.8em;'>{i}</span>" for i in result['ingredients']])}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("طلب بديل صحي"):
                st.balloons()
