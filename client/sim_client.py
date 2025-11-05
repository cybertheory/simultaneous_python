"""Main Simultaneous client."""

import inspect
import os
from typing import Any, Callable

import httpx

from simultaneous.agent.spec import AgentSpec
from simultaneous.runtime.base import Runtime
from simultaneous.runtime.browser import Browser
from simultaneous.client.browser import BrowserClient
from simultaneous.browsers import Browsers
from simultaneous.client.llms import Models
from simultaneous.runtime.base import RuntimeKind
from simultaneous.providers.router import get_adapter
from simultaneous.client.runs import RunManager
from simultaneous.client.logs import LogManager
from simultaneous.client.workflows import WorkflowManager
from simultaneous.utils.env import get_env


class SimClient:
    """
    Main client for Simultaneous SDK.
    
    Example:
        ```python
        from simultaneous import SimClient, Browser
        
        client = SimClient(api_key="SIM_...")
        
        @client.agent(name="scrape-jobs", runtime=Browser())
        async def scrape_jobs(query: str) -> list[dict]:
            ...
        
        run_id = await client.run("scrape-jobs", params={"query": "sap payroll"}, parallel=50)
        await client.logs.stream(run_id)
        res = await client.runs.wait(run_id)
        ```
    """
    
    # API base URL
    API_BASE_URL = os.getenv("SIMULTANEOUS_API_URL", "https://api.simultaneous.live")
    
    def __init__(
        self,
        api_key: str | None = None,
        default_runtime: Runtime | None = None,
        api_url: str | None = None,
        project_id: str | None = None,
    ):
        """
        Initialize Simultaneous client.
        
        Args:
            api_key: Simultaneous API key (optional for MVP)
            default_runtime: Default runtime to use (defaults to Browser())
            api_url: Simultaneous API base URL (defaults to https://api.simultaneous.live)
        """
        self.api_key = api_key or get_env("SIMULTANEOUS_API_KEY")
        self.api_url = (api_url or self.API_BASE_URL).rstrip("/")
        self.default_runtime = default_runtime or Browser()
        self.project_id = project_id or get_env("SIMULTANEOUS_PROJECT_ID")
        
        # Initialize HTTP client for API calls
        self._http_client: httpx.AsyncClient | None = None
        
        # Initialize managers
        self.runs = RunManager(self)
        self.logs = LogManager(self)
        self.workflow = WorkflowManager(self)
        
        # Agent registry (for MVP, local only)
        self._agents: dict[str, dict[str, Any]] = {}

    # --- Provider/Adapter helpers ---
    def provider(self, provider: str, **config_overrides: Any):
        """Return a provider adapter using client's API settings.
        
        Args:
            provider: provider name (e.g., "browserbase")
            **config_overrides: override keys for adapter config
        """
        base_config: dict[str, Any] = {
            "project_id": self.project_id,
            "simultaneous_api_url": self.api_url,
            "simultaneous_api_key": self.api_key,
        }
        base_config.update(config_overrides)
        return get_adapter(
            runtime_kind=RuntimeKind.BROWSER,
            provider=provider,
            config=base_config,
        )

    def browser_client(
        self,
        *,
        provider: str | Browsers = "browserbase",
        model_api_key: str | None = None,
        model_name: str | Models = "gpt-4o",
        model_client_options: dict | None = None,
        adapter_config: dict | None = None,
        **kwargs: Any,
    ) -> BrowserClient:
        """Construct a BrowserClient that can self-launch via provider.
        
        The returned client will launch a session using the provider adapter
        built from this SimClient's credentials and project id.
        """
        adapter = self.provider(provider, **(adapter_config or {}))
        return BrowserClient(
            adapter=adapter,
            model_api_key=model_api_key,
            model_name=model_name,
            model_client_options=model_client_options,
            **kwargs,
        )
    
    @property
    def http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for API calls."""
        if self._http_client is None:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._http_client = httpx.AsyncClient(
                base_url=self.api_url,
                timeout=httpx.Timeout(connect=5.0, read=30.0, write=5.0, pool=5.0),
                headers=headers,
            )
        return self._http_client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def agent(
        self,
        name: str | None = None,
        runtime: Runtime | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Decorator for registering agents.
        
        Args:
            name: Agent name (defaults to function name)
            runtime: Runtime configuration (uses default if None)
            **kwargs: Additional agent metadata
        
        Example:
            ```python
            @client.agent(name="scrape-jobs", runtime=Browser())
            async def scrape_jobs(query: str) -> list[dict]:
                ...
            ```
        """
        def decorator(func: Callable) -> Callable:
            agent_name = name or func.__name__
            
            # Extract function metadata
            sig = inspect.signature(func)
            inputs = []
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                param_type = "string"
                if param.annotation != inspect.Parameter.empty:
                    # Map Python types to spec types
                    ann_str = str(param.annotation)
                    if "list" in ann_str or "dict" in ann_str:
                        param_type = "json"
                    elif ann_str in ("int", "float"):
                        param_type = "number"
                    elif ann_str == "bool":
                        param_type = "boolean"
                
                inputs.append({
                    "name": param_name,
                    "type": param_type,
                    "default": param.default if param.default != inspect.Parameter.empty else None,
                })
            
            # Create agent spec
            agent_info = {
                "name": agent_name,
                "func": func,
                "runtime": runtime or self.default_runtime,
                "inputs": inputs,
                "docstring": func.__doc__ or "",
                **kwargs,
            }
            
            self._agents[agent_name] = agent_info
            
            # Return the original function (not wrapped for MVP)
            return func
        
        return decorator
    
    async def run(
        self,
        agent_ref: str | Callable,
        params: dict[str, Any] | None = None,
        runtime: Runtime | None = None,
        parallel: int = 1,
    ) -> str:
        """
        Run an agent (convenience method).
        
        Args:
            agent_ref: Agent name or callable
            params: Input parameters
            runtime: Runtime configuration (uses default if None)
            parallel: Number of parallel shards
            
        Returns:
            Run ID
        """
        return await self.runs.create(
            agent_ref=agent_ref,
            params=params,
            runtime=runtime,
            parallel=parallel,
        )
    
    def get_agent(self, name: str) -> dict[str, Any] | None:
        """Get agent metadata by name."""
        return self._agents.get(name)

