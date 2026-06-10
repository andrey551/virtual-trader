import asyncio
import json
import os
import sys
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.types as types
from mcp.server.stdio import stdio_server

# Adjust import path to ensure src modules can be resolved
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.forecaster import predict_forecast

server = Server("math-tools-mcp")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """Define the tools this server provides"""
    return [
        types.Tool(
            name="predict_asset_trajectory",
            description="Exposes exact quantitative baseline and swarm-adjusted asset price forecasts over short, medium, and long horizons.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticker": {
                        "type": "string",
                        "description": "Asset ticker symbol (e.g. AAPL, BTC-USD, EURUSD=X)."
                    },
                    "current_price": {
                        "type": "number",
                        "description": "The current price/spot price of the asset."
                    },
                    "consensus_verdict": {
                        "type": "string",
                        "description": "Consensus verdict determined by Swarm (STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL)."
                    },
                    "consensus_confidence": {
                        "type": "number",
                        "description": "Consensus confidence level as percentage (0.0 to 100.0)."
                    },
                    "momentum_direction": {
                        "type": "number",
                        "description": "Trend momentum direction scalar from -1.0 to 1.0."
                    },
                    "risk_multiplier": {
                        "type": "number",
                        "description": "Risk sizing multiplier (typically 0.5 to 2.0)."
                    },
                    "volatility_outlook": {
                        "type": "string",
                        "description": "Expected asset volatility (HIGH, MEDIUM, LOW)."
                    }
                },
                "required": [
                    "ticker", "current_price", "consensus_verdict", "consensus_confidence",
                    "momentum_direction", "risk_multiplier", "volatility_outlook"
                ],
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Execute the matching tool function based on name"""
    if name != "predict_asset_trajectory":
        raise ValueError(f"Unknown tool: {name}")
        
    args = arguments or {}
    try:
        # Compute exact mathematical prices
        forecast_result = predict_forecast(args)
        
        result_payload = {
            "status": "success",
            **forecast_result
        }
        
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result_payload, ensure_ascii=False)
            )
        ]
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e)
        }
        return [
            types.TextContent(
                type="text",
                text=json.dumps(error_result, ensure_ascii=False)
            )
        ]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="math-tools-mcp",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
