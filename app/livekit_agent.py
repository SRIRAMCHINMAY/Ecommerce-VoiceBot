import asyncio
import os
import sys
import logging
from typing import Annotated
from dotenv import load_dotenv

# Ensure the project root is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit.agents import JobContext, WorkerOptions, cli, voice, llm
from livekit.plugins import openai, silero

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-agent")

# Global variables for shared resources (lazy-loaded on first use)
_embedding_model = None
_qdrant_service = None
_order_service = None
_services_lock = asyncio.Lock()

async def get_services():
    """Get or initialize services (lazy loading)"""
    global _embedding_model, _qdrant_service, _order_service
    
    async with _services_lock:
        if _embedding_model is None:
            logger.info("⏳ Loading services (first time)...")
            try:
                # Import heavy modules only when needed
                from sentence_transformers import SentenceTransformer
                from app.config.qdrant_config import QdrantConfig
                from app.service.qdrant_service import QdrantService
                from app.service.orders_service import OrderService
                
                # Load in separate thread to avoid blocking
                _embedding_model = await asyncio.to_thread(
                    SentenceTransformer, "all-MiniLM-L6-v2"
                )
                _qdrant_service = QdrantService(QdrantConfig())
                _order_service = OrderService(csv_path="./data/orders.csv")
                logger.info("✅ Services loaded!")
            except Exception as e:
                logger.error(f"❌ Failed to load services: {e}")
                return None, None, None
    
    return _embedding_model, _qdrant_service, _order_service

class ECommerceTools:
    """E-commerce function tools for the voice agent"""
    
    @llm.function_tool(description="Search for products in the catalog. Use this when user asks about products, prices, or wants to browse items.")
    async def search_products(
        self, 
        query: Annotated[str, "What the user is looking for (e.g., 'laptop', 'headphones under $50', 'electronics')"]
    ):
        """Search the product catalog"""
        logger.info(f"🔍 Searching products for: {query}")
        model, qdrant, _ = await get_services()
        
        if not model or not qdrant:
            return "Product catalog is currently loading. Please try again in a moment."
        
        try:
            # Encode query
            query_vector = await asyncio.to_thread(model.encode, [query])
            
            # Search in Qdrant
            results = qdrant.search(query_vector[0].tolist(), limit=10)
            
            if not results:
                return "No products found matching your search."
            
            # Format results
            products = []
            for r in results:
                name = r.payload.get('name', '')
                price = r.payload.get('price', '')
                category = r.payload.get('category', '')
                desc = r.payload.get('description', '')
                
                if name and price:
                    products.append(f"• {name} - ${price} ({category}): {desc}")
            
            if not products:
                return "No products found matching your search."
            
            return "Here are the products I found:\n\n" + "\n".join(products[:5])
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return "Sorry, I encountered an error while searching for products."

    @llm.function_tool(description="Track an order status by order ID. Use this when user asks about their order, delivery status, or provides an order number.")
    async def track_order(
        self,
        order_id: Annotated[str, "The order ID to track (e.g., 'ORD12345')"]
    ):
        """Track order status"""
        logger.info(f"📦 Tracking order: {order_id}")
        _, _, orders = await get_services()
        
        if not orders:
            return "Order tracking system is currently loading. Please try again in a moment."
        
        try:
            # Ensure order ID has ORD prefix
            if not order_id.upper().startswith("ORD"):
                order_id = "ORD" + order_id
            
            order = orders.track_order(order_id.upper())
            
            if not order:
                return f"Order {order_id} not found. Please check the order ID and try again."
            
            # Format order details
            status = order.get('status', 'unknown').upper()
            customer = order.get('customer_name', 'N/A')
            total = order.get('total', 0)
            order_date = order.get('order_date', 'N/A')
            
            response = f"Order {order_id} for {customer}:\n"
            response += f"Status: {status}\n"
            response += f"Total: ${total:.2f}\n"
            response += f"Order Date: {order_date}\n"
            
            if order.get('tracking_number'):
                response += f"Tracking Number: {order.get('tracking_number')}\n"
            if order.get('carrier'):
                response += f"Carrier: {order.get('carrier')}\n"
            if order.get('estimated_delivery'):
                response += f"Estimated Delivery: {order.get('estimated_delivery')}\n"
            
            items = order.get('items', [])
            if items:
                items_list = ", ".join([f"{item.get('name', '')} x{item.get('quantity', 1)}" for item in items])
                response += f"Items: {items_list}"
            
            return response
            
        except Exception as e:
            logger.error(f"Error tracking order: {e}")
            return "Sorry, I encountered an error while tracking the order."

async def entrypoint(ctx: JobContext):
    logger.info(f"🚀 Joining room: {ctx.room.name}")
    
    # Connect first - this is required!
    await ctx.connect()
    logger.info("✅ Connected to room!")
    
    # Create voice agent with e-commerce context and tools
    logger.info("⏳ Creating voice agent...")
    agent = voice.Agent(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(
            model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        ),
        tts=openai.TTS(),
        instructions="""You are a helpful e-commerce voice assistant. When a user first speaks, greet them warmly and explain you can help with products and orders.

IMPORTANT INSTRUCTIONS:
- Be conversational, friendly, and concise
- When users ask about products, USE THE search_products TOOL to find them
- When users ask about orders or provide an order ID, USE THE track_order TOOL  
- Always provide specific product details (name, price, category) when showing products
- Keep responses natural for voice - avoid overly long lists
- If unclear, politely ask for clarification

Examples:
- "Show me laptops" → Use search_products("laptops")
- "Track order ORD12345" → Use track_order("ORD12345")
- "What's under $50?" → Use search_products("products under $50")
""",
        tools=llm.find_function_tools(ECommerceTools()),
    )
    
    logger.info("✅ Agent created! Starting session...")
    session = voice.AgentSession()
    
    # Start session - this blocks until room disconnects
    await session.start(agent, room=ctx.room, capture_run=False)
    
    logger.info("Session ended")

if __name__ == "__main__":
    logger.info("🎬 Starting E-Commerce Voice Agent...")
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
