# -*- coding: utf-8 -*-
"""
CoPaw Mempalace Sync - Monkey Patch Module
===========================================
This module patches CoPawAgent._register_hooks to add MempalaceSyncHook
without modifying CoPaw source code.

This file should be loaded via a .pth file in site-packages.
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)

# Store the original method
_original_register_hooks = None
_patched = False


def _patched_register_hooks(self):
    """Patched _register_hooks that adds MempalaceSyncHook."""
    # Call original method first
    if _original_register_hooks is not None:
        _original_register_hooks(self)

    # Add our mempalace sync hook
    try:
        from .hooks.mempalace_sync import MempalaceSyncHook

        working_dir = (
            self._workspace_dir
            if hasattr(self, "_workspace_dir") and self._workspace_dir
            else os.getcwd()
        )

        mempalace_sync_hook = MempalaceSyncHook(
            workspace_dir=working_dir,
        )
        self.register_instance_hook(
            hook_type="post_reply",
            hook_name="mempalace_sync_hook",
            hook=mempalace_sync_hook.__call__,
        )
        logger.debug("Registered mempalace sync hook (via monkey patch)")
    except Exception as e:
        logger.warning(f"Failed to register mempalace sync hook: {e}")


def apply_patch():
    """Apply the monkey patch to CoPawAgent."""
    global _original_register_hooks, _patched

    if _patched:
        return

    try:
        from copaw.agents.react_agent import CoPawAgent

        _original_register_hooks = CoPawAgent._register_hooks
        CoPawAgent._register_hooks = _patched_register_hooks
        _patched = True
        logger.info("CoPaw Mempalace Sync hook patch applied")
    except ImportError:
        # CoPaw not yet loaded, will retry later
        logger.debug("CoPaw not yet loaded, patch will be applied later")
    except Exception as e:
        logger.warning(f"Failed to apply mempalace sync patch: {e}")


# Try to apply patch immediately
apply_patch()

# Also hook into importlib to apply patch when CoPaw is imported
import importlib
import importlib.util

_original_import = __builtins__.__import__


def _patched_import(name, *args, **kwargs):
    """Intercept imports to apply patch when CoPaw is loaded."""
    result = _original_import(name, *args, **kwargs)

    if name == "copaw.agents.react_agent" and not _patched:
        apply_patch()

    return result


# Only apply import hook if not already patched
if not _patched:
    __builtins__.__import__ = _patched_import
