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
import json
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
PATCH_MODULE = os.path.join(PLUGIN_DIR, "palace_discovery.py")
HOOK_MODULE = os.path.join(PLUGIN_DIR, "hooks", "mempalace_sync.py")
SYNC_SCRIPT = os.path.join(PLUGIN_DIR, "scripts", "sync_mempalace.py")

# Targets
TARGET_DISCOVERY = os.path.join(SITE_PACKAGES, "palace_discovery.py")
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
        print_error(f"Discovery module not found: {PATCH_MODULE}")
        return False
    print_success(f"Discovery module found: {PATCH_MODULE}")

    if not os.path.exists(HOOK_MODULE):
        print_error(f"Hook module not found: {HOOK_MODULE}")
        return False
    print_success(f"Hook module found: {HOOK_MODULE}")

    if not os.path.exists(SITE_PACKAGES):
        print_error(f"site-packages not found: {SITE_PACKAGES}")
        return False
    print_success(f"site-packages found: {SITE_PACKAGES}")

    return True


def install_discovery_module() -> bool:
    """Copy the discovery module to site-packages."""
    print_step("Installing discovery module to site-packages...")

    try:
        shutil.copy2(PATCH_MODULE, TARGET_DISCOVERY)
        print_success(f"Copied to: {TARGET_DISCOVERY}")
        return True
    except Exception as e:
        print_error(f"Failed to copy discovery module: {e}")
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
    """Create the .pth file to auto-load the discovery module."""
    print_step("Creating .pth file for auto-loading...")

    # The .pth file should contain the import statement
    pth_content = "# CoPaw Mempalace Sync - Auto-load discovery module\nimport palace_discovery\n"

    try:
        with open(TARGET_PTH, "w", encoding="utf-8") as f:
            f.write(pth_content)
        print_success(f"Created: {TARGET_PTH}")
        return True
    except Exception as e:
        print_error(f"Failed to create .pth file: {e}")
        return False


def prompt_configuration() -> None:
    """Prompt user for optional configuration."""
    print_header("Optional Configuration")
    print("""
The plugin can find mempalace automatically, but you can also
configure it explicitly for better reliability.

Options:
  1. Set MEMPALACE_HOME environment variable (system-wide)
  2. Create .mempalace.json in your workspace (per-workspace)
  3. Skip configuration (use auto-discovery)
""")

    choice = input("Choose an option (1/2/3) [3]: ").strip()

    if choice == "1":
        configure_environment_variable()
    elif choice == "2":
        configure_workspace_config()
    else:
        print("\nUsing auto-discovery. You can configure later if needed.")
        print_config_instructions()


def configure_environment_variable() -> None:
    """Guide user to set MEMPALACE_HOME environment variable."""
    print_step("Environment Variable Configuration")
    print("""
To set MEMPALACE_HOME as a SYSTEM environment variable:

Windows:
  1. Open System Properties (Win+Pause)
  2. Click "Advanced system settings"
  3. Click "Environment Variables"
  4. Under "System variables", click "New"
  5. Variable name: MEMPALACE_HOME
  6. Variable value: C:\\Users\\YourName\\.mempalace
     (adjust to your actual mempalace location)

Linux/Mac:
  Add to ~/.bashrc or ~/.zshrc:
    export MEMPALACE_HOME="$HOME/.mempalace"

After setting, restart your terminal/CoPaw daemon.
""")


def configure_workspace_config() -> None:
    """Create .mempalace.json in the workspace."""
    print_step("Workspace Configuration")

    # Try to detect workspace directory
    workspace_dir = os.environ.get(
        "WORKING_DIR",
        os.path.join(os.path.expanduser("~"), ".copaw", "workspaces", "default"),
    )

    print(f"\nWorkspace directory: {workspace_dir}")

    # Try to auto-detect palace location
    default_palace = os.path.join(os.path.expanduser("~"), ".mempalace", "palace")
    palace_input = input(f"Palace directory [{default_palace}]: ").strip()
    palace_dir = palace_input if palace_input else default_palace

    config = {"palace_dir": palace_dir}
    config_file = os.path.join(workspace_dir, ".mempalace.json")

    try:
        os.makedirs(workspace_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        print_success(f"Created: {config_file}")
    except Exception as e:
        print_error(f"Failed to create config: {e}")


def print_config_instructions() -> None:
    """Print configuration instructions for later."""
    print("""
Configuration Options (if auto-discovery doesn't work):

1. Environment Variable:
   Set MEMPALACE_HOME to your mempalace directory (e.g., C:\\Users\\You\\.mempalace)

2. Workspace Config:
   Create .mempalace.json in your workspace:
   {
     "palace_dir": "C:\\Users\\You\\.mempalace\\palace"
   }

3. Or let auto-discovery handle it (it checks common locations).
""")


def uninstall() -> bool:
    """Remove the installed files."""
    print_step("Uninstalling...")

    files_to_remove = [
        TARGET_PTH,
        TARGET_DISCOVERY,
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

    # Check for --no-config flag
    skip_config = "--no-config" in sys.argv

    print(f"\nPlugin directory: {PLUGIN_DIR}")
    print(f"Site-packages: {SITE_PACKAGES}")

    # Run installation steps
    steps = [
        ("Check prerequisites", check_prerequisites),
        ("Install discovery module", install_discovery_module),
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

    # Prompt for configuration unless --no-config
    if not skip_config:
        prompt_configuration()

    print_header("Installation Complete!")
    print("""
This installation is PERSISTENT across CoPaw updates!

How it works:
    1. A .pth file in site-packages auto-loads the discovery module
    2. The discovery module finds your mempalace palace directory
    3. The hook monkey-patches CoPawAgent to add mempalace sync
    4. No CoPaw source files are modified

Palace Discovery Order:
    1. MEMPALACE_HOME environment variable
    2. .mempalace.json in workspace directory
    3. Auto-discovery via pip show
    4. Common installation locations
    5. Default: ~/.mempalace/palace

Next steps:
    1. Restart CoPaw daemon:
       copaw daemon restart

    2. Test the sync:
       - Have a conversation with your CoPaw agent
       - Check mempalace status:
         python -m palace_discovery

To uninstall:
    python install_persistent.py --uninstall

For more information, see README.md
""")


if __name__ == "__main__":
    main()
