#!/usr/bin/env python
import os
import site
import sys
from pathlib import Path


def main() -> None:
    vendor_dir = Path(__file__).resolve().parent / ".vendor"
    if vendor_dir.exists():
        sys.path.insert(0, str(vendor_dir))
    user_site = site.getusersitepackages()
    if user_site and user_site not in sys.path:
        sys.path.append(user_site)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codereviewer.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Install the requirements before running the project."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
