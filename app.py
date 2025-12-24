import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# إعدادات الواجهة
st.set_page_config(page_title="BioGuard AI", layout="centered")

# الربط بالـ API
genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI")
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("🛡️ BioGuard AI Dashboard")

# إضافة ملفات WebP للصيغ المسموح بها
uploaded_file = st.file_uploader("ارفع صورة المنتج...", type=["jpg", "png", "jpeg", "webp"])

if uploaded_file:
    # تحويل الصورة إلى RGB لضمان توافق Gemini مع صيغة WebP
    img = Image.open(uploaded_file).convert("RGB")
    st.image(img, use_container_width=True, caption="تم رفع الصورة بنجاح")
    
    with st.spinner("جاري التحليل..."):
        prompt = """Analyze this food image. Return ONLY JSON with: 
        product_name, calories, all_ingredients (list), risky_elements (list)."""
        
        try:
            response = model.generate_content([prompt, img])
            res_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)
            
            st.success(f"المنتج: {data.get('product_name')}")
            st.metric("🔥 السعرات", data.get('calories'))
            st.write("📋 المكونات:", ", ".join(data.get('all_ingredients', [])))
            
            for risk in data.get('risky_elements', []):
                st.error(f"⚠️ تنبيه: يحتوي على {risk}")
        except Exception as e:
            st.error(f"حدث خطأ في المعالجة: {e}")
