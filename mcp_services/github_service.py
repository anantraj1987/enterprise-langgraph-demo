import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="GitHub Code Analysis MCP Microservice", version="1.0.0")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class MCPToolRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


@app.get("/mcp/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "analyze_git_commits",
                "description": "Inspects recent repository commits, changed files, and stack trace logs.",
                "parameters": {"repo_name": "string"}
            }
        ]
    }


@app.post("/mcp/invoke")
def invoke_tool(request: MCPToolRequest):
    if request.tool_name == "analyze_git_commits":
        file_path = DATA_DIR / "git_repositories.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return {"result": json.load(f)}
        return {"error": "Git data source offline."}
    return {"error": f"Tool '{request.tool_name}' not recognized."}


if __name__ == "__main__":
    print("Starting GitHub MCP Microservice on http://localhost:8002 ...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
