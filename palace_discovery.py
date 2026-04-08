# -*- coding: utf-8 -*-
"""
MemPalace Discovery Module
==========================
Finds the MemPalace palace directory using multiple strategies:
1. Environment variable: MEMPALACE_HOME
2. Workspace config: .mempalace.json in working directory
3. Auto-discovery: via pip show or common locations
4. Default: ~/.mempalace/palace

This module is used by both the hook and the sync script.
"""

import os
import json
import subprocess
import shutil
from typing import Optional


def find_palace_dir(working_dir: Optional[str] = None) -> str:
    """Find the MemPalace palace directory.

    Search order:
    1. MEMPALACE_HOME environment variable
    2. .mempalace.json in working directory
    3. Auto-discovery via pip show mempalace
    4. Common installation locations
    5. Default: ~/.mempalace/palace

    Args:
        working_dir: The working directory to check for config.
                    If None, uses current directory.

    Returns:
        The path to the palace directory.
    """
    # 1. Environment variable (highest priority)
    env_home = os.environ.get("MEMPALACE_HOME")
    if env_home:
        palace_dir = os.path.join(env_home, "palace")
        if os.path.exists(palace_dir):
            return palace_dir
        # Maybe MEMPALACE_HOME points directly to palace
        if os.path.exists(env_home) and os.path.exists(
            os.path.join(env_home, "drawers")
        ):
            return env_home

    # 2. Workspace config file
    if working_dir is None:
        working_dir = os.getcwd()

    config_file = os.path.join(working_dir, ".mempalace.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            palace_dir = config.get("palace_dir")
            if palace_dir and os.path.exists(palace_dir):
                return palace_dir
        except (json.JSONDecodeError, IOError):
            pass

    # 3. Auto-discovery via pip show
    discovered = _discover_via_pip()
    if discovered:
        return discovered

    # 4. Common installation locations
    common_locations = _get_common_locations()
    for loc in common_locations:
        if os.path.exists(loc) and os.path.exists(os.path.join(loc, "drawers")):
            return loc

    # 5. Default location
    default = os.path.join(os.path.expanduser("~"), ".mempalace", "palace")
    return default


def _discover_via_pip() -> Optional[str]:
    """Try to find mempalace installation via pip show."""
    try:
        # Find Python with mempalace installed
        python_path = _find_mempalace_python()
        if not python_path:
            return None

        result = subprocess.run(
            [python_path, "-m", "pip", "show", "mempalace"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )

        if result.returncode != 0:
            return None

        # Parse Location from pip show output
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                location = line.split(":", 1)[1].strip()
                # mempalace typically creates palace in ~/.mempalace/palace
                # But we can check if there's a palace in the install location
                possible_palace = os.path.join(
                    os.path.expanduser("~"), ".mempalace", "palace"
                )
                if os.path.exists(possible_palace):
                    return possible_palace
                break

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def _get_common_locations() -> list[str]:
    """Get common mempalace installation locations."""
    home = os.path.expanduser("~")
    return [
        os.path.join(home, ".mempalace", "palace"),
        os.path.join(home, "mempalace", "palace"),
        os.path.join(home, ".local", "share", "mempalace", "palace"),
        # Windows specific
        os.path.join(home, "AppData", "Local", "mempalace", "palace"),
        os.path.join(home, "AppData", "Roaming", "mempalace", "palace"),
    ]


def _find_mempalace_python() -> Optional[str]:
    """Find Python executable with mempalace installed.

    Searches in order:
    1. MEMPALACE_VENV environment variable
    2. WORKING_DIR/.venv
    3. Common venv locations
    4. System python
    """
    # Check environment variable
    venv_path = os.environ.get("MEMPALACE_VENV")
    if venv_path:
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        if os.path.exists(python_exe):
            return python_exe
        python_exe = os.path.join(venv_path, "bin", "python")
        if os.path.exists(python_exe):
            return python_exe

    # Check working directory venv
    working_dir = os.environ.get("WORKING_DIR")
    if working_dir:
        venv_python = os.path.join(working_dir, ".venv", "Scripts", "python.exe")
        if os.path.exists(venv_python):
            return venv_python
        venv_python = os.path.join(working_dir, ".venv", "bin", "python")
        if os.path.exists(venv_python):
            return venv_python

    # Check if python/mempalace is in PATH
    if shutil.which("python"):
        return "python"

    return None


def get_palace_status() -> dict:
    """Get status information about the palace discovery.

    Returns:
        dict with discovery results and debug info.
    """
    working_dir = os.environ.get("WORKING_DIR", os.getcwd())
    palace_dir = find_palace_dir(working_dir)

    return {
        "palace_dir": palace_dir,
        "exists": os.path.exists(palace_dir),
        "has_drawers": os.path.exists(os.path.join(palace_dir, "drawers")),
        "env_home": os.environ.get("MEMPALACE_HOME"),
        "config_file": os.path.join(working_dir, ".mempalace.json"),
        "config_exists": os.path.exists(os.path.join(working_dir, ".mempalace.json")),
    }


if __name__ == "__main__":
    # CLI mode: print discovered palace directory
    status = get_palace_status()
    print(f"Palace directory: {status['palace_dir']}")
    print(f"Exists: {status['exists']}")
    print(f"Has drawers: {status['has_drawers']}")
    if status["env_home"]:
        print(f"MEMPALACE_HOME: {status['env_home']}")
    print(f"Config file: {status['config_file']} (exists: {status['config_exists']})")
