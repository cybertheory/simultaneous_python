"""Tests for agent specification."""

import tempfile
from pathlib import Path

import pytest

from simultaneous.agent.spec import AgentSpec, SpecError


def test_load_valid_spec() -> None:
    """Test loading a valid sim.yaml."""
    spec_yaml = """
name: test-agent
version: 1.0.0
description: Test agent
runtime:
  type: browser
  provider: browserbase
  region: sfo
entrypoint:
  command: ["python", "main.py"]
inputs:
  - name: query
    type: string
outputs:
  - name: result
    type: json
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(spec_yaml)
        spec_path = Path(f.name)
    
    try:
        spec = AgentSpec.from_file(spec_path)
        assert spec.name == "test-agent"
        assert spec.version == "1.0.0"
        assert spec.runtime.type == "browser"
        assert spec.runtime.provider == "browserbase"
        assert len(spec.inputs) == 1
        assert spec.inputs[0].name == "query"
    finally:
        spec_path.unlink()


def test_load_missing_file() -> None:
    """Test loading a non-existent spec raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        AgentSpec.from_file(Path("/nonexistent/sim.yaml"))


def test_invalid_runtime_type() -> None:
    """Test invalid runtime type raises error."""
    spec_yaml = """
name: test-agent
version: 1.0.0
runtime:
  type: invalid
  provider: browserbase
entrypoint:
  command: ["python", "main.py"]
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(spec_yaml)
        spec_path = Path(f.name)
    
    try:
        with pytest.raises(ValueError):
            AgentSpec.from_file(spec_path)
    finally:
        spec_path.unlink()


def test_default_values() -> None:
    """Test default values in spec."""
    spec_yaml = """
name: test-agent
version: 1.0.0
runtime:
  type: browser
entrypoint:
  command: ["python", "main.py"]
"""
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(spec_yaml)
        spec_path = Path(f.name)
    
    try:
        spec = AgentSpec.from_file(spec_path)
        assert spec.runtime.provider == "auto"
        assert spec.runtime.region == "auto"
        assert spec.inputs == []
        assert spec.outputs == []
    finally:
        spec_path.unlink()





