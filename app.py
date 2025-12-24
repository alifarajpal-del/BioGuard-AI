import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# 1. إعدادات الصفحة والستايل (التصميم الذي صممناه)
# -------------------------------------------------------
st.set_page_config(page_title="BioGuard AI", layout="centered")

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .stApp { background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%); }
    
    /* تصميم البطاقات الشفافة */
    .report-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 15px;
        direction: rtl;
    }
    
    .status-safe { border-right: 5px solid #10b981; }
    .status-warning { border-right: 5px solid #f59e0b; }
    .status-critical { border-right: 5px solid #ef4444; }
    
    .card-title { color: #ffffff; font-weight: bold; font-size: 1.2rem; }
    .card-text { color: #cbd5e1; font-size: 1rem; }
</style>
""", unsafe_allow_html=True)

# 2. حل مشكلة الـ API 404 نهائياً
# -------------------------------------------------------
# استخدام النسخة v1 المستقرة والربط المباشر
try:
    genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI")
    # نحدد الموديل بدون 'models/' لتجنب مشاكل المسارات في بعض الإصدارات
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"خطأ في إعداد المحرك: {e}")

# 3. واجهة التحميل
# -------------------------------------------------------
st.markdown("<h1 style='text-align: center; color: white;'>🛡️ BioGuard AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #94a3b8;'>Your Health, Our Mission</p>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type=["jpg", "jpeg", "png", "webp"])

if uploaded_file:
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, use_container_width=True)
    
    with st.spinner("جاري التحليل الحيوي للمنتج..."):
        # البرومبت لضمان استخراج السعرات والمكونات
        prompt = """Analyze this food product. 
        Return ONLY a JSON object with: 
        'name', 'calories', 'ingredients' (list), 'risks' (list of dicts with 'type' and 'msg').
        Types should be: 'safe', 'warning', or 'critical'."""
        
        try:
            # استخدام generate_content مع معالجة الخطأ
            response = model.generate_content([prompt, img])
            
            # تنظيف الـ JSON
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_text)
            
            # عرض البيانات بتصميم الواجهة المرفقة
            st.markdown(f"### نتائج الفحص لـ: {data.get('name')}")
            st.markdown(f"**السعرات الحرارية المقدرة:** {data.get('calories')}")
            
            # عرض المكونات كـ Tags
            tags = " ".join([f"<span style='background:#334155; color:white; padding:4px 10px; border-radius:15px; margin:2px; display:inline-block;'>{i}</span>" for i in data.get('ingredients', [])])
            st.markdown(tags, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # عرض بطاقات التحذير (التصميم المطلوب)
            for risk in data.get('risks', []):
                css_class = f"status-{risk['type']}"
                st.markdown(f"""
                <div class="report-card {css_class}">
                    <div class="card-title">⚠️ تحليل: {risk.get('type').upper()}</div>
                    <div class="card-text">{risk.get('msg')}</div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            # في حال استمر خطأ 404، سنقوم بتنبيه المستخدم لتغيير نسخة المكتبة
            st.error(f"حدث خطأ في الاتصال بالسيرفر. يرجى التأكد من تحديث ملف requirements.txt")
            st.code("google-generativeai>=0.7.0")

# 4. تذييل الصفحة
st.markdown("<hr style='border: 0.5px solid rgba(255,255,255,0.1)'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #475569;'>BioGuard AI v1.0 - Alpha Phase</p>", unsafe_allow_html=True)
