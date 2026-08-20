import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Monitoring MCP Microservice", version="1.0.0")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class MCPToolRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


@app.get("/mcp/tools")
def list_tools():
    """MCP Protocol Tool Discovery Endpoint."""
    return {
        "tools": [
            {
                "name": "query_ec2_metrics",
                "description": "Queries real-time CloudWatch telemetry for server nodes and database clusters.",
                "parameters": {"resource_id": "string"}
            }
        ]
    }


@app.post("/mcp/invoke")
def invoke_tool(request: MCPToolRequest):
    """MCP Protocol Tool Invocation Endpoint."""
    if request.tool_name == "query_ec2_metrics":
        resource_id = request.arguments.get("resource_id", "")
        file_path = DATA_DIR / "monitoring_telemetry.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
                if resource_id:
                    filtered = [m for m in data.get("metrics", []) if resource_id.lower() in m.get("resource_id", "").lower()]
                    return {"result": filtered if filtered else data}
                return {"result": data}
        return {"error": "Telemetry store offline."}
    return {"error": f"Tool '{request.tool_name}' not recognized."}


if __name__ == "__main__":
    print("Starting Monitoring MCP Microservice on http://localhost:8001 ...")
    uvicorn.run(app, host="0.0.0.0", port=8001)