import streamlit as st
import google.generativeai as genai
from PIL import Image
import json

# إعداد واجهة المستخدم الاحترافية
st.set_page_config(page_title="BioGuard AI", page_icon="🛡️", layout="centered")

# الربط بمفتاح Gemini الخاص بك
genai.configure(api_key="AIzaSyA6PghCI7HTdVUvrGgKqDhPFIW20XPJegI")
model = genai.GenerativeModel('gemini-1.5-flash')

# تصميم واجهة التطبيق
st.markdown("""
    <div style='text-align: center; background-color: #2980b9; padding: 20px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>🛡️ BioGuard AI</h1>
        <p style='color: #ecf0f1;'>مساعدك الذكي للتغذية الآمنة</p>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("📸 التقط صورة للمكونات أو ارفعها من الاستوديو", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="تم رفع المنتج بنجاح", use_container_width=True)
    
    with st.spinner("🔍 BioGuard يحلل السعرات والمكونات الآن..."):
        # البرومبت الصارم لضمان التفاصيل
        prompt = """
        Analyze this food image. You MUST return a JSON with these exact keys:
        'product_name', 'calories', 'all_ingredients' (list), 'risky_elements' (list of Sodium, MSG, etc.).
        Be very detailed about chemical additives and nutritional values.
        """
        response = model.generate_content([prompt, image])
        
        try:
            # تنظيف النص وتحويله لـ JSON
            res_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)
            
            # عرض النتائج في بطاقات
            col1, col2 = st.columns(2)
            col1.metric("📦 المنتج", data.get('product_name', 'Unknown'))
            col2.metric("🔥 السعرات", data.get('calories', 'غير متوفر'))
            
            st.subheader("📋 المكونات الكاملة للمنتج")
            st.write(", ".join(data.get('all_ingredients', [])))
            
            risks = data.get('risky_elements', [])
            if risks:
                st.error("🚨 تحذيرات صحية (هامة لمرضى الضغط):")
                for r in risks:
                    st.warning(f"تنبيه: يحتوي على **{r}** - يفضل البحث عن بديل.")
                    if st.button(f"🛒 اطلب بديل صحي لـ {r}"):
                        st.balloons()
                        st.success("تم توجيهك لمتجر البدائل الصحية (أرباح متوقعة: $2.5)")
            else:
                st.success("✅ المنتج يبدو آمناً بناءً على تحليلي الأولي للمكونات.")
                
        except Exception as e:
            st.error("فشل في استخراج البيانات. تأكد من أن صورة المكونات واضحة.")

