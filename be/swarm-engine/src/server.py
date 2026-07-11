import asyncio
import os
import sys
import json
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse

# Ensure swarm-engine parent directory is in PYTHONPATH to allow modular sub-imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

app = FastAPI(title="Virtual Trader Swarm Agent Engine Service")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/debate")
async def run_debate_stream(
    ticker: str = Query(..., description="Asset ticker symbol"),
    category: str = Query(..., description="Asset category"),
    price: float = Query(..., description="Current asset price")
):
    """
    Spawns the main.py CLI as a subprocess, captures stdout/stderr in real-time,
    and streams the JSON-lines output to the client.
    """
    async def event_generator():
        # Determine Python command
        python_exe = sys.executable
        script_path = os.path.join(BASE_DIR, "src", "main.py")
        
        cmd = [
            python_exe,
            "-u",
            script_path,
            "--ticker", ticker,
            "--category", category,
            "--price", str(price)
        ]

        
        # Propagate GEMINI_API_KEY and other env variables
        env = os.environ.copy()
        
        print(f"[Swarm Service] Spawning: {' '.join(cmd)}")
        sys.stdout.flush()
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=BASE_DIR
        )
        
        # Read stdout line-by-line and yield
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            line_str = line.decode("utf-8").strip()
            if line_str:
                # Print to service console logs for monitoring
                print(f"[Agent Log] {line_str}")
                sys.stdout.flush()
                yield line_str + "\n"
            
        # Wait for completion and read stderr
        stderr_data = await process.stderr.read()
        if stderr_data:
            stderr_str = stderr_data.decode("utf-8")
            print(f"[Swarm Stderr] {stderr_str}")
            sys.stdout.flush()
            # If there's an error, yield it so the backend knows
            # Yielding a JSON object with error description is safest
            try:
                # check if it's already JSON, else wrap it
                json.loads(stderr_str)
                yield stderr_str + "\n"
            except Exception:
                yield json.dumps({"status": "error", "message": stderr_str}) + "\n"
            
        await process.wait()
        print(f"[Swarm Service] Finished debate for {ticker}")
        sys.stdout.flush()

    return StreamingResponse(event_generator(), media_type="application/x-json-stream")
