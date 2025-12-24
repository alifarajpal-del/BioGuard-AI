import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# 1. إعداد واجهة Streamlit
st.set_page_config(page_title="BioGuard AI", layout="centered")

# 2. الربط بالـ API مع تحديد النسخة المستقرة لتجنب خطأ 404
# نستخدم هنا 'v1' بدلاً من الافتراضي
genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI", transport='rest')

# محاولة تحميل النموذج بمسارين مختلفين لضمان العمل
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    model = genai.GenerativeModel('models/gemini-1.5-flash')

st.title("🛡️ BioGuard AI Dashboard")
st.write("الآن يدعم جميع الصيغ بما في ذلك WebP")

uploaded_file = st.file_uploader("ارفع صورة المنتج...", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file:
    # تحويل الصورة لضمان التوافق
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, use_container_width=True)
    
    with st.spinner("جاري التحليل العميق..."):
        prompt = """Analyze this image. Return ONLY JSON with: 
        'product_name', 'calories', 'all_ingredients' (list), 'risky_elements' (list)."""
        
        try:
            # طلب التوليد
            response = model.generate_content([prompt, img])
            
            # تنظيف النص المستلم
            res_text = response.text.strip()
            if "```json" in res_text:
                res_text = res_text.split("```json")[1].split("```")[0].strip()
            elif "```" in res_text:
                res_text = res_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(res_text)
            
            # عرض النتائج الاحترافية
            st.success(f"المنتج: {data.get('product_name')}")
            st.metric("🔥 السعرات الحرارية", data.get('calories'))
            
            st.subheader("📋 المكونات المرصودة")
            st.write(", ".join(data.get('all_ingredients', [])))
            
            for risk in data.get('risky_elements', []):
                st.error(f"⚠️ تنبيه صحي: تم رصد {risk}")
        except Exception as e:
            st.error(f"تنبيه: تأكد من وضوح صورة المكونات (Error: {str(e)})")
