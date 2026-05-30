from fastapi import APIRouter, HTTPException, Body
from src.services.mcp_client import mcp_client

router = APIRouter(prefix="/mcp-bridge", tags=["MCP Bridge"])

@router.post("/execute")
async def execute_mcp_tool(
    tool: str = Body(..., description="Tool name to call"),
    arguments: dict = Body(default={}, description="Arguments for the tool")
):
    """
    HTTP POST bridge to trigger stdio MCP tool calls from web endpoints.
    """
    try:
        res = await mcp_client.call_tool(tool, arguments)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP Bridge execution failed: {str(e)}")
