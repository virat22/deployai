"""
DeployAI — Streamlit Frontend
AI-powered infrastructure delivery platform
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.delta_generator import generate_delta_file

# Try importing AI engine (graceful fallback if not configured)
try:
    from core.ai_engine import validate_delta, enhance_delta_with_ai, explain_delta, get_client
    try:
        token = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN"))
    except Exception:
        token = os.getenv("GITHUB_TOKEN")
    AI_AVAILABLE = bool(token)
except Exception:
    AI_AVAILABLE = False

st.set_page_config(page_title="DeployAI", page_icon="🚀", layout="wide")

st.title("🚀 DeployAI")
st.subheader("AI-Powered Infrastructure Delivery")

st.markdown("### Generate Site-Specific Delta File")
st.markdown("Upload your full site config, global base, and optional DIM file to get a clean delta.")

col1, col2, col3 = st.columns(3)

with col1:
    full_file = st.file_uploader("Full Site File", type=["yaml", "yml"], key="full")
with col2:
    global_file = st.file_uploader("Global Base File", type=["yaml", "yml"], key="global")
with col3:
    dim_file = st.file_uploader("DIM File (optional)", type=["yaml", "yml"], key="dim")

if st.button("Generate Delta", type="primary"):
    if full_file and global_file:
        full_content = full_file.read().decode("utf-8")
        global_content = global_file.read().decode("utf-8")
        dim_content = dim_file.read().decode("utf-8") if dim_file else ""

        with st.spinner("Computing delta..."):
            result = generate_delta_file(
                full_yaml=full_content,
                global_yaml=global_content,
                dim_yaml=dim_content,
                full_name=full_file.name,
                global_name=global_file.name,
                dim_name=dim_file.name if dim_file else ""
            )

        st.session_state["delta_result"] = result
        st.session_state["global_content"] = global_content
        st.session_state["full_content"] = full_content
    else:
        st.error("Please upload at least the Full Site File and Global Base File.")

# Display results if available
if "delta_result" in st.session_state:
    result = st.session_state["delta_result"]
    st.success("Delta generated!")
    st.code(result, language="yaml")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            label="📥 Download Delta",
            data=result,
            file_name="SITE_delta.yaml",
            mime="text/yaml"
        )

    if AI_AVAILABLE:
        with col_b:
            if st.button("🔍 Validate with AI"):
                with st.spinner("AI validating..."):
                    validation = validate_delta(result, st.session_state["global_content"], st.session_state["full_content"])
                st.markdown(validation)
        with col_c:
            if st.button("💡 Explain Delta"):
                with st.spinner("AI explaining..."):
                    explanation = explain_delta(result)
                st.markdown(explanation)
