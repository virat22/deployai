"""
DeployAI — Core YAML Delta Generator
Computes site-specific delta: Full - Global - DIM
"""
import yaml
import re
from copy import deepcopy


def load_yaml(content: str) -> dict:
    """Load YAML from string, handling %placeholders% and anchors."""
    # First try direct load
    try:
        return yaml.safe_load(content) or {}
    except yaml.YAMLError:
        pass

    # Remove anchors/aliases and quote %PLACEHOLDER% patterns
    sanitized = content
    # Remove anchor definitions (&name)
    sanitized = re.sub(r'\s+&[A-Za-z_][A-Za-z0-9_]*', '', sanitized)
    # Replace alias references (*name) with placeholder
    sanitized = re.sub(r'\*[A-Za-z_][A-Za-z0-9_]*', '"__alias__"', sanitized)
    # Quote unquoted %PLACEHOLDER% values
    sanitized = re.sub(r':\s+(%[A-Za-z0-9_]+%)', r': "\1"', sanitized)

    try:
        return yaml.safe_load(sanitized) or {}
    except yaml.YAMLError as e:
        # Last resort: line-by-line fix
        lines = []
        for line in content.split('\n'):
            if line.strip().startswith('#'):
                lines.append(line)
                continue
            # Remove anchors
            line = re.sub(r'\s+&[A-Za-z_][A-Za-z0-9_]*', '', line)
            # Replace aliases
            line = re.sub(r'\*[A-Za-z_][A-Za-z0-9_]*', '"__alias__"', line)
            # Quote %placeholders%
            if '%' in line:
                line = re.sub(r':\s+([^"\'#\n]*%[A-Za-z0-9_]+%[^"\'#\n]*)', r': "\1"', line)
            lines.append(line)
        try:
            return yaml.safe_load('\n'.join(lines)) or {}
        except yaml.YAMLError:
            return {}


def is_placeholder_resolved(global_val, site_val) -> bool:
    """Check if site value is just a resolved placeholder from global."""
    if not isinstance(global_val, str) or not isinstance(site_val, str):
        return False
    placeholders = re.findall(r'%[A-Za-z0-9_]+%', global_val)
    if not placeholders:
        return False
    pattern = re.escape(global_val)
    for ph in placeholders:
        pattern = pattern.replace(re.escape(ph), r'.+')
    return bool(re.fullmatch(pattern, site_val))


def is_registry_placeholder(global_val, site_val) -> bool:
    """Check if it's a registry URL resolved from a generic placeholder."""
    generic_registries = ['top.secret.io', 'top.secret.repo']
    if isinstance(global_val, str) and global_val.strip() in generic_registries:
        return True
    return False


SIZING_KEYS = {
    'cpu', 'memory', 'hugepages', 'replicas', 'replicaCount',
    'Xmx', 'Xms', '-Xmx', '-Xms', 'AvailableRamGB',
    'nbEsdrSessionContext', 'nbTcpSessionContext', 'nbCPEnrichmentContext',
    'minReplicas', 'maxReplicas', 'retentionSize'
}


def is_sizing_key(key: str) -> bool:
    """Check if a key is a sizing/DIM concern."""
    return key in SIZING_KEYS


def is_resource_block(key: str, val) -> bool:
    """Check if this is a resources block (requests/limits with cpu/memory)."""
    if key == 'resources' and isinstance(val, dict):
        return any(k in val for k in ('requests', 'limits'))
    return False


def flatten_keys(d: dict, prefix: list = None) -> set:
    """Get all leaf key paths from a dict."""
    if prefix is None:
        prefix = []
    keys = set()
    if isinstance(d, dict):
        for k, v in d.items():
            path = prefix + [k]
            if isinstance(v, dict):
                keys.update(flatten_keys(v, path))
            else:
                keys.add(tuple(path))
    return keys


def path_in_dim_leaf(path: list, d: dict) -> bool:
    """Check if a key path resolves to a LEAF value in DIM (not just a parent dict)."""
    current = d
    for p in path:
        if isinstance(current, dict) and p in current:
            current = current[p]
        else:
            return False
    # It's in DIM only if we reached a leaf (not a dict that has sub-keys)
    return not isinstance(current, dict)


def compute_delta(full: dict, global_base: dict, dim: dict, path: list = None) -> dict:
    """Recursively compute delta between full site and global, excluding DIM."""
    if path is None:
        path = []
    delta = {}

    if not isinstance(full, dict):
        return delta

    for key, site_val in full.items():
        current_path = path + [key]

        # Skip sizing keys
        if is_sizing_key(key):
            continue

        # Skip resource blocks entirely
        if is_resource_block(key, site_val):
            continue

        # Skip if this exact path is a LEAF in DIM
        if path_in_dim_leaf(current_path, dim):
            continue

        global_val = global_base.get(key) if isinstance(global_base, dict) else None

        # Both are dicts — recurse
        if isinstance(site_val, dict) and isinstance(global_val, dict):
            sub_delta = compute_delta(site_val, global_val, dim, current_path)
            if sub_delta:
                delta[key] = sub_delta

        # Key doesn't exist in global — it's new/site-specific
        elif key not in (global_base or {}):
            if not is_sizing_key(key) and not is_resource_block(key, site_val):
                delta[key] = deepcopy(site_val)

        # Values differ
        elif site_val != global_val:
            # Skip resolved placeholders
            if is_placeholder_resolved(global_val, site_val):
                continue
            if is_registry_placeholder(global_val, site_val):
                continue
            # Skip lists with same content (minor formatting)
            if isinstance(site_val, list) and isinstance(global_val, list):
                if set(str(x) for x in site_val) == set(str(x) for x in global_val):
                    continue
            delta[key] = deepcopy(site_val)

    return delta


def generate_delta_file(full_yaml: str, global_yaml: str, dim_yaml: str = "",
                        full_name: str = "", global_name: str = "", dim_name: str = "") -> str:
    """Main entry point: generate a site delta YAML string."""
    full = load_yaml(full_yaml)
    global_base = load_yaml(global_yaml)
    dim = load_yaml(dim_yaml) if dim_yaml else {}

    delta = compute_delta(full, global_base, dim)

    # Ensure 'global' key exists
    if 'global' not in delta:
        delta = {'global': {}, **delta}

    header = f"""# Site-specific delta overrides (auto-generated by DeployAI)
# Base: {global_name}
# DIM: {dim_name or 'None'}
# Logic: {full_name} - {global_name} - {dim_name or 'None'}
"""
    yaml_output = yaml.dump(delta, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return header + "---\n" + yaml_output
