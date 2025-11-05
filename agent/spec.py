"""Agent specification (sim.yaml) models."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator


class RuntimeSpec(BaseModel):
    """Runtime specification from sim.yaml."""
    
    type: str = Field(..., description="Runtime type: browser, desktop, sandbox")
    provider: str = Field(default="auto", description="Provider: auto, browserbase, self")
    region: str = Field(default="auto", description="Region for provider")
    
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate runtime type."""
        valid_types = {"browser", "desktop", "sandbox"}
        if v not in valid_types:
            raise ValueError(f"Invalid runtime type '{v}'. Must be one of: {valid_types}")
        return v


class EntrypointSpec(BaseModel):
    """Entrypoint specification from sim.yaml."""
    
    command: list[str] = Field(..., description="Command to run (e.g., ['python', 'main.py'])")
    args: list[str] = Field(default_factory=list, description="Additional arguments")


class InputSpec(BaseModel):
    """Input parameter specification."""
    
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type: string, number, boolean, json")
    default: Any = Field(default=None, description="Default value (optional)")
    description: str = Field(default="", description="Parameter description")


class OutputSpec(BaseModel):
    """Output specification."""
    
    name: str = Field(..., description="Output name")
    type: str = Field(..., description="Output type: string, number, boolean, json")


class AgentSpec(BaseModel):
    """Complete agent specification from sim.yaml."""
    
    name: str = Field(..., description="Agent name")
    version: str = Field(default="1.0.0", description="Agent version")
    description: str = Field(default="", description="Agent description")
    runtime: RuntimeSpec = Field(..., description="Runtime configuration")
    entrypoint: EntrypointSpec = Field(..., description="Entrypoint command")
    inputs: list[InputSpec] = Field(default_factory=list, description="Input parameters")
    outputs: list[OutputSpec] = Field(default_factory=list, description="Output definitions")
    secrets: list[str] = Field(default_factory=list, description="Secret names required")
    permissions: dict[str, Any] = Field(default_factory=dict, description="Permission requirements")
    timeouts: dict[str, int] = Field(default_factory=dict, description="Timeout settings")
    
    @classmethod
    def from_file(cls, path: Path | str) -> "AgentSpec":
        """
        Load agent spec from sim.yaml file.
        
        Args:
            path: Path to sim.yaml file
            
        Returns:
            AgentSpec instance
            
        Raises:
            FileNotFoundError: If sim.yaml doesn't exist
            ValueError: If sim.yaml is invalid
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Agent spec not found: {path}")
        
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        
        if not data:
            raise ValueError(f"Empty or invalid sim.yaml: {path}")
        
        try:
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Invalid agent spec: {e}") from e
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentSpec":
        """Create AgentSpec from dictionary."""
        return cls(**data)
    
    def to_file(self, path: Path | str, metadata: dict[str, Any] | None = None) -> None:
        """Save agent spec to sim.yaml file.
        
        Args:
            path: Path to sim.yaml file (will be created or overwritten)
            metadata: Optional metadata dict to include (for API tracking info)
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict, excluding None values
        data = self.model_dump(exclude_none=False)
        
        # Convert nested models to dicts
        yaml_data = {
            "name": data["name"],
            "version": data.get("version", "1.0.0"),
            "description": data.get("description", ""),
            "runtime": {
                "type": data["runtime"]["type"],
                "provider": data["runtime"].get("provider", "auto"),
                "region": data["runtime"].get("region", "auto"),
            },
            "entrypoint": {
                "command": data["entrypoint"]["command"],
                "args": data["entrypoint"].get("args", []),
            },
            "inputs": [
                {
                    "name": i["name"],
                    "type": i["type"],
                    "default": i.get("default"),
                    "description": i.get("description", ""),
                }
                for i in data.get("inputs", [])
            ],
            "outputs": [
                {"name": o["name"], "type": o["type"]}
                for o in data.get("outputs", [])
            ],
            "secrets": data.get("secrets", []),
            "permissions": data.get("permissions", {}),
            "timeouts": data.get("timeouts", {}),
        }
        
        # Add metadata section if provided
        if metadata:
            yaml_data["metadata"] = metadata
        
        with open(path, "w") as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


class SpecError(RuntimeError):
    """Raised when agent spec is invalid."""
    pass







