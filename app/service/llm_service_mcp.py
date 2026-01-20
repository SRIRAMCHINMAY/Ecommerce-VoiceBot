# app/service/llm_service_mcp.py

import anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPEnabledLLMService