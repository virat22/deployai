"""Full test suite for delta generator with all file pairs."""
import sys
sys.path.insert(0, '.')
from core.delta_generator import generate_delta_file

tests = [
    {
        "name": "FEA_ECP",
        "full": "/home/epahvir/FEA_ECP_ORValues.yaml",
        "global": "/home/epahvir/FCP_ORValues.yaml",
        "dim": "/home/epahvir/FEA_ECP_DIM_ORValues.yaml",
    },
    {
        "name": "FEA_EUP",
        "full": "/home/epahvir/FEA_EUP_ORValues.yaml",
        "global": "/home/epahvir/FUP_ORValues.yaml",
        "dim": "/home/epahvir/FEA_EUP_DIM_ORValues.yaml",
    },
    {
        "name": "EML_FEA_Pure",
        "full": "/home/epahvir/EML_FEA_Pure_ORValues.yaml-Template",
        "global": "/home/epahvir/EML_FCP_ORValues.yaml-Template",
        "dim": "/home/epahvir/EML_FEA_Pure_DIM_ORValues.yaml",
    },
]

for t in tests:
    print(f"\n{'='*60}")
    print(f"TEST: {t['name']}")
    print(f"{'='*60}")
    try:
        with open(t['full']) as f:
            full = f.read()
        with open(t['global']) as f:
            glob = f.read()
        with open(t['dim']) as f:
            dim = f.read()

        result = generate_delta_file(full, glob, dim, t['full'], t['global'], t['dim'])
        lines = result.strip().split('\n')
        print(f"Output: {len(lines)} lines")
        # Show first 20 lines of actual content (skip header)
        content_lines = [l for l in lines if not l.startswith('#') and l != '---']
        for line in content_lines[:20]:
            print(f"  {line}")
        if len(content_lines) > 20:
            print(f"  ... ({len(content_lines) - 20} more lines)")
        print(f"\n✅ {t['name']} PASSED")
    except Exception as e:
        print(f"\n❌ {t['name']} FAILED: {e}")
