# -*- coding: utf-8 -*-
"""
CoPaw Mempalace Sync Hook
=========================
A post_reply hook that automatically syncs CoPaw conversations to MemPalace.

This hook triggers after each assistant reply, exporting the latest session
and importing it into MemPalace for persistent memory across sessions.

Usage:
    This hook is registered automatically when installed via the installer.
"""

import logging
import os
import subprocess
import asyncio
from typing import TYPE_CHECKING, Any

from agentscope.agent import ReActAgent
from agentscope.message import Msg

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class MempalaceSyncHook:
    """Hook for syncing conversations to mempalace after each reply.

    This hook runs asynchronously in the background to avoid blocking
    the main conversation flow.

    Attributes:
        workspace_dir: The workspace directory containing sessions.
        palace_dir: The mempalace palace directory (auto-discovered).
        sync_script: Path to the sync script.
    """

    def __init__(
        self,
        workspace_dir: str,
        palace_dir: str | None = None,
        sync_script: str | None = None,
    ):
        """Initialize mempalace sync hook.

        Args:
            workspace_dir: The workspace directory containing sessions.
            palace_dir: The mempalace palace directory (optional, auto-discovered if None).
            sync_script: Path to the sync script (optional).
        """
        self.workspace_dir = workspace_dir

        # Auto-discover palace directory if not specified
        if palace_dir:
            self.palace_dir = palace_dir
        else:
            self.palace_dir = self._discover_palace_dir()

        # Determine sync script path
        if sync_script:
            self.sync_script = sync_script
        else:
            # Default: look in plugin's scripts directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.sync_script = os.path.join(plugin_dir, "scripts", "sync_mempalace.py")

    def _discover_palace_dir(self) -> str:
        """Discover the palace directory using multiple strategies."""
        # Try to import the discovery module
        try:
            # First try from the plugin directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            discovery_path = os.path.join(plugin_dir, "palace_discovery.py")

            if os.path.exists(discovery_path):
                import importlib.util

                spec = importlib.util.spec_from_file_location(
                    "palace_discovery", discovery_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    return module.find_palace_dir(self.workspace_dir)
        except Exception as e:
            logger.debug(f"Failed to import discovery module: {e}")

        # Fallback: use environment variable or default
        env_home = os.environ.get("MEMPALACE_HOME")
        if env_home:
            return os.path.join(env_home, "palace")

        return os.path.join(os.path.expanduser("~"), ".mempalace", "palace")

    async def __call__(
        self,
        agent: ReActAgent,
        kwargs: dict[str, Any],
        output: Msg,
    ) -> Msg | None:
        """Post-reply hook to sync conversation to mempalace.

        Args:
            agent: The agent instance.
            kwargs: The reply function arguments.
            output: The output message from the agent.

        Returns:
            None (doesn't modify the output message).
        """
        try:
            # Run sync in background to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._sync_conversation,
            )
        except Exception as e:
            logger.warning(f"Failed to sync to mempalace: {e}")

        return None  # Don't modify the output message

    def _sync_conversation(self) -> None:
        """Execute the mempalace sync script."""
        try:
            # Check if sync script exists
            if not os.path.exists(self.sync_script):
                logger.debug(f"Sync script not found: {self.sync_script}")
                return

            # Run the sync script
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["WORKSPACE_DIR"] = self.workspace_dir
            env["PALACE_DIR"] = self.palace_dir

            result = subprocess.run(
                ["python", self.sync_script],
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

            if result.returncode == 0:
                logger.debug(f"Mempalace sync completed: {result.stdout.strip()}")
            else:
                logger.warning(f"Mempalace sync failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.warning("Mempalace sync timed out")
        except Exception as e:
            logger.warning(f"Mempalace sync error: {e}")
