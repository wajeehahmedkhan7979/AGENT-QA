"""
Pytest configuration for backend tests.
Adds parent directory to Python path for module imports.
"""
import sys
from pathlib import Path

# Add parent directory (apps/backend) to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
