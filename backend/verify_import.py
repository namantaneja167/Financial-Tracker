import sys
from pathlib import Path

# Add project root to python path
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

try:
    from backend.main import app
    from backend.api import endpoints
    print("Backend imports successful!")
except ImportError as e:
    print(f"Backend import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Backend syntax/runtime error: {e}")
    sys.exit(1)
