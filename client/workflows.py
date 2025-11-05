"""Workflow chaining for agents."""

from typing import Any, Callable

from simultaneous.client.runs import RunManager


class WorkflowManager:
    """Manages workflow chaining."""
    
    def __init__(self, client: "SimClient"):
        """Initialize workflow manager."""
        self.client = client
    
    def chain(self, *agent_refs: str | Callable) -> list[str | Callable]:
        """
        Create a linear workflow chain.
        
        Args:
            *agent_refs: Agent references in order
            
        Returns:
            List of agent references
        """
        return list(agent_refs)
    
    async def run(
        self,
        workflow: list[str | Callable],
        params: dict[str, Any] | None = None,
        runtime: Any = None,
    ) -> str:
        """
        Run a workflow chain.
        
        Args:
            workflow: List of agent references (from chain())
            params: Initial parameters
            runtime: Runtime configuration
            
        Returns:
            Final run ID
        """
        params = params or {}
        current_params = params
        
        run_ids = []
        
        for agent_ref in workflow:
            # Run agent with current params
            run_id = await self.client.runs.create(
                agent_ref=agent_ref,
                params=current_params,
                runtime=runtime,
                parallel=1,  # TODO: Allow parallel per step
            )
            run_ids.append(run_id)
            
            # Wait for completion
            result = await self.client.runs.wait(run_id)
            
            if result["state"] != "SUCCEEDED":
                raise RuntimeError(
                    f"Workflow step failed: {agent_ref} ended with state {result['state']}"
                )
            
            # Extract outputs for next step
            # TODO: Implement output extraction from results
            # For now, pass params through
            # current_params = extract_outputs(result)
        
        # Return last run ID
        return run_ids[-1] if run_ids else ""








