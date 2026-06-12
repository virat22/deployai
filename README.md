# DeployAI 🚀

AI-Powered Infrastructure Delivery Platform

## Problem
Modern Kubernetes deployments involve complex Helm values management across multiple environments (global + site deltas + DIM sizing), certificate lifecycle management, and CI/CD pipeline creation. Today this requires deep expertise and error-prone manual YAML operations.

## Solution
DeployAI automates infrastructure delivery using AI:
1. **YAML Delta Generator** — Upload full site config + global base → get clean site-specific delta
2. **CI Pipeline Generator** — Input chart details → get production-ready GitLab CI pipeline
3. **Certificate Generator** — Input DNS/namespace → get cert-manager Certificate CR

## Tech Stack
- **AI**: Azure OpenAI (GPT-4o) via Azure AI Foundry
- **Agent Framework**: Semantic Kernel
- **Frontend**: Streamlit
- **Hosting**: Azure Container Apps
- **Code**: Python 3.11+

## Setup

```bash
# Clone
git clone https://github.com/<your-repo>/deployai.git
cd deployai

# Install
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your Azure OpenAI credentials

# Run
streamlit run app/main.py
```

## Architecture

```
User → Streamlit UI → Core Modules → Azure OpenAI (validation/enhancement)
                         ├── delta_generator.py (YAML diff logic)
                         ├── pipeline_generator.py (CI/CD templates)
                         └── cert_generator.py (Certificate CRs)
```

## Team
- [Your Name] — Platform Engineer / SRE

## License
MIT
