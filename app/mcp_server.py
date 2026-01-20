# app/mcp_server.py

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Initialize MCP server
app = Server("ecommerce-assistant")

@app.list_tools()
async def list_tools():
    """
    Declare available tools to the LLM
    """
    return [
        Tool(
            name="search_products",
            description="Search the product catalog",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price filter"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="track_order",
            description="Track order status",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Order ID to track"
                    }
                },
                "required": ["order_id"]
            }
        ),
        Tool(
            name="get_product_details",
            description="Get detailed product information",
            inputSchema={
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "string",
                        "description": "Product ID"
                    }
                },
                "required": ["product_id"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    """
    Execute tool calls from the LLM
    """
    if name == "search_products":
        results = await rag_service.search_products(
            query=arguments["query"],
            max_price=arguments.get("max_price")
        )
        return [TextContent(
            type="text",
            text=json.dumps(results, indent=2)
        )]
    
    elif name == "track_order":
        order = orders_service.track_order(arguments["order_id"])
        return [TextContent(
            type="text",
            text=json.dumps(order, indent=2)
        )]
    
    elif name == "get_product_details":
        product = products_service.get_product(arguments["product_id"])
        return [TextContent(
            type="text",
            text=json.dumps(product, indent=2)
        )]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """
    Start MCP server
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())