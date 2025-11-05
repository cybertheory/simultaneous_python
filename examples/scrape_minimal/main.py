"""Minimal scraping agent example."""

import json
import os
import sys


def main() -> None:
    """Main entrypoint for the agent."""
    # Get input parameters
    query = os.getenv("QUERY", "")
    
    print(f"Starting scrape for query: {query}", file=sys.stderr)
    
    # Simulate scraping (for now, just return mock data)
    # In a real scenario, this would use browser automation
    results = [
        {"title": f"Job result 1 for {query}", "url": "https://example.com/job1"},
        {"title": f"Job result 2 for {query}", "url": "https://example.com/job2"},
        {"title": f"Job result 3 for {query}", "url": "https://example.com/job3"},
    ]
    
    print(f"Found {len(results)} results", file=sys.stderr)
    
    # Output results as JSON
    output = {
        "rows": results,
        "count": len(results),
    }
    
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()





