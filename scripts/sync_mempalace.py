#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mempalace Sync Script for CoPaw
================================
Syncs CoPaw conversation sessions to MemPalace palace.

This script is designed to be called by MempalaceSyncHook after each reply.
It extracts the latest session, converts it to conversation format, and
imports it into MemPalace.

Environment variables:
    WORKSPACE_DIR: The workspace directory (default: ~/.copaw/workspaces/default)
    PALACE_DIR: The mempalace palace directory (auto-discovered if not set)
    MEMPALACE_HOME: Home directory of mempalace installation (optional)
    MEMPALACE_VENV: Path to mempalace venv python (optional, auto-detected)

Requirements:
    - Python 3.10+
    - mempalace installed (pip install mempalace)
"""

import os
import sys
import json
import glob
import tempfile
import subprocess
from datetime import datetime
from pathlib import Path


def get_workspace_dir() -> str:
    """Get the workspace directory."""
    return os.environ.get(
        "WORKSPACE_DIR",
        os.path.join(os.path.expanduser("~"), ".copaw", "workspaces", "default"),
    )


def get_palace_dir() -> str:
    """Get the mempalace palace directory using discovery."""
    # First check if explicitly set via environment
    palace_dir = os.environ.get("PALACE_DIR")
    if palace_dir and os.path.exists(palace_dir):
        return palace_dir

    # Use discovery module
    try:
        # Try to find discovery module relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        discovery_path = os.path.join(script_dir, "..", "palace_discovery.py")

        if os.path.exists(discovery_path):
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "palace_discovery", discovery_path
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.find_palace_dir(get_workspace_dir())
    except Exception as e:
        print(f"Discovery module error: {e}", file=sys.stderr)

    # Fallback to environment variable or default
    env_home = os.environ.get("MEMPALACE_HOME")
    if env_home:
        return os.path.join(env_home, "palace")

    return os.path.join(os.path.expanduser("~"), ".mempalace", "palace")


def find_mempalace_python() -> str | None:
    """Find mempalace python executable.

    Searches in order:
    1. MEMPALACE_VENV environment variable
    2. Common venv locations relative to workspace
    3. System python (if mempalace is installed globally)
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

    # Auto-detect from workspace
    workspace_dir = get_workspace_dir()
    common_venv_paths = [
        os.path.join(workspace_dir, ".venv", "Scripts", "python.exe"),
        os.path.join(workspace_dir, "venv", "Scripts", "python.exe"),
        os.path.join(os.path.dirname(workspace_dir), ".venv", "Scripts", "python.exe"),
        # Linux/Mac
        os.path.join(workspace_dir, ".venv", "bin", "python"),
        os.path.join(workspace_dir, "venv", "bin", "python"),
    ]

    for path in common_venv_paths:
        if os.path.exists(path):
            return path

    # Fall back to system python
    return "python"


def get_latest_session_file(workspace_dir: str) -> str | None:
    """Get the most recently modified session file."""
    sessions_dir = os.path.join(workspace_dir, "sessions")
    if not os.path.exists(sessions_dir):
        return None

    session_files = glob.glob(os.path.join(sessions_dir, "*.json"))
    if not session_files:
        return None

    # Sort by modification time, newest first
    session_files.sort(key=os.path.getmtime, reverse=True)
    return session_files[0]


def extract_text_content(content: list | str) -> str:
    """Extract text from content (can be string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    texts.append(block.get("text", ""))
                elif block.get("type") == "thinking":
                    # Skip thinking blocks
                    pass
            elif isinstance(block, str):
                texts.append(block)
        return " ".join(texts)
    return str(content)


def session_to_conv_format(session_file: str) -> str | None:
    """Convert a CoPaw session file to mempalace conversation format.

    Returns the path to the temporary conversation file, or None if conversion fails.
    """
    try:
        with open(session_file, "r", encoding="utf-8") as f:
            session_data = json.load(f)

        # Extract messages from session (CoPaw format: agent.memory.content)
        memory = session_data.get("agent", {}).get("memory", {})
        content = memory.get("content", [])
        if not content:
            return None

        # Convert to mempalace convo format
        # Format: alternating Human: and Assistant: messages
        conv_lines = []
        for item in content:
            if not isinstance(item, list) or len(item) == 0:
                continue
            # Each item is [msg, ...] where msg has role and content
            msg = item[0] if isinstance(item, list) else item
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "")
            raw_content = msg.get("content", "")
            text = extract_text_content(raw_content)

            if not text:
                continue

            if role == "user":
                conv_lines.append(f"Human: {text}")
            elif role == "assistant":
                conv_lines.append(f"Assistant: {text}")

        if not conv_lines:
            return None

        # Create temporary file
        session_name = Path(session_file).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_file = os.path.join(
            tempfile.gettempdir(),
            f"copaw_session_{session_name}_{timestamp}.txt",
        )

        with open(temp_file, "w", encoding="utf-8") as f:
            f.write("\n\n".join(conv_lines))

        return temp_file

    except Exception as e:
        print(f"Error converting session: {e}", file=sys.stderr)
        return None


def mine_to_mempalace(conv_file: str, palace_dir: str, python_path: str) -> bool:
    """Mine a conversation file to mempalace."""
    try:
        # Create a temp directory for the conversation
        temp_dir = os.path.join(tempfile.gettempdir(), f"mempalace_conv_{os.getpid()}")
        os.makedirs(temp_dir, exist_ok=True)

        # Move the conversation file to temp dir
        dest_file = os.path.join(temp_dir, Path(conv_file).name)
        os.rename(conv_file, dest_file)

        # Run mempalace init and mine
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # Initialize the directory
        init_result = subprocess.run(
            [python_path, "-m", "mempalace", "init", temp_dir, "--yes"],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )

        if init_result.returncode != 0:
            print(f"Init failed: {init_result.stderr}", file=sys.stderr)
            return False

        # Mine the conversation
        mine_result = subprocess.run(
            [
                python_path,
                "-m",
                "mempalace",
                "mine",
                temp_dir,
                "--mode",
                "convos",
                "--wing",
                "copaw_sessions",
            ],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )

        # Cleanup
        try:
            os.remove(dest_file)
            os.rmdir(temp_dir)
        except Exception:
            pass

        if mine_result.returncode == 0:
            return True
        else:
            print(f"Mine failed: {mine_result.stderr}", file=sys.stderr)
            return False

    except Exception as e:
        print(f"Error mining to mempalace: {e}", file=sys.stderr)
        return False


def main():
    """Main entry point."""
    workspace_dir = get_workspace_dir()
    palace_dir = get_palace_dir()
    python_path = find_mempalace_python()

    # Debug info (only shown if PALACE_DIR was not explicitly set)
    if not os.environ.get("PALACE_DIR"):
        print(f"Discovered palace: {palace_dir}", file=sys.stderr)

    # Get latest session file
    session_file = get_latest_session_file(workspace_dir)
    if not session_file:
        print("No session files found", file=sys.stderr)
        sys.exit(0)  # Not an error, just nothing to sync

    # Convert to convo format
    conv_file = session_to_conv_format(session_file)
    if not conv_file:
        print("Failed to convert session", file=sys.stderr)
        sys.exit(1)

    # Mine to mempalace
    success = mine_to_mempalace(conv_file, palace_dir, python_path)

    if success:
        print("Sync completed successfully")
        sys.exit(0)
    else:
        print("Sync failed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
