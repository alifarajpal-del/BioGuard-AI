import concurrent.futures
import html
import json
import os
import re
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import streamlit as st
from PIL import Image

try:
    import google.generativeai as genai
except Exception:
    genai = None


APP_TITLE = "BioGuard AI"
MODEL_NAME = "gemini-1.5-flash"

DEFAULT_TIMEOUT_SECONDS = 35
MAX_IMAGE_LONG_EDGE = 1400


@dataclass
class RiskResult:
    product_name: str
    risk_level: str
    estimated_calories_kcal: Optional[float]
    warning_ar: str
    key_risk_factors: list[str]
    uncertainty: str


def _get_api_key() -> Optional[str]:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        return st.secrets.get("GEMINI_API_KEY")
    if hasattr(st, "secrets") and "GOOGLE_API_KEY" in st.secrets:
        return st.secrets.get("GOOGLE_API_KEY")

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _resize_image_for_inference(img: Image.Image) -> Image.Image:
    w, h = img.size
    long_edge = max(w, h)
    if long_edge <= MAX_IMAGE_LONG_EDGE:
        return img

    scale = MAX_IMAGE_LONG_EDGE / float(long_edge)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return img.resize((new_w, new_h))


def _sanitize_json_candidate(text: str) -> str:
    if not text:
        return ""

    s = text.strip()

    # Remove common markdown fences if present.
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)

    # If model added any leading/trailing explanation, grab the first JSON object.
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start : end + 1]

    return s.strip()


def _parse_risk_result(raw_text: str) -> Tuple[Optional[RiskResult], Optional[str]]:
    candidate = _sanitize_json_candidate(raw_text)
    if not candidate:
        return None, "empty_model_response"

    try:
        data = json.loads(candidate)
    except Exception:
        return None, "invalid_json"

    if not isinstance(data, dict):
        return None, "json_not_object"

    product_name = str(data.get("product_name") or data.get("product") or data.get("name") or "")

    risk_level = str(data.get("risk_level") or data.get("risk") or "").strip().upper()
    if risk_level in {"LOW RISK", "LOW_RISK"}:
        risk_level = "LOW"
    if risk_level in {"HIGH RISK", "HIGH_RISK"}:
        risk_level = "HIGH"

    estimated = data.get("estimated_calories_kcal")
    if estimated is None:
        estimated = data.get("estimated_calories")

    estimated_calories_kcal: Optional[float]
    if estimated is None or estimated == "":
        estimated_calories_kcal = None
    else:
        try:
            estimated_calories_kcal = float(estimated)
        except Exception:
            estimated_calories_kcal = None

    warning_ar = str(data.get("warning_ar") or data.get("warning") or data.get("message_ar") or "").strip()

    key_risk_factors = data.get("key_risk_factors") or data.get("risk_factors") or []
    if isinstance(key_risk_factors, str):
        key_risk_factors = [key_risk_factors]
    if not isinstance(key_risk_factors, list):
        key_risk_factors = []
    key_risk_factors = [str(x) for x in key_risk_factors if str(x).strip()]

    uncertainty = str(data.get("uncertainty") or "MEDIUM").strip().upper()
    if uncertainty not in {"LOW", "MEDIUM", "HIGH"}:
        uncertainty = "MEDIUM"

    if risk_level not in {"LOW", "HIGH"}:
        return None, "missing_or_invalid_risk_level"

    if not warning_ar:
        return None, "missing_warning_ar"

    return (
        RiskResult(
            product_name=product_name,
            risk_level=risk_level,
            estimated_calories_kcal=estimated_calories_kcal,
            warning_ar=warning_ar,
            key_risk_factors=key_risk_factors,
            uncertainty=uncertainty,
        ),
        None,
    )


