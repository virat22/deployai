"""
DeployAI — AI Engine (GitHub Models)
Uses GPT-4o via GitHub Models (Microsoft AI stack)
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = None


def get_client() -> OpenAI:
    global client
    if client is None:
        # Try Streamlit secrets first, then env vars
        try:
            import streamlit as st
            token = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN"))
        except Exception:
            token = os.getenv("GITHUB_TOKEN")
        client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=token
        )
    return client


def get_model() -> str:
    try:
        import streamlit as st
        return st.secrets.get("AI_MODEL", os.getenv("AI_MODEL", "gpt-4o"))
    except Exception:
        return os.getenv("AI_MODEL", "gpt-4o")


def validate_delta(delta_yaml: str, global_yaml: str, full_yaml: str) -> str:
    """Validate the generated delta using AI."""
    prompt = f"""You are an expert Kubernetes/Helm engineer. Analyze this generated delta YAML file and validate it.

DELTA (generated site-specific overrides):
```yaml
{delta_yaml}
```

GLOBAL BASE (first 200 lines):
```yaml
{global_yaml[:8000]}
```

Validate the delta and report:
1. **Duplicates**: Any values in the delta that are identical to the global (should be removed)
2. **Resolved Placeholders**: Values that are just %DNINT%, %n1ZID% etc resolved to real hostnames (should be removed)
3. **Helm Array Issues**: Any arrays that will fully replace the global array — warn if incomplete
4. **Sizing Values**: Any cpu/memory/replicas/storage sizes that should be in a DIM file instead
5. **Recommendations**: Suggested removals or additions

Respond in markdown format."""

    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=2000
    )
    return response.choices[0].message.content


def enhance_delta_with_ai(full_yaml: str, global_yaml: str, dim_yaml: str) -> str:
    """Use AI to generate the delta directly."""
    prompt = f"""You are an expert Kubernetes/Helm engineer. Given three Helm values files, generate a SITE-SPECIFIC DELTA file.

FULL SITE CONFIG:
```yaml
{full_yaml[:12000]}
```

GLOBAL BASE:
```yaml
{global_yaml[:12000]}
```

DIM FILE (sizing, already handled):
```yaml
{dim_yaml[:4000]}
```

Generate a delta YAML containing ONLY values from FULL that:
1. DIFFER from GLOBAL in meaning (not just placeholder resolution)
2. Are NOT in DIM
3. Are NOT resolved placeholders (%DNINT% → real domain, top.secret.repo → real registry)
4. Are NOT sizing values (cpu, memory, replicas, storage size, JVM heap)

For arrays: Helm replaces entirely. If array differs, include COMPLETE array.
Output ONLY valid YAML with a header comment."""

    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=4000
    )
    return response.choices[0].message.content


def explain_delta(delta_yaml: str) -> str:
    """Generate human-readable explanation of the delta."""
    prompt = f"""Explain this Helm values delta file in simple terms. For each entry, explain what it does and why it might differ per site.

```yaml
{delta_yaml}
```

Format as a markdown table:
| Key | Value | Why Site-Specific |
|-----|-------|------------------|
"""
    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000
    )
    return response.choices[0].message.content
