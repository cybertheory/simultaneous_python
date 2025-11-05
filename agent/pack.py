"""Agent packaging utilities."""

import os
import tarfile
import tempfile
from pathlib import Path
from typing import Any

from simultaneous.agent.spec import AgentSpec, RuntimeSpec, EntrypointSpec, SpecError


def pack_agent(
    agent_dir: Path | str,
    output_path: Path | str | None = None,
    spec_path: Path | str | None = None,
) -> Path:
    """
    Pack an agent directory into a tar.gz bundle.
    
    Args:
        agent_dir: Directory containing the agent code
        output_path: Output path for tar.gz (defaults to temp file)
        spec_path: Path to sim.yaml (defaults to agent_dir/sim.yaml)
        
    Returns:
        Path to the created tar.gz file
        
    Raises:
        SpecError: If sim.yaml is missing or invalid
    """
    agent_dir = Path(agent_dir)
    if not agent_dir.exists():
        raise SpecError(f"Agent directory not found: {agent_dir}")
    
    # Find or create spec
    if spec_path:
        spec_path = Path(spec_path)
    else:
        spec_path = agent_dir / "sim.yaml"
    
    if not spec_path.exists():
        # Auto-generate minimal spec if missing
        spec = _generate_default_spec(agent_dir)
    else:
        spec = AgentSpec.from_file(spec_path)
    
    # Create output path
    if output_path:
        output_path = Path(output_path)
    else:
        output_file = tempfile.NamedTemporaryFile(
            suffix=".tar.gz",
            delete=False,
        )
        output_path = Path(output_file.name)
        output_file.close()
    
    # Create tar.gz
    with tarfile.open(output_path, "w:gz") as tar:
        # Add sim.yaml
        tar.add(spec_path, arcname="sim.yaml")
        
        # Add all files in agent_dir (excluding common ignores)
        ignore_patterns = {
            ".git",
            "__pycache__",
            "*.pyc",
            ".env",
            "*.egg-info",
            "dist",
            "build",
            ".pytest_cache",
        }
        
        for root, dirs, files in os.walk(agent_dir):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns]
            
            for file in files:
                if any(file.endswith(pattern) for pattern in ignore_patterns):
                    continue
                
                file_path = Path(root) / file
                arcname = file_path.relative_to(agent_dir)
                tar.add(file_path, arcname=str(arcname))
    
    return output_path


def _generate_default_spec(agent_dir: Path) -> AgentSpec:
    """Generate a minimal default spec if sim.yaml is missing."""
    # Try to find main.py or similar entrypoint
    entrypoint_candidates = ["main.py", "app.py", "index.py"]
    entrypoint = None
    
    for candidate in entrypoint_candidates:
        if (agent_dir / candidate).exists():
            entrypoint = ["python", candidate]
            break
    
    if not entrypoint:
        # Default fallback
        entrypoint = ["python", "-m", "main"]
    
    return AgentSpec(
        name=agent_dir.name,
        version="1.0.0",
        description="Auto-generated agent spec",
        runtime=RuntimeSpec(
            type="browser",
            provider="auto",
            region="auto",
        ),
        entrypoint=EntrypointSpec(
            command=entrypoint,
        ),
        inputs=[],
        outputs=[],
    )

