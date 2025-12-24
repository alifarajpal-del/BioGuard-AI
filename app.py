import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import os

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="BioGuard AI",
    layout="centered",
    initial_sidebar_state="collapsed"
)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# ---------------- STYLE ----------------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at center, #16222a 0%, #0a0e14 100%);
    color: white;
}
.card {
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(18px);
    border-radius: 22px;
    padding: 28px;
    border: 1px solid rgba(0,242,255,0.25);
    box-shadow: 0 12px 40px rgba(0,0,0,0.8);
    margin-top: 20px;
}
.safe { border-color:#00ff88; }
.warn { border-color:#ffd000; }
.critical { border-color:#ff4d4d; }

.risk-bar {
    height: 10px;
    border-radius: 20px;
    background: linear-gradient(90deg,#00ff88,#ffd000,#ff4d4d);
    margin: 10px 0;
}
h1,h2,h3 { color:#00f2ff; font-family:Segoe UI; }
small { color:#94a3b8; }
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown("<div style='text-align:center'>", unsafe_allow_html=True)
st.title("🛡️ BioGuard AI")
st.markdown("<small>Personal Preventive Health Intelligence</small>")
st.markdown("</div>", unsafe_allow_html=True)

# ---------------- HEALTH PROFILE ----------------
with st.expander("🧬 Health Profile", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        high_bp = st.checkbox("High Blood Pressure")
        diabetes = st.checkbox("Diabetes")
    with col2:
        salt_sens = st.slider("Salt Sensitivity", 1, 5, 3)
        sugar_sens = st.slider("Sugar Sensitivity", 1, 5, 3)

# ---------------- IMAGE INPUT ----------------
uploaded = st.file_uploader(
    "Scan food product image",
    type=["jpg","png","jpeg","webp"]
)

def safe_json(text):
    try:
        text = text[text.find("{"):text.rfind("}")+1]
        return json.loads(text)
    except:
        return None

# ---------------- ANALYSIS ----------------
if uploaded:
    img = Image.open(uploaded).convert("RGB")
    st.image(img, caption="Scanned Product", use_column_width=True)

    if st.button("🔍 Analyse Safely"):
        with st.spinner("Analyzing health impact..."):

            prompt = f"""
You are a preventive health AI.

User conditions:
- High Blood Pressure: {high_bp}
- Diabetes: {diabetes}
- Salt sensitivity: {salt_sens}/5
- Sugar sensitivity: {sugar_sens}/5

Analyze the product image.

Return ONLY valid JSON:
{{
 "name":"",
 "calories":"",
 "risk_score":0-100,
 "status":"safe|warning|critical",
 "reason":"",
 "medical_explanation_ar":"",
 "recommendation_ar":""
}}
"""

            try:
                response = model.generate_content([prompt, img])
                data = safe_json(response.text)

                if not data:
                    st.error("Could not analyze product clearly.")
                else:
                    status_class = (
                        "safe" if data["status"]=="safe"
                        else "warn" if data["status"]=="warning"
                        else "critical"
                    )

                    st.markdown(f"""
                    <div class="card {status_class}">
                        <h2>{data["name"]}</h2>
                        <p>🔥 {data["calories"]} calories</p>
                        <div class="risk-bar"></div>
                        <p><b>Risk Score:</b> {data["risk_score"]}/100</p>
                        <hr>
                        <p><b>Why?</b><br>{data["medical_explanation_ar"]}</p>
                        <hr>
                        <p><b>Recommendation:</b><br>{data["recommendation_ar"]}</p>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception:
                st.error("Analysis failed. Try a clearer image.")