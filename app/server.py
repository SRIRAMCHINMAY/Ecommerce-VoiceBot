from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, Response
import asyncio
import os
import base64
import re
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from typing import Dict, List
from qdrant_client.models import Filter, FieldCondition, Range

load_dotenv()

# Import services
from app.config.qdrant_config import QdrantConfig
from app.service.qdrant_service import QdrantService
from app.service.rag_service import RAGService
from app.service.stt_service import STTService
from app.service.tts_service import TTSService, TTSConfig
from app.service.llm_service import LLMService
from app.service.orders_service import OrderService
from app.service.livekit_service import livekit_service
from langchain_openai import ChatOpenAI

# ============================================================================
# INITIALIZE FASTAPI
# ============================================================================

app = FastAPI(title="E-Commerce Voicebot")

# Global services
services = {}
embedding_model = None

# Conversation memory - stores chat history per session
conversation_memory: Dict[str, List[Dict]] = {}

# ============================================================================
# STARTUP
# ============================================================================

@app.on_event("startup")
async def startup():
    global services, embedding_model
    
    print("\n🚀 Initializing services...")
    
    config = QdrantConfig()
    qdrant = QdrantService(config)
    rag = RAGService(qdrant)
    
    # Clear existing data to avoid duplicates on restart
    print("🧹 Clearing vector database...")
    qdrant.clear_collection()
    
    if os.path.exists("./data/products.csv"):
        count = rag.ingest_csv("./data/products.csv", "description", 
                               ["name", "price", "category", "stock", "brand"])
        print(f"✅ Loaded {count} products")
    
    if os.path.exists("./data/policies.csv"):
        count = rag.ingest_csv("./data/policies.csv", "answer", 
                               ["category", "question"])
        print(f"✅ Loaded {count} policies")
    
    stt = STTService()
    tts = TTSService(TTSConfig(openai_api_key=os.getenv("OPENAI_API_KEY")))
    
    llm_client = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "openai/gpt-4o-mini"),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=200  # Increased for longer responses
    )
    llm = LLMService(client=llm_client)
    
    order_service = OrderService(csv_path="./data/orders.csv")
    
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    
    services = {
        "qdrant": qdrant,
        "rag": rag,
        "stt": stt,
        "tts": tts,
        "llm": llm,
        "orders": order_service
    }
    
    print("✅ All services ready!\n")

# ============================================================================
# IMPROVED QUERY PROCESSOR WITH CONVERSATION MEMORY
# ============================================================================

