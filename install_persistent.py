#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoPaw Mempalace Sync - Persistent Installation Script
=====================================================
This script installs the mempalace sync hook using a .pth file,
which persists across CoPaw updates.

The .pth file mechanism is a Python feature that automatically imports
modules when Python starts. Unlike modifying CoPaw source files,
.pth files in site-packages are NOT removed during normal pip updates.
"""

import os
import sys
import shutil
from pathlib import Path

# Configuration
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_PACKAGES = os.path.join(
    os.path.dirname(sys.executable),
    "Lib",
    "site-packages",
)

# Files
PATCH_MODULE = os.path.join(PLUGIN_DIR, "copaw_mempalace_patch.py")
HOOK_MODULE = os.path.join(PLUGIN_DIR, "hooks", "mempalace_sync.py")
SYNC_SCRIPT = os.path.join(PLUGIN_DIR, "scripts", "sync_mempalace.py")

# Targets
TARGET_PATCH = os.path.join(SITE_PACKAGES, "copaw_mempalace_patch.py")
TARGET_HOOK = os.path.join(
    os.path.dirname(SITE_PACKAGES),
    "copaw",
    "agents",
    "hooks",
    "mempalace_sync.py",
)
TARGET_PTH = os.path.join(SITE_PACKAGES, "copaw_mempalace_sync.pth")


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_step(text: str) -> None:
    print(f"\n>>> {text}")


def print_success(text: str) -> None:
    print(f"    [OK] {text}")


def print_error(text: str) -> None:
    print(f"    [FAIL] {text}", file=sys.stderr)


def check_prerequisites() -> bool:
    """Check if required files exist."""
    print_step("Checking prerequisites...")

    if not os.path.exists(PATCH_MODULE):
        print_error(f"Patch module not found: {PATCH_MODULE}")
        return False
    print_success(f"Patch module found: {PATCH_MODULE}")

    if not os.path.exists(HOOK_MODULE):
        print_error(f"Hook module not found: {HOOK_MODULE}")
        return False
    print_success(f"Hook module found: {HOOK_MODULE}")

    if not os.path.exists(SITE_PACKAGES):
        print_error(f"site-packages not found: {SITE_PACKAGES}")
        return False
    print_success(f"site-packages found: {SITE_PACKAGES}")

    return True


def install_patch_module() -> bool:
    """Copy the patch module to site-packages."""
    print_step("Installing patch module to site-packages...")

    try:
        shutil.copy2(PATCH_MODULE, TARGET_PATCH)
        print_success(f"Copied to: {TARGET_PATCH}")
        return True
    except Exception as e:
        print_error(f"Failed to copy patch module: {e}")
        return False


def install_hook_module() -> bool:
    """Copy the hook module to CoPaw's hooks directory."""
    print_step("Installing hook module to CoPaw...")

    try:
        os.makedirs(os.path.dirname(TARGET_HOOK), exist_ok=True)
        shutil.copy2(HOOK_MODULE, TARGET_HOOK)
        print_success(f"Copied to: {TARGET_HOOK}")
        return True
    except Exception as e:
        print_error(f"Failed to copy hook module: {e}")
        return False


def install_sync_script() -> bool:
    """Copy the sync script to CoPaw's scripts directory."""
    print_step("Installing sync script...")

    scripts_dir = os.path.join(os.path.dirname(SITE_PACKAGES), "scripts")
    os.makedirs(scripts_dir, exist_ok=True)
    target = os.path.join(scripts_dir, "sync_mempalace.py")

    try:
        shutil.copy2(SYNC_SCRIPT, target)
        print_success(f"Copied to: {target}")
        return True
    except Exception as e:
        print_error(f"Failed to copy sync script: {e}")
        return False


def create_pth_file() -> bool:
    """Create the .pth file to auto-load the patch module."""
    print_step("Creating .pth file for auto-loading...")

    # The .pth file should contain the import statement
    pth_content = f"# CoPaw Mempalace Sync - Auto-load patch\nimport copaw_mempalace_patch\n"

    try:
        with open(TARGET_PTH, "w", encoding="utf-8") as f:
            f.write(pth_content)
        print_success(f"Created: {TARGET_PTH}")
        return True
    except Exception as e:
        print_error(f"Failed to create .pth file: {e}")
        return False


def uninstall() -> bool:
    """Remove the installed files."""
    print_step("Uninstalling...")

    files_to_remove = [
        TARGET_PTH,
        TARGET_PATCH,
        TARGET_HOOK,
    ]

    for f in files_to_remove:
        if os.path.exists(f):
            try:
                os.remove(f)
                print_success(f"Removed: {f}")
            except Exception as e:
                print_error(f"Failed to remove {f}: {e}")

    return True


def main():
    """Main entry point."""
    print_header("CoPaw Mempalace Sync - Persistent Installation")

    # Check for uninstall flag
    if "--uninstall" in sys.argv:
        uninstall()
        print_header("Uninstallation Complete!")
        print("\nRestart CoPaw daemon to apply changes:")
        print("  copaw daemon restart")
        return

    print(f"\nPlugin directory: {PLUGIN_DIR}")
    print(f"Site-packages: {SITE_PACKAGES}")

    # Run installation steps
    steps = [
        ("Check prerequisites", check_prerequisites),
        ("Install patch module", install_patch_module),
        ("Install hook module", install_hook_module),
        ("Install sync script", install_sync_script),
        ("Create .pth file", create_pth_file),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n{'=' * 60}")
            print(f"  Installation failed at: {step_name}")
            print('=' * 60)
            sys.exit(1)

    print_header("Installation Complete!")
    print("""
This installation is PERSISTENT across CoPaw updates!

How it works:
    1. A .pth file in site-packages auto-loads the patch module
    2. The patch module monkey-patches CoPawAgent._register_hooks
    3. No CoPaw source files are modified

Next steps:
    1. Restart CoPaw daemon:
       copaw daemon restart

    2. Test the sync:
       - Have a conversation with your CoPaw agent
       - Check mempalace status:
         mempalace status

To uninstall:
    python install_persistent.py --uninstall

For more information, see README.md
""")


if __name__ == "__main__":
    main()
