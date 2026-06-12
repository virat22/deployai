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
    from core.ai_engine import validate_delta, enhance_delta_with_ai, explain_delta
    AI_AVAILABLE = True
except Exception:
    AI_AVAILABLE = False

st.set_page_config(page_title="DeployAI", page_icon="🚀", layout="wide")

st.title("🚀 DeployAI")
st.subheader("AI-Powered Infrastructure Delivery")

tab1, tab2, tab3 = st.tabs(["📄 YAML Delta Generator", "⚙️ CI Pipeline Generator", "🔐 Certificate Generator"])

# --- Tab 1: Delta Generator ---
with tab1:
    st.markdown("### Generate Site-Specific Delta File")
    st.markdown("Upload your full site config, global base, and optional DIM file to get a clean delta.")

    col1, col2, col3 = st.columns(3)

    with col1:
        full_file = st.file_uploader("Full Site File", type=["yaml", "yml"], key="full")
    with col2:
        global_file = st.file_uploader("Global Base File", type=["yaml", "yml"], key="global")
    with col3:
        dim_file = st.file_uploader("DIM File (optional)", type=["yaml", "yml"], key="dim")

    use_ai = st.checkbox("🤖 Use AI Enhancement (Azure OpenAI)", value=False, disabled=not AI_AVAILABLE)
    if not AI_AVAILABLE:
        st.caption("⚠️ Configure .env with Azure OpenAI credentials to enable AI features")

    if st.button("Generate Delta", type="primary"):
        if full_file and global_file:
            full_content = full_file.read().decode("utf-8")
            global_content = global_file.read().decode("utf-8")
            dim_content = dim_file.read().decode("utf-8") if dim_file else ""

            with st.spinner("Computing delta..."):
                if use_ai and AI_AVAILABLE:
                    result = enhance_delta_with_ai(full_content, global_content, dim_content)
                else:
                    result = generate_delta_file(
                        full_yaml=full_content,
                        global_yaml=global_content,
                        dim_yaml=dim_content,
                        full_name=full_file.name,
                        global_name=global_file.name,
                        dim_name=dim_file.name if dim_file else ""
                    )

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

            # AI-powered validation and explanation
            if AI_AVAILABLE:
                with col_b:
                    if st.button("🔍 Validate with AI"):
                        with st.spinner("AI validating..."):
                            validation = validate_delta(result, global_content, full_content)
                        st.markdown(validation)
                with col_c:
                    if st.button("💡 Explain Delta"):
                        with st.spinner("AI explaining..."):
                            explanation = explain_delta(result)
                        st.markdown(explanation)
        else:
            st.error("Please upload at least the Full Site File and Global Base File.")

# --- Tab 2: CI Pipeline Generator ---
with tab2:
    st.markdown("### Generate GitLab CI Pipeline")
    st.markdown("Provide chart details to generate a production-ready `.gitlab-ci.yml`")

    product_name = st.text_input("Product Name", value="ngxp-trust-manager")
    registry = st.text_input("Container Registry", value="ericngxpint10acr.azurecr.io")
    image_name = st.text_input("Image Name", value="trust-manager")
    image_tag = st.text_input("Image Tag", value="v0.20.2")

    if st.button("Generate Pipeline", type="primary", key="gen_pipe"):
        pipeline = f"""workflow:
  rules:
    - if: $CI_COMMIT_TAG
      when: never
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      when: never
    - when: always

default:
  before_script:
    - source build.env
    - source build.sh
    - export BUILD_PKG_NAME="${{PRODUCT_NAME}}-${{CI_COMMIT_BRANCH}}.tar.gz"
  tags:
    - cmgt-grp-shell-runner-rich

stages:
  - build
  - package
  - publish

variables:
  PRODUCT_NAME: {product_name}
  REGISTRY: {registry}
  ARTIFACTORY_REPO_PATH: ngxp/packages

build-helm:
  stage: build
  before_script:
    - source build.sh
  script:
    - echo "Packaging Helm chart"
    - build_helm
  artifacts:
    paths:
      - .builds/helm/*.tgz
    expire_in: 1 week

record-image:
  stage: build
  script:
    - mkdir -p .builds/images
    - echo "{registry}/{image_name}:{image_tag}" > .builds/images/images.txt
    - cat .builds/images/images.txt
  artifacts:
    paths:
      - .builds/images/images.txt

create-package:
  stage: package
  needs:
    - build-helm
    - record-image
  script:
    - PKG_NAME="${{PRODUCT_NAME}}-${{CI_COMMIT_REF_SLUG}}.tar.gz"
    - mkdir package
    - cp .builds/helm/*.tgz package/
    - cp .builds/images/images.txt package/
    - tar -czf "$PKG_NAME" -C package .
    - echo "Created package:"
    - ls -lh "$PKG_NAME"
  artifacts:
    paths:
      - "*.tar.gz"

publish:
  stage: publish
  needs:
    - create-package
  script:
    - PKG_NAME="${{PRODUCT_NAME}}-${{CI_COMMIT_REF_SLUG}}.tar.gz"
    - jf config rm artifactory --quiet || true
    - >-
      jf config add artifactory --interactive=false
      --url="$ARTIFACTORY_BASE_URL"
      --artifactory-url="$ARTIFACTORY_BASE_URL/artifactory/"
      --user="$ARTIFACTORY_USER"
      --access-token="$ARTIFACTORY_KEY"
    - jf rt ping --server-id=artifactory
    - >-
      jf rt u --server-id=artifactory --flat=false
      "$PKG_NAME" "${{ARTIFACTORY_REPO_PATH}}/${{CI_COMMIT_BRANCH}}/$PKG_NAME"
    - jf config rm artifactory --quiet
    - echo "Package uploaded successfully"
"""
        st.success("Pipeline generated!")
        st.code(pipeline, language="yaml")
        st.download_button("Download .gitlab-ci.yml", data=pipeline, file_name=".gitlab-ci.yml")

# --- Tab 3: Certificate Generator ---
with tab3:
    st.markdown("### Generate cert-manager Certificate CR")

    cert_name = st.text_input("Certificate Secret Name", value="app-es-http-secret")
    namespace = st.text_input("Namespace", value="cert-manager")
    issuer_name = st.text_input("ClusterIssuer Name", value="eric-ngxp-vault-issuer-vprobe-jwt-rsa")
    common_name = st.text_input("Common Name", value="app-es-http-secret.exfohub.com")
    dns_names = st.text_area("DNS Names (one per line)", value="*.live-session.svc\n*.live-session.svc.cluster.local")
    key_size = st.selectbox("Key Size", [4096, 2048], index=0)

    if st.button("Generate Certificate", type="primary", key="gen_cert"):
        dns_list = [d.strip() for d in dns_names.strip().split("\n") if d.strip()]
        dns_yaml = "\n".join([f"    - \"{d}\"" for d in dns_list])

        cert_yaml = f"""apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: {cert_name}
  namespace: {namespace}
spec:
  secretName: {cert_name}
  issuerRef:
    name: {issuer_name}
    kind: ClusterIssuer
  commonName: {common_name}
  privateKey:
    algorithm: RSA
    size: {key_size}
    encoding: PKCS8
  dnsNames:
{dns_yaml}
"""
        st.success("Certificate CR generated!")
        st.code(cert_yaml, language="yaml")
        st.download_button("Download Certificate YAML", data=cert_yaml, file_name=f"{cert_name}.yaml")
