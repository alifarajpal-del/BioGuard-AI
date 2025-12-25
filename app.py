import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="BioGuard AI",
    page_icon="🛡️",
    layout="centered"
)

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at center, #1a2a3a 0%, #0a0e14 100%);
    color: white;
}
.result-card {
    background: rgba(255, 255, 255, 0.04);
    backdrop-filter: blur(18px);
    border-radius: 22px;
    padding: 26px;
    margin-top: 25px;
    text-align: center;
    box-shadow: 0 10px 40px rgba(0,0,0,0.8);
}
.alert-safe {
    border: 2px solid #00ff88;
}
.alert-critical {
    border: 2px solid #ff4d4d;
}
.stButton>button {
    background: linear-gradient(90deg, #00f2ff, #0072ff);
    color: white;
    border: none;
    border-radius: 40px;
    padding: 12px 45px;
    font-weight: 700;
    box-shadow: 0 0 18px rgba(0, 242, 255, 0.45);
}
h1, h2, h3 {
    color: #00f2ff !important;
    font-family: 'Segoe UI', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ---------------- GEMINI SETUP ----------------
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("❌ API Key غير موجود. تأكد من ضبط Environment Variable")
    st.stop()

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    safety_settings={
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
        "HARM_CATEGORY_SEXUAL_CONTENT": "BLOCK_NONE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
    }
)

# ---------------- UI ----------------
st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
st.title("🛡️ BioGuard AI")
st.markdown("<p style='color:#94a3b8'>Smart Food Safety Scanner</p>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "📷 ارفع صورة المنتج",
    type=["jpg", "jpeg", "png", "webp"]
)

# ---------------- IMAGE ANALYSIS ----------------
if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, caption="Product Image", use_column_width=True)

    if st.button("🔍 ANALYZE PRODUCT"):
        with st.spinner("جاري التحليل الذكي..."):
            prompt = """
You are a food safety expert AI.

Analyze the product in the image.
Return ONLY valid JSON in Arabic.

Schema:
{
  "name": "اسم المنتج",
  "calories": "عدد السعرات التقريبي",
  "status": "safe أو critical",
  "msg": "شرح صحي مختصر وواضح"
}
"""

            try:
                response = model.generate_content([prompt, image])
                raw_text = response.text

                # استخراج JSON حتى لو كان محاط بنص
                match = re.search(r"\{.*\}", raw_text, re.DOTALL)
                if not match:
                    raise ValueError("Invalid JSON")

                data = json.loads(match.group())

                card_class = "alert-safe" if data["status"] == "safe" else "alert-critical"
                icon = "✅" if data["status"] == "safe" else "⚠️"

                st.markdown(f"""
                <div class="result-card {card_class}">
                    <h2>{icon} {data["name"]}</h2>
                    <h3 style="color:white">🔥 {data["calories"]} سعرة حرارية</h3>
                    <hr style="opacity:0.15">
                    <p style="font-size:1.15em;line-height:1.7">
                        {data["msg"]}
                    </p>
                </div>
                """, unsafe_allow_html=True)

            except Exception:
                st.error("❌ تعذر تحليل الصورة. جرّب صورة أوضح للمكونات.")