async def process_query(user_text: str, session_id: str = "default") -> str:
    """Process text query with RAG + LLM + Conversation Memory"""
    
    # Initialize conversation history for new sessions
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []
    
    # Get conversation history (last 6 messages = 3 turns)
    history = conversation_memory[session_id][-6:]
    
    # Check for order tracking queries
    order_info = None
    lowered = user_text.lower()
    order_keywords = ["track", "order", "status", "where is", "my order", "order number"]
    
    # Try to extract order ID (e.g., ORD12345, ord-12345, etc.)
    # Pattern 1: ORD followed by numbers (e.g., ORD12345, ord-12345)
    order_id_match = re.search(r'\b(?:ORD|order)[\s\-_]?(\d{5,})\b', user_text, re.IGNORECASE)
    if not order_id_match:
        # Pattern 2: Just numbers that might be order IDs (if order keywords are present)
        if any(keyword in lowered for keyword in order_keywords):
            order_id_match = re.search(r'\b(\d{5,})\b', user_text)
    
    if order_id_match:
        matched_text = order_id_match.group(0).upper()
        if matched_text.startswith("ORD") or matched_text.startswith("ORDER"):
            order_id = matched_text.replace(" ", "").replace("-", "").replace("_", "")
            # Clean up common prefixes
            if order_id.startswith("ORDER"):
                order_id = order_id[5:]
            if not order_id.startswith("ORD"):
                order_id = "ORD" + order_id
        else:
            # Just numbers, prepend ORD - use group(1) if available (from pattern 1), else group(0)
            if order_id_match.lastindex and order_id_match.lastindex >= 1:
                order_id = "ORD" + order_id_match.group(1)
            else:
                order_id = "ORD" + order_id_match.group(0)
        
        order_service = services.get("orders")
        if order_service:
            order_info = order_service.track_order(order_id)
    
    # IMPROVED RAG: encode query and apply structured price filters if mentioned
    query_vector = embedding_model.encode([user_text])[0]

    price_filter: Filter | None = None
    min_price: float | None = None
    max_price: float | None = None

    # Support phrases like "between 20 and 50", "between $20-$50"
    between_match = re.search(
        r"between\s*\$?\s*(\d+(?:\.\d+)?)\s*(?:and|-|to)\s*\$?\s*(\d+(?:\.\d+)?)",
        lowered,
    )
    # Support "under/below/less than/up to 50"
    under_match = re.search(
        r"(?:under|below|less than|up to)\s*\$?\s*(\d+(?:\.\d+)?)",
        lowered,
    )
    # Support "over/above/more than/greater than 50"
    over_match = re.search(
        r"(?:over|above|more than|greater than)\s*\$?\s*(\d+(?:\.\d+)?)",
        lowered,
    )

    if between_match:
        min_price = float(between_match.group(1))
        max_price = float(between_match.group(2))
    elif under_match:
        max_price = float(under_match.group(1))
    elif over_match:
        min_price = float(over_match.group(1))

    if min_price is not None or max_price is not None:
        range_kwargs: dict = {}
        if min_price is not None:
            range_kwargs["gte"] = min_price
        if max_price is not None:
            range_kwargs["lte"] = max_price

        price_filter = Filter(
            must=[
                FieldCondition(
                    key="price",
                    range=Range(**range_kwargs),
                )
            ]
        )

    query_kwargs = {
        "collection_name": services["qdrant"].collection_name,
        "query": query_vector.tolist(),
        "limit": 30,  # search a broader set of candidates
        "with_payload": True,
    }

    if price_filter is not None:
        query_kwargs["query_filter"] = price_filter

    results = services["qdrant"].client.query_points(**query_kwargs).points
    
    # Build context (results may already be filtered by price)
    context_parts = []
    
    if results:
        for r in results:
            name = r.payload.get("name", "")
            price = r.payload.get("price", "")
            desc = r.payload.get("description", "")
            answer = r.payload.get("answer", "")
            category = r.payload.get("category", "")
            
            if name and price:
                product_info = f"{name} (${price}) - {category}: {desc}"
                context_parts.append(product_info)
            elif answer:
                context_parts.append(answer)
    
    context = "\n\n".join(context_parts) if context_parts else ""
    
    # Add order information to context if found
    order_context = ""
    if order_info:
        order_details = []
        order_details.append(f"Order ID: {order_info.get('order_id', 'N/A')}")
        order_details.append(f"Customer: {order_info.get('customer_name', 'N/A')}")
        order_details.append(f"Status: {order_info.get('status', 'N/A').upper()}")
        order_details.append(f"Total: ${order_info.get('total', 0):.2f}")
        order_details.append(f"Order Date: {order_info.get('order_date', 'N/A')}")
        
        items = order_info.get('items', [])
        if items:
            items_list = ", ".join([f"{item.get('name', '')} x{item.get('quantity', 1)}" for item in items])
            order_details.append(f"Items: {items_list}")
        
        if order_info.get('tracking_number'):
            order_details.append(f"Tracking Number: {order_info.get('tracking_number')}")
        if order_info.get('carrier'):
            order_details.append(f"Carrier: {order_info.get('carrier')}")
        if order_info.get('estimated_delivery'):
            order_details.append(f"Estimated Delivery: {order_info.get('estimated_delivery')}")
        if order_info.get('delivered_date'):
            order_details.append(f"Delivered Date: {order_info.get('delivered_date')}")
        if order_info.get('cancelled_date'):
            order_details.append(f"Cancelled Date: {order_info.get('cancelled_date')}")
        if order_info.get('cancellation_reason'):
            order_details.append(f"Cancellation Reason: {order_info.get('cancellation_reason')}")
        
        order_context = "\n\nORDER TRACKING INFORMATION:\n" + "\n".join(order_details)
    elif any(keyword in lowered for keyword in order_keywords):
        order_context = "\n\nORDER TRACKING INFORMATION:\nOrder not found. Please check the order ID and try again."
    
    # Build conversation history for LLM
    history_text = ""
    if history:
        history_text = "\n\nConversation History:\n"
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"
    
    # Enhanced system prompt with conversation awareness
    system_prompt = f"""You are a helpful e-commerce assistant with conversation memory.

IMPORTANT INSTRUCTIONS:
- Remember the conversation history and maintain context
- When showing products, list ALL matching items from the context
- If user asks about products under a price, show ALL items under that price
- Be conversational and remember what was discussed earlier
- Format product lists clearly with bullets
- When user asks about order tracking, provide the complete order details from the ORDER TRACKING INFORMATION section below
- If order is found, provide all relevant details including status, tracking number, carrier, and delivery dates
- If order is not found, politely inform the user and ask them to verify the order ID

{history_text}

Available Products/Information:
{context}{order_context}"""
    
    # Get LLM response
    response = services["llm"].invoke(user_text, system_prompt=system_prompt)
    
    # Update conversation memory
    conversation_memory[session_id].append({"role": "user", "content": user_text})
    conversation_memory[session_id].append({"role": "assistant", "content": response})
    
    # Keep only last 10 messages (5 turns)
    if len(conversation_memory[session_id]) > 10:
        conversation_memory[session_id] = conversation_memory[session_id][-10:]
    
    return response

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def home():
    """Serve the web UI"""
    return HTMLResponse(content=HTML_UI)

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    """Text chat endpoint with session support"""
    user_text = data.get("message", "")
    session_id = data.get("session_id", "default")  # Get session ID from client
    
    if not user_text:
        return {"error": "No message provided"}
    
    response = await process_query(user_text, session_id)
    
    return {
        "user": user_text,
        "bot": response,
        "session_id": session_id
    }

