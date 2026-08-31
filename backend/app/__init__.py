"""Backend application package."""

import os
import sys
from pathlib import Path

# Ensure backend root and local venv site-packages are always in sys.path
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

_venv_site_packages = _backend_dir / "venv" / "Lib" / "site-packages"
if _venv_site_packages.exists() and str(_venv_site_packages) not in sys.path:
    sys.path.insert(0, str(_venv_site_packages))
