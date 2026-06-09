import sys
import os
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MathToolsMCPClient:
    def __init__(self):
        use_docker = os.getenv("MCP_USE_DOCKER", "False").lower() in ("true", "1", "yes")
        if use_docker:
            print("[Math MCP Client] Configuring to run math-tools in container via Docker CLI...")
            self.server_params = StdioServerParameters(
                command="docker",
                args=["run", "-i", "--rm", "mcp-math-tools"],
                env=os.environ.copy()
            )
        else:
            # Resolve target path to sibling folder: be/math-tools/server.py
            swarm_src_dir = os.path.dirname(os.path.abspath(__file__))
            be_dir = os.path.dirname(os.path.dirname(swarm_src_dir))
            server_path = os.path.join(be_dir, "math-tools", "server.py")
            
            print(f"[Math MCP Client] Configured to run math-tools server locally: {server_path}")
            self.server_params = StdioServerParameters(
                command=sys.executable,
                args=[server_path],
                env=os.environ.copy()
            )
        self.session = None
        self._exit_stack = None

    async def start(self):
        """
        Starts the math-tools MCP Server stdio subprocess and initializes the protocol handshake.
        """
        from contextlib import AsyncExitStack
        self._exit_stack = AsyncExitStack()
        
        try:
            read_stream, write_stream = await self._exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            print("[Math MCP Client] Handshake initialized successfully.")
        except Exception as e:
            print(f"[Math MCP Client] Failed to start MCP Client connection: {e}", file=sys.stderr)
            self.session = None
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

    async def call_predict_trajectory(self, arguments: dict) -> dict:
        """
        Calls the 'predict_asset_trajectory' tool on the math-tools MCP server.
        """
        if not self.session:
            await self.start()
            if not self.session:
                return {"status": "error", "message": "MCP Session not active and failed to initialize."}
                
        try:
            result = await self.session.call_tool("predict_asset_trajectory", arguments)
            # The tool result contains text content, which is a JSON string
            content_text = result.content[0].text
            return json.loads(content_text)
        except Exception as e:
            return {"status": "error", "message": f"MCP tool call failed: {str(e)}"}

    async def stop(self):
        """
        Terminates the stdio connection and clean up resources.
        """
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self.session = None
            print("[Math MCP Client] Connection closed.")
