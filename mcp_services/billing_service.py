
import json
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="AWS Billing MCP Microservice", version="1.0.0")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class MCPToolRequest(BaseModel):
    tool_name: str
    arguments: dict = {}


@app.get("/mcp/tools")
def list_tools():
    return {
        "tools": [
            {
                "name": "inspect_aws_cost_explorer",
                "description": "Retrieves AWS Cost Explorer cost driver breakdowns and usage variance spikes.",
                "parameters": {"account_id": "string"}
            }
        ]
    }


@app.post("/mcp/invoke")
def invoke_tool(request: MCPToolRequest):
    if request.tool_name == "inspect_aws_cost_explorer":
        file_path = DATA_DIR / "billing_records.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return {"result": json.load(f)}
        return {"error": "Billing records data source offline."}
    return {"error": f"Tool '{request.tool_name}' not recognized."}


if __name__ == "__main__":
    print("Starting Billing MCP Microservice on http://localhost:8003 ...")
    uvicorn.run(app, host="0.0.0.0", port=8003)