@app.post("/api/voice")
async def voice_endpoint(audio: UploadFile = File(...)):
    """Voice input endpoint"""
    try:
        audio_bytes = await audio.read()
        transcript = await services["stt"].transcribe(audio_bytes)
        
        if not transcript:
            return {"error": "Could not transcribe audio"}
        
        response_text = await process_query(transcript, "default")
        response_audio = await services["tts"].synthesize(response_text)
        audio_base64 = base64.b64encode(response_audio).decode('utf-8')
        
        return {
            "transcript": transcript,
            "response": response_text,
            "audio": audio_base64
        }
    
    except Exception as e:
        print(f"Error in voice endpoint: {e}")
        return {"error": str(e)}

@app.post("/api/reset")
async def reset_conversation(data: dict):
    """Reset conversation memory"""
    session_id = data.get("session_id", "default")
    if session_id in conversation_memory:
        conversation_memory[session_id] = []
    return {"status": "reset"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "services": {
            "qdrant": "ok" if services.get("qdrant") else "not ready",
            "llm": "ok" if services.get("llm") else "not ready"
        }
    }

@app.post("/api/track-order")
async def track_order_endpoint(data: dict):
    """Track order by order ID"""
    order_id = data.get("order_id", "")
    
    if not order_id:
        return {"error": "No order ID provided"}
    
    order_service = services.get("orders")
    if not order_service:
        return {"error": "Order service not available"}
    
    order = order_service.track_order(order_id)
    
    if not order:
        return {
            "success": False,
            "message": f"Order {order_id} not found. Please check your order ID and try again."
        }
    
    return {
        "success": True,
        "order": order
    }

@app.get("/api/livekit/token")
async def get_livekit_token(room: str, participant: str | None = None):
    """Generate a token for LiveKit client"""
    try:
        # Use a unique participant name if not provided to avoid "could not restart" errors
        if not participant:
            import uuid
            participant = f"user-{uuid.uuid4().hex[:8]}"
            
        token = livekit_service.create_token(room, participant)
        return {
            "token": token,
            "url": livekit_service.url
        }
    except Exception as e:
        return {"error": str(e)}

# ============================================================================
# UPDATED WEB UI WITH SESSION MANAGEMENT
# ============================================================================

HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>E-Commerce Voicebot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            text-align: center;
            border-radius: 20px 20px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .header-content {
            flex: 1;
        }
        
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .reset-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 15px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .reset-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .message {
            margin-bottom: 15px;
            display: flex;
            animation: slideIn 0.3s ease;
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
            white-space: pre-wrap;
        }
        
        .message.user .message-content {
            background: #667eea;
            color: white;
        }
        
        .message.bot .message-content {
            background: white;
            color: #333;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
            border-radius: 0 0 20px 20px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
        }
        
        #messageInput:focus {
            border-color: #667eea;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
        }
        
        #sendButton {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        #voiceButton {
            background: #4CAF50;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
        }
        
        #voiceButton.recording {
            background: #f44336;
            animation: pulse 1s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.1); }
        }
        
        .btn:hover {
            transform: scale(1.05);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .suggestions {
            padding: 10px 20px;
            background: white;
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        
        .suggestion-chip {
            padding: 6px 12px;
            background: #f0f0f0;
            border-radius: 15px;
            font-size: 12px;
            cursor: pointer;
        }
        
        .suggestion-chip:hover {
            background: #e0e0e0;
        }

        .status {
            padding: 8px 20px;
            background: #fff3cd;
            text-align: center;
            font-size: 12px;
            color: #856404;
            display: none;
        }

        .status.active {
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-content">
                <h1>🎤 E-Commerce Voicebot</h1>
                <p>Type or speak - I remember our conversation!</p>
            </div>
            <button class="reset-btn" onclick="resetConversation()">🔄 Reset Chat</button>
        </div>
        
        <div class="status" id="status"></div>
        
        <div class="suggestions">
            <div class="suggestion-chip" onclick="sendMessage('What products do you have under $50?')">
                💰 Under $50
            </div>
            <div class="suggestion-chip" onclick="sendMessage('Show me all electronics')">
                📱 Electronics
            </div>
            <div class="suggestion-chip" onclick="sendMessage('What\\'s your return policy?')">
                ↩️ Returns
            </div>
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message bot">
                <div class="message-content">
👋 Hello! I'm your shopping assistant with memory! I can:
- Show you all products under any price
- Remember our conversation
- Answer questions about products and policies

Try: "Show me products under $50"
                </div>
            </div>
        </div>
        
        <div class="input-container">
            <button class="btn" id="voiceButton" onclick="toggleVoiceRecording()">
                🎤
            </button>
            <input 
                type="text" 
                id="messageInput" 
                placeholder="Type or speak..."
                onkeypress="if(event.key==='Enter') sendMessage()"
            >
            <button class="btn" id="sendButton" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const voiceButton = document.getElementById('voiceButton');
        const statusDiv = document.getElementById('status');
        
        // Generate unique session ID
        const sessionId = 'session_' + Date.now();
        
        let mediaRecorder;
        let audioChunks = [];
        let isRecording = false;

        function showStatus(message) {
            statusDiv.textContent = message;
            statusDiv.classList.add('active');
            setTimeout(() => {
                statusDiv.classList.remove('active');
            }, 3000);
        }

        function addMessage(content, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'bot'}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(contentDiv);
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage(text = null) {
            const message = text || messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            sendButton.disabled = true;
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        message: message,
                        session_id: sessionId
                    })
                });
                
                const data = await response.json();
                addMessage(data.bot, false);
            } catch (error) {
                addMessage('Sorry, something went wrong.', false);
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        async function resetConversation() {
            try {
                await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                
                chatContainer.innerHTML = '';
                addMessage('Conversation reset! How can I help you?', false);
                showStatus('✅ Conversation reset');
            } catch (error) {
                console.error('Error resetting:', error);
            }
        }

        async function toggleVoiceRecording() {
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];
                
                mediaRecorder.ondataavailable = (event) => {
                    audioChunks.push(event.data);
                };
                
                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    await sendVoiceMessage(audioBlob);
                    stream.getTracks().forEach(track => track.stop());
                };
                
                mediaRecorder.start();
                isRecording = true;
                voiceButton.classList.add('recording');
                voiceButton.textContent = '⏹️';
                showStatus('🎤 Recording... Click again to stop');
                
            } catch (error) {
                console.error('Error accessing microphone:', error);
                showStatus('❌ Could not access microphone');
            }
        }

        function stopRecording() {
            if (mediaRecorder && isRecording) {
                mediaRecorder.stop();
                isRecording = false;
                voiceButton.classList.remove('recording');
                voiceButton.textContent = '🎤';
                showStatus('Processing your voice...');
            }
        }

        async function sendVoiceMessage(audioBlob) {
            sendButton.disabled = true;
            voiceButton.disabled = true;
            
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'recording.wav');
                
                const response = await fetch('/api/voice', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage('Sorry, I could not understand that.', false);
                    return;
                }
                
                addMessage(`🎤 "${data.transcript}"`, true);
                addMessage(data.response, false);
                
                if (data.audio) {
                    const audioData = atob(data.audio);
                    const audioArray = new Uint8Array(audioData.length);
                    for (let i = 0; i < audioData.length; i++) {
                        audioArray[i] = audioData.charCodeAt(i);
                    }
                    const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                    const audioUrl = URL.createObjectURL(audioBlob);
                    const audio = new Audio(audioUrl);
                    audio.play();
                    
                    showStatus('🔊 Playing response...');
                }
                
            } catch (error) {
                console.error('Error sending voice:', error);
                addMessage('Sorry, something went wrong with voice processing.', false);
            } finally {
                sendButton.disabled = false;
                voiceButton.disabled = false;
            }
        }

        messageInput.focus();
    </script>
</body>
</html>
"""