def _build_prompt() -> str:
    # Keep prompt concise and deterministic.
    return (
        "You are BioGuard AI, a preventive health risk interpreter for packaged foods. "
        "Analyze the provided food product image (front label and/or ingredients panel). "
        "Extract what you can ONLY from the image and make cautious inferences if needed. "
        "You must NOT provide a medical diagnosis. Provide preventive awareness only.\n\n"
        "Return ONLY valid JSON (no markdown, no code fences, no extra text).\n"
        "JSON schema:\n"
        "{\n"
        "  \"product_name\": string,\n"
        "  \"risk_level\": \"LOW\" or \"HIGH\",\n"
        "  \"estimated_calories_kcal\": number or null,\n"
        "  \"warning_ar\": string (Arabic),\n"
        "  \"key_risk_factors\": array of strings,\n"
        "  \"uncertainty\": \"LOW\" or \"MEDIUM\" or \"HIGH\"\n"
        "}\n\n"
        "Risk guidance:\n"
        "- HIGH if image suggests high sugar/sodium/ultra-processed risks, or if uncertain but potentially risky.\n"
        "- LOW only when there are clear signals of lower risk.\n"
        "- warning_ar must be short, clear, and non-diagnostic, in Arabic.\n"
    )


def _call_gemini(image: Image.Image, timeout_s: int) -> str:
    if genai is None:
        raise RuntimeError("google-generativeai not installed")

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("missing_api_key")

    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config={
            "temperature": 0.2,
            "max_output_tokens": 512,
        },
    )

    prompt = _build_prompt()

    def _do_call() -> str:
        # google-generativeai accepts PIL.Image for multimodal calls.
        resp = model.generate_content([prompt, image])
        # Prefer .text if available.
        txt = getattr(resp, "text", None)
        if txt is None:
            # Some SDK versions store candidates differently; fallback to string conversion.
            txt = str(resp)
        return txt

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_do_call)
        return future.result(timeout=timeout_s)


def _analyze(image: Image.Image, timeout_s: int) -> RiskResult:
    # Retry strategy: 1 retry on JSON parse/validation errors.
    last_err: Optional[str] = None

    for attempt in range(2):
        raw = _call_gemini(image=image, timeout_s=timeout_s)
        result, err = _parse_risk_result(raw)
        if result is not None:
            return result

        last_err = err or "unknown_parse_error"

        # Small backoff before retry.
        if attempt == 0:
            time.sleep(0.6)

    raise RuntimeError(f"ai_output_invalid:{last_err}")


def _inject_css() -> None:
    st.markdown(
        """
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');

          html, body, [class*="css"], .stApp {
            font-family: 'Poppins', sans-serif;
          }

          .stApp {
            background: radial-gradient(1200px 800px at 15% 20%, rgba(0,255,255,0.12), rgba(0,0,0,0) 60%),
                        radial-gradient(1000px 700px at 85% 30%, rgba(255,0,180,0.10), rgba(0,0,0,0) 55%),
                        linear-gradient(135deg, #060818 0%, #070a1a 35%, #060818 100%);
            color: #EAF2FF;
          }

          .bg-card {
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            backdrop-filter: blur(10px);
            border-radius: 18px;
            padding: 18px 18px;
          }

          .title {
            font-size: 2.0rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
          }

          .subtitle {
            opacity: 0.9;
            margin-bottom: 14px;
          }

          .risk-card {
            border-radius: 18px;
            padding: 18px;
            border: 1px solid rgba(255,255,255,0.14);
            background: rgba(255,255,255,0.06);
          }

          .risk-low {
            box-shadow: 0 0 18px rgba(0, 255, 150, 0.35), 0 0 40px rgba(0, 255, 150, 0.15);
            border-color: rgba(0, 255, 150, 0.35);
          }

          .risk-high {
            box-shadow: 0 0 18px rgba(255, 60, 90, 0.35), 0 0 40px rgba(255, 60, 90, 0.15);
            border-color: rgba(255, 60, 90, 0.35);
          }

          .risk-label {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 8px;
          }

          .muted {
            opacity: 0.8;
          }

          .small {
            font-size: 0.95rem;
          }

          .hr {
            height: 1px;
            background: rgba(255,255,255,0.10);
            margin: 12px 0;
          }

          .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            margin-right: 8px;
            margin-bottom: 8px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        f"""
        <div class="bg-card">
          <div class="title">{APP_TITLE}</div>
          <div class="subtitle">امسح المنتج الغذائي فوراً واحصل على تنبيه صحي مبسّط (للوقاية، وليس للتشخيص).</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_result(result: RiskResult) -> None:
    is_high = result.risk_level == "HIGH"
    card_class = "risk-card risk-high" if is_high else "risk-card risk-low"
    icon = "⚠️" if is_high else "✅"
    label = "HIGH RISK" if is_high else "LOW RISK"

    product_line = f"<div class=\"muted small\">{html.escape(result.product_name) if result.product_name else ''}</div>"

    calories_line = ""
    if result.estimated_calories_kcal is not None:
        calories_line = (
            f"<div class=\"muted small\">Estimated calories: {result.estimated_calories_kcal:.0f} kcal</div>"
        )

    factors_html = ""
    if result.key_risk_factors:
        pills = "".join([f"<span class=\"pill\">{html.escape(x)}</span>" for x in result.key_risk_factors])
        factors_html = f"<div class=\"hr\"></div><div class=\"small\">{pills}</div>"

    st.markdown(
        f"""
        <div class="{card_class}">
          <div class="risk-label">{icon} {label}</div>
          {product_line}
          {calories_line}
          <div class="hr"></div>
          <div class="small">{html.escape(result.warning_ar)}</div>
          {factors_html}
          <div class="hr"></div>
          <div class="muted small">Uncertainty: {html.escape(result.uncertainty)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    st.sidebar.markdown("## Setup")
    st.sidebar.markdown(
        """
        - Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in your environment, or in Streamlit `secrets`.
        - Run: `streamlit run app.py`
        """
    )

    st.sidebar.markdown("## Tips for best results")
    st.sidebar.markdown(
        """
        - Take a clear photo of the **ingredients panel**.
        - Avoid glare/reflections.
        - Make text readable.
        """
    )

    st.sidebar.markdown("## Disclaimer")
    st.sidebar.markdown("BioGuard AI يقدم توعية صحية وقائية ولا يقدم تشخيصاً طبياً.")


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🧪", layout="centered")
    _inject_css()
    _render_sidebar()

    if "result" not in st.session_state:
        st.session_state.result = None
    if "error" not in st.session_state:
        st.session_state.error = None

    _render_header()

    st.markdown("<div style=\"height: 14px\"></div>", unsafe_allow_html=True)

    uploaded = st.file_uploader("Upload a food product image", type=["png", "jpg", "jpeg"], accept_multiple_files=False)

    if uploaded is not None:
        try:
            img = Image.open(uploaded).convert("RGB")
            img = _resize_image_for_inference(img)
        except Exception:
            st.session_state.error = "تعذر قراءة الصورة. حاول رفع صورة أخرى واضحة." 
            st.session_state.result = None
            img = None

        if img is not None:
            st.image(img, caption="Preview", use_container_width=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                timeout_s = st.number_input(
                    "Timeout (seconds)",
                    min_value=10,
                    max_value=90,
                    value=DEFAULT_TIMEOUT_SECONDS,
                    step=5,
                )

            with col2:
                do_analyze = st.button("Analyze", type="primary", use_container_width=True)

            if do_analyze:
                st.session_state.error = None
                st.session_state.result = None

                if genai is None:
                    st.session_state.error = "المكتبة google-generativeai غير مثبتة. تأكد من تثبيت المتطلبات." 
                else:
                    api_key = _get_api_key()
                    if not api_key:
                        st.session_state.error = "لم يتم العثور على مفتاح API. عيّن GEMINI_API_KEY أو GOOGLE_API_KEY." 
                    else:
                        try:
                            with st.spinner("Analyzing…"):
                                res = _analyze(img, timeout_s=int(timeout_s))
                            st.session_state.result = res
                        except concurrent.futures.TimeoutError:
                            st.session_state.error = "انتهت مهلة التحليل. حاول مرة أخرى بصورة أوضح أو أعد المحاولة لاحقاً." 
                        except RuntimeError as e:
                            msg = str(e)
                            if msg == "missing_api_key":
                                st.session_state.error = "لم يتم العثور على مفتاح API. عيّن GEMINI_API_KEY أو GOOGLE_API_KEY." 
                            elif msg.startswith("ai_output_invalid"):
                                st.session_state.error = "تعذر استخراج نتيجة موثوقة من الصورة. حاول تصوير جدول المكونات بشكل أوضح." 
                            else:
                                st.session_state.error = "حدث خطأ أثناء التحليل. حاول مرة أخرى." 
                        except Exception:
                            st.session_state.error = "حدث خطأ غير متوقع. حاول مرة أخرى." 

    st.markdown("<div style=\"height: 14px\"></div>", unsafe_allow_html=True)

    if st.session_state.error:
        st.error(st.session_state.error)

    if st.session_state.result is not None:
        _render_result(st.session_state.result)


if __name__ == "__main__":
    main()
