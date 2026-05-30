import sys
import os
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClientService:
    def __init__(self):
        # Resolve path to the sibling mcp-data-crawler project directory
        services_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(services_dir)
        backend_core_dir = os.path.dirname(src_dir)
        be_dir = os.path.dirname(backend_core_dir)
        crawler_dir = os.path.join(be_dir, "mcp-data-crawler")
        server_path = os.path.join(crawler_dir, "server.py")
        
        # Spawn the Python server as an stdio child process
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path],
            env=os.environ.copy()
        )
        self.session = None
        self._exit_stack = None

    async def start(self):
        """
        Starts the Python MCP Server stdio subprocess and initializes the protocol handshake.
        """
        if self.session:
            return
            
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
            print("Connected to modular Python MCP Server via stdio successfully.")
        except Exception as e:
            print(f"Failed to start MCP Client connection channel: {str(e)}")
            self.session = None
            if self._exit_stack:
                await self._exit_stack.aclose()
                self._exit_stack = None

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Invokes an MCP tool on the server and parses the returning structured JSON content.
        """
        if not self.session:
            await self.start()
            if not self.session:
                raise RuntimeError("MCP Session is not active and failed to initialize.")
                
        try:
            result = await self.session.call_tool(tool_name, arguments)
            # The tool result contains text content, which is a JSON string
            content_text = result.content[0].text
            return json.loads(content_text)
        except Exception as e:
            return {"status": "error", "message": f"MCP execution failed: {str(e)}"}

    async def stop(self):
        """
        Closes the communication channel and cleanly terminates the subprocess.
        """
        if self._exit_stack:
            await self._exit_stack.aclose()
            self._exit_stack = None
            self.session = None
            print("Closed MCP Client connection stack.")

# Share single client across core routers and background schedulers
mcp_client = MCPClientService()
