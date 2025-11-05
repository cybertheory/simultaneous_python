"""Local agent runner (for development/testing)."""

import asyncio
import os
import subprocess
from pathlib import Path
from typing import Any

from simultaneous.agent.spec import AgentSpec


class LocalRunner:
    """Runner for executing agents locally (development only)."""
    
    def __init__(self, agent_dir: Path | str):
        """
        Initialize local runner.
        
        Args:
            agent_dir: Directory containing agent code and sim.yaml
        """
        self.agent_dir = Path(agent_dir)
        self.spec = AgentSpec.from_file(self.agent_dir / "sim.yaml")
    
    async def run(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Run the agent locally.
        
        Args:
            params: Input parameters for the agent
            
        Returns:
            Output dictionary
        """
        params = params or {}
        
        # Set up environment
        env = os.environ.copy()
        for key, value in params.items():
            env[key.upper()] = str(value)
        
        # Build command
        cmd = self.spec.entrypoint.command + self.spec.entrypoint.args
        
        # Run in agent directory
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.agent_dir),
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "exitCode": process.returncode,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else "",
        }

