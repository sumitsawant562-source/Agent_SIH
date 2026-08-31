import sys
import os
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add venv site-packages if available to ensure all libraries (jose, etc.) can be found
venv_site_packages = backend_dir / "venv" / "Lib" / "site-packages"
if venv_site_packages.exists() and str(venv_site_packages) not in sys.path:
    sys.path.insert(0, str(venv_site_packages))
