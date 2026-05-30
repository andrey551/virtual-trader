import { NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await request.json();
    const { tool, arguments: toolArgs } = body;
    
    if (!tool) {
      return NextResponse.json({ status: "error", message: "Missing tool name" }, { status: 400 });
    }
    
    // Absolute paths using process.cwd() (points to the /fe directory)
    const backendDir = path.join(process.cwd(), "../be/mcp-data-crawler");
    const scriptPath = path.join(backendDir, "test_mcp_tools.py");
    const argsString = JSON.stringify(toolArgs || {});
    
    return new Promise<Response>((resolve) => {
      // Spawn Python process safely without shell expansion
      const pythonProcess = spawn("python", [scriptPath, "--tool", tool, "--args", argsString], {
        cwd: backendDir
      });
      
      let stdout = "";
      let stderr = "";
      
      pythonProcess.stdout.on("data", (data) => {
        stdout += data.toString();
      });
      
      pythonProcess.stderr.on("data", (data) => {
        stderr += data.toString();
      });
      
      pythonProcess.on("close", (code) => {
        if (code !== 0) {
          resolve(NextResponse.json({
            status: "error",
            message: `Python process exited with code ${code}`,
            stderr: stderr,
            stdout: stdout
          }, { status: 500 }));
          return;
        }
        
        try {
          const markerStart = "--- RESULT ---";
          const markerEnd = "--------------";
          
          const startIdx = stdout.indexOf(markerStart);
          const endIdx = stdout.indexOf(markerEnd, startIdx + markerStart.length);
          
          if (startIdx !== -1 && endIdx !== -1) {
            const jsonStr = stdout.substring(startIdx + markerStart.length, endIdx).trim();
            const parsed = JSON.parse(jsonStr);
            resolve(NextResponse.json(parsed));
          } else {
            resolve(NextResponse.json({
              status: "error",
              message: "Could not locate output JSON markers in Python output stream.",
              stdout: stdout,
              stderr: stderr
            }, { status: 500 }));
          }
        } catch (parseErr) {
          resolve(NextResponse.json({
            status: "error",
            message: `Failed to parse output JSON: ${(parseErr as Error).message}`,
            stdout: stdout,
            stderr: stderr
          }, { status: 500 }));
        }
      });
    });
    
  } catch (err) {
    const error = err as Error;
    return NextResponse.json({ status: "error", message: error.message }, { status: 500 });
  }
}
