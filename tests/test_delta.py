"""Quick test for delta generator using your actual files."""
import sys
sys.path.insert(0, '.')
from core.delta_generator import generate_delta_file

# Load your actual files
with open('/home/epahvir/FEA_ECP_ORValues.yaml', 'r') as f:
    full = f.read()
with open('/home/epahvir/FCP_ORValues.yaml', 'r') as f:
    global_base = f.read()
with open('/home/epahvir/FEA_ECP_DIM_ORValues.yaml', 'r') as f:
    dim = f.read()

result = generate_delta_file(
    full_yaml=full,
    global_yaml=global_base,
    dim_yaml=dim,
    full_name="FEA_ECP_ORValues.yaml",
    global_name="FCP_ORValues.yaml",
    dim_name="FEA_ECP_DIM_ORValues.yaml"
)

print(result)
