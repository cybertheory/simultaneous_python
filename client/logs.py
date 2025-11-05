"""Log streaming for runs."""

from typing import Any

from rich.console import Console
from rich.text import Text

from simultaneous.client.runs import RunManager


class LogManager:
    """Manages log streaming for runs."""
    
    def __init__(self, client: "SimClient"):
        """Initialize log manager."""
        self.client = client
        self.console = Console()
    
    async def stream(
        self,
        run_id: str,
        follow: bool = True,
    ) -> None:
        """
        Stream logs from a run.
        
        Args:
            run_id: Run ID
            follow: Whether to follow logs until completion
        """
        if run_id not in self.client.runs._runs:
            raise ValueError(f"Run not found: {run_id}")
        
        run_info = self.client.runs._runs[run_id]
        adapter = run_info["adapter"]
        provider_run_ids = run_info["provider_run_ids"]
        
        cursors = {pid: None for pid in provider_run_ids}
        seen_entries: set[tuple[str, str, str]] = set()  # (provider_run_id, timestamp, line)
        
        while follow:
            any_new = False
            
            for provider_run_id in provider_run_ids:
                cursor = cursors.get(provider_run_id)
                
                try:
                    logs_response = await adapter.logs(
                        provider_run_id=provider_run_id,
                        cursor=cursor,
                    )
                    
                    entries = logs_response.get("entries", [])
                    next_cursor = logs_response.get("next_cursor")
                    
                    for entry in entries:
                        # Deduplicate entries
                        entry_key = (
                            provider_run_id,
                            entry.get("ts", ""),
                            entry.get("line", ""),
                        )
                        
                        if entry_key not in seen_entries:
                            seen_entries.add(entry_key)
                            any_new = True
                            
                            # Format and print
                            stream = entry.get("stream", "stdout")
                            line = entry.get("line", "")
                            
                            if stream == "stderr":
                                self.console.print(Text(line, style="red"))
                            else:
                                self.console.print(line)
                    
                    if next_cursor:
                        cursors[provider_run_id] = next_cursor
                
                except Exception as e:
                    self.console.print(f"[red]Error fetching logs: {e}[/red]")
            
            # Check if run is terminal
            if not any_new:
                # Poll status to see if done
                status = await self.client.runs.wait(run_id)
                if status["state"] in {"SUCCEEDED", "FAILED", "CANCELLED"}:
                    follow = False
            
            if follow and not any_new:
                # Brief sleep if no new logs
                import asyncio
                await asyncio.sleep(0.5)
    
    async def get(
        self,
        run_id: str,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """
        Get logs from a run (non-streaming).
        
        Args:
            run_id: Run ID
            cursor: Pagination cursor
            
        Returns:
            Logs dictionary
        """
        if run_id not in self.client.runs._runs:
            raise ValueError(f"Run not found: {run_id}")
        
        run_info = self.client.runs._runs[run_id]
        adapter = run_info["adapter"]
        provider_run_ids = run_info["provider_run_ids"]
        
        all_entries = []
        for provider_run_id in provider_run_ids:
            try:
                logs_response = await adapter.logs(
                    provider_run_id=provider_run_id,
                    cursor=cursor,
                )
                entries = logs_response.get("entries", [])
                all_entries.extend(entries)
            except Exception:
                # Continue on errors
                pass
        
        return {
            "entries": all_entries,
        }







