import asyncio
from mcp.server.fastmcp import FastMCP
import sys
import os

# Add root folder to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import server
import council_settings

async def test_server_tools():
    print("Running server smoke test...")
    # Load settings to see what is configured
    settings = council_settings.load_settings()
    
    # Redact sensitive information before logging
    safe_settings = settings.copy()
    if "openrouter_api_key" in safe_settings:
        key = safe_settings["openrouter_api_key"]
        if len(key) > 10:
            safe_settings["openrouter_api_key"] = f"{key[:8]}...[REDACTED]...{key[-4:]}"
        else:
            safe_settings["openrouter_api_key"] = "[REDACTED]"
            
    print(f"Current Settings (safe): {safe_settings}")
    
    # We will temporarily enable both tools to verify their schema
    test_settings = settings.copy()
    test_settings["expose_internal_council"] = True
    test_settings["expose_council"] = True
    
    # Create a fresh FastMCP instance
    test_mcp = FastMCP("llm_council_mcp_test")
    
    # Register
    server.register_configured_tools(test_mcp, test_settings)
    
    tools = await test_mcp.list_tools()
    print(f"Exposed Tools Count: {len(tools)}")
    
    for tool in tools:
        print("\n-------------------------------------------")
        print(f"Tool Name: {tool.name}")
        print(f"Description: {tool.description}")
        print(f"Input Schema: {tool.inputSchema}")
        
        # Verify that input schema is flat (no "params" wrapper)
        properties = tool.inputSchema.get("properties", {})
        if "params" in properties:
            print("❌ ERROR: Found nested 'params' in input schema!")
            sys.exit(1)
        else:
            print("✓ SUCCESS: Schema is flat.")
            
        print(f"Properties: {list(properties.keys())}")
        
    print("\nSmoke test passed successfully!")

if __name__ == "__main__":
    asyncio.run(test_server_tools())
