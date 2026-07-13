import sys
import os
import json
import time
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.config import settings
from src.metrics import (
    MCP_TOOL_DURATION,
    MCP_TOOL_CALLS_TOTAL,
    MCP_CRAWLED_BYTES,
    MCP_CRAWLED_ITEMS
)


class MCPClientService:
    def __init__(self):
        if getattr(settings, "MCP_USE_DOCKER", False):
            # Spawn Playwright MCP crawler dynamically via Docker CLI using host daemon
            print("[MCP Client] Configuring to run Playwright MCP crawler in container via Docker CLI...")
            self.server_params = StdioServerParameters(
                command="docker",
                args=["run", "-i", "--rm", "--ipc=host", "mcp-data-crawler"],
                env=os.environ.copy()
            )
        else:
            # Resolve path to the sibling mcp-data-crawler project directory
            services_dir = os.path.dirname(os.path.abspath(__file__))
            src_dir = os.path.dirname(services_dir)
            backend_core_dir = os.path.dirname(src_dir)
            be_dir = os.path.dirname(backend_core_dir)
            crawler_dir = os.path.join(be_dir, "mcp-data-crawler")
            server_path = os.path.join(crawler_dir, "server.py")
            
            print(f"[MCP Client] Configuring to run local Python MCP crawler: {server_path}")
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
                
        start_time = time.perf_counter()
        status = "success"
        try:
            result = await self.session.call_tool(tool_name, arguments)
            # The tool result contains text content, which is a JSON string
            content_text = result.content[0].text
            parsed_result = json.loads(content_text)
            
            if parsed_result.get("status") == "error":
                status = "error"
            
            # Record sizes and items count
            size_bytes = len(content_text.encode('utf-8'))
            MCP_CRAWLED_BYTES.labels(tool_name=tool_name).inc(size_bytes)
            
            # Estimate items count
            items_count = 1
            if isinstance(parsed_result, dict):
                # E.g. lists inside dict keys like "news", "quotes", etc.
                for k, v in parsed_result.items():
                    if isinstance(v, list):
                        items_count = max(items_count, len(v))
            elif isinstance(parsed_result, list):
                items_count = len(parsed_result)
            MCP_CRAWLED_ITEMS.labels(tool_name=tool_name).inc(items_count)
            
            return parsed_result
        except Exception as e:
            status = "error"
            print(f"[MCP Client Error] Failed to call tool {tool_name} with args {arguments}: {e}")
            try:
                print(f"[MCP Client Error Content] content_text: {content_text}")
            except NameError:
                pass
            return {"status": "error", "message": f"MCP execution failed: {str(e)}"}
        finally:
            duration = time.perf_counter() - start_time
            MCP_TOOL_DURATION.labels(tool_name=tool_name, status=status).observe(duration)
            MCP_TOOL_CALLS_TOTAL.labels(tool_name=tool_name, status=status).inc()

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
