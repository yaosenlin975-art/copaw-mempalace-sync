#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CoPaw Mempalace Sync Plugin Installer
======================================
This script installs the MempalaceSyncHook into your CoPaw installation.

What it does:
    1. Copies the hook to CoPaw's hooks directory
    2. Updates hooks/__init__.py to export the new hook
    3. Patches react_agent.py to register the hook
    4. Creates the sync script in CoPaw's scripts directory

Usage:
    python install.py

Requirements:
    - Python 3.10+
    - CoPaw installed
    - MemPalace installed (pip install mempalace)
"""

import os
import sys
import shutil
from pathlib import Path

# CoPaw installation path (auto-detected)
COPAW_INSTALL_DIR = os.path.join(
    os.path.dirname(sys.executable),
    "Lib",
    "site-packages",
    "copaw",
)

# Plugin directory (where this script is located)
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print('=' * 60)


def print_step(text: str) -> None:
    """Print a step message."""
    print(f"\n>>> {text}")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"    ✓ {text}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"    ✗ {text}", file=sys.stderr)


def check_prerequisites() -> bool:
    """Check if CoPaw and MemPalace are installed."""
    print_step("Checking prerequisites...")

    # Check CoPaw
    if not os.path.exists(COPAW_INSTALL_DIR):
        print_error(f"CoPaw not found at: {COPAW_INSTALL_DIR}")
        print("Please set COPAW_INSTALL_DIR environment variable or modify this script.")
        return False
    print_success(f"CoPaw found: {COPAW_INSTALL_DIR}")

    # Check hooks directory
    hooks_dir = os.path.join(COPAW_INSTALL_DIR, "agents", "hooks")
    if not os.path.exists(hooks_dir):
        print_error(f"Hooks directory not found: {hooks_dir}")
        return False
    print_success(f"Hooks directory found: {hooks_dir}")

    return True


def install_hook() -> bool:
    """Install the hook file."""
    print_step("Installing MempalaceSyncHook...")

    src = os.path.join(PLUGIN_DIR, "hooks", "mempalace_sync.py")
    dst = os.path.join(COPAW_INSTALL_DIR, "agents", "hooks", "mempalace_sync.py")

    if not os.path.exists(src):
        print_error(f"Hook source not found: {src}")
        return False

    try:
        shutil.copy2(src, dst)
        print_success(f"Copied hook to: {dst}")
        return True
    except Exception as e:
        print_error(f"Failed to copy hook: {e}")
        return False


def update_hooks_init() -> bool:
    """Update hooks/__init__.py to export MempalaceSyncHook."""
    print_step("Updating hooks/__init__.py...")

    init_file = os.path.join(COPAW_INSTALL_DIR, "agents", "hooks", "__init__.py")

    if not os.path.exists(init_file):
        print_error(f"hooks/__init__.py not found: {init_file}")
        return False

    try:
        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if already installed
        if "MempalaceSyncHook" in content:
            print_success("MempalaceSyncHook already exported in __init__.py")
            return True

        # Add import
        import_line = "from .mempalace_sync import MempalaceSyncHook"
        if import_line not in content:
            content = content.replace(
                "from .memory_compaction import MemoryCompactionHook",
                "from .memory_compaction import MemoryCompactionHook\n" + import_line,
            )

        # Add to __all__
        if '"MempalaceSyncHook"' not in content:
            content = content.replace(
                '"MemoryCompactionHook",\n]',
                '"MemoryCompactionHook",\n    "MempalaceSyncHook",\n]',
            )

        with open(init_file, "w", encoding="utf-8") as f:
            f.write(content)

        print_success("Updated hooks/__init__.py")
        return True

    except Exception as e:
        print_error(f"Failed to update __init__.py: {e}")
        return False


def patch_react_agent() -> bool:
    """Patch react_agent.py to register the hook."""
    print_step("Patching react_agent.py...")

    react_agent_file = os.path.join(COPAW_INSTALL_DIR, "agents", "react_agent.py")

    if not os.path.exists(react_agent_file):
        print_error(f"react_agent.py not found: {react_agent_file}")
        return False

    try:
        with open(react_agent_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Check if already patched
        if "MempalaceSyncHook" in content:
            print_success("react_agent.py already patched")
            return True

        # Add import
        content = content.replace(
            "from .hooks import BootstrapHook, MemoryCompactionHook",
            "from .hooks import BootstrapHook, MemoryCompactionHook, MempalaceSyncHook",
        )

        # Add hook registration (after memory compaction hook)
        hook_registration = '''
        # Mempalace sync hook - auto-sync conversations to mempalace
        mempalace_sync_hook = MempalaceSyncHook(
            workspace_dir=working_dir,
        )
        self.register_instance_hook(
            hook_type="post_reply",
            hook_name="mempalace_sync_hook",
            hook=mempalace_sync_hook.__call__,
        )
        logger.debug("Registered mempalace sync hook")
'''

        # Find the end of memory compaction hook registration
        marker = 'logger.debug("Registered memory compaction hook")'
        if marker in content:
            content = content.replace(
                marker,
                marker + hook_registration,
            )
        else:
            print_error("Could not find insertion point in react_agent.py")
            return False

        with open(react_agent_file, "w", encoding="utf-8") as f:
            f.write(content)

        print_success("Patched react_agent.py")
        return True

    except Exception as e:
        print_error(f"Failed to patch react_agent.py: {e}")
        return False


def install_sync_script() -> bool:
    """Install the sync script to CoPaw's scripts directory."""
    print_step("Installing sync script...")

    scripts_dir = os.path.join(os.path.dirname(COPAW_INSTALL_DIR), "..", "..", "scripts")
    os.makedirs(scripts_dir, exist_ok=True)

    src = os.path.join(PLUGIN_DIR, "scripts", "sync_mempalace.py")
    dst = os.path.join(scripts_dir, "sync_mempalace.py")

    if not os.path.exists(src):
        print_error(f"Sync script not found: {src}")
        return False

    try:
        shutil.copy2(src, dst)
        print_success(f"Copied sync script to: {dst}")
        return True
    except Exception as e:
        print_error(f"Failed to copy sync script: {e}")
        return False


def main():
    """Main installer entry point."""
    print_header("CoPaw Mempalace Sync Plugin Installer")

    print(f"\nPlugin directory: {PLUGIN_DIR}")
    print(f"CoPaw install dir: {COPAW_INSTALL_DIR}")

    # Run installation steps
    steps = [
        ("Check prerequisites", check_prerequisites),
        ("Install hook", install_hook),
        ("Update hooks/__init__.py", update_hooks_init),
        ("Patch react_agent.py", patch_react_agent),
        ("Install sync script", install_sync_script),
    ]

    for step_name, step_func in steps:
        if not step_func():
            print(f"\n{'=' * 60}")
            print(f"  Installation failed at: {step_name}")
            print('=' * 60)
            sys.exit(1)

    print_header("Installation Complete!")
    print("""
Next steps:
    1. Restart CoPaw daemon:
       copaw daemon restart

    2. Test the sync:
       - Have a conversation with your CoPaw agent
       - Check mempalace status:
         mempalace status

    3. Search your memories:
       mempalace search "your query"

For more information, see README.md
""")


if __name__ == "__main__":
    main()
