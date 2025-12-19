from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import List, Dict, Any, Optional
from app.core.settings import settings

class LLMService:
    """Model-agnostic LLM service using LangChain"""
    
    def __init__(self, client: ChatOpenAI):
        """
        Initialize with a LangChain ChatOpenAI client
        
        Args:
            client: ChatOpenAI instance (can be OpenRouter, OpenAI, etc.)
        """
        self.client = client
    
    def invoke(self, query: str, system_prompt: Optional[str] = None, 
               context: Optional[str] = None) -> str:
        """
        Model-agnostic invoke method
        
        Args:
            query: User query/message
            system_prompt: Optional system prompt
            context: Optional additional context (e.g., RAG results)
        
        Returns:
            LLM response as string
        """
        messages = []
        
        # Build system message
        if system_prompt:
            full_system_prompt = system_prompt
        else:
            full_system_prompt = self._default_system_prompt()
        
        if context:
            full_system_prompt += f"\n\nRelevant Context:\n{context}"
        
        messages.append(SystemMessage(content=full_system_prompt))
        messages.append(HumanMessage(content=query))
        
        # Invoke LLM
        response = self.client.invoke(messages)
        
        return response.content
    
    def _default_system_prompt(self) -> str:
        """Default system prompt for e-commerce assistant"""
        return """You are a helpful e-commerce voice assistant.
Be concise and friendly (max 2-3 sentences per response).
Help users with orders, returns, and product questions."""


class ConversationalLLMService:
    """
    Conversational wrapper with history management
    Keeps LLMService simple and stateless
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.conversations: Dict[str, List[Dict]] = {}
    
    def chat(self, user_message: str, room_name: str, 
             system_prompt: Optional[str] = None,
             context: Optional[str] = None) -> str:
        """
        Chat with conversation history
        
        Args:
            user_message: User's message
            room_name: Unique identifier for conversation
            system_prompt: Optional system prompt
            context: Optional RAG context
        
        Returns:
            Assistant's response
        """
        # Initialize conversation history
        if room_name not in self.conversations:
            self.conversations[room_name] = []
        
        # Build messages with history
        messages = []
        
        # System prompt
        if system_prompt:
            full_system = system_prompt
        else:
            full_system = self._default_system_prompt()
        
        if context:
            full_system += f"\n\nRelevant Context:\n{context}"
        
        messages.append(SystemMessage(content=full_system))
        
        # Add conversation history (last 6 messages = 3 turns)
        for msg in self.conversations[room_name][-6:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current message
        messages.append(HumanMessage(content=user_message))
        
        # Get response
        response = self.llm_service.client.invoke(messages)
        assistant_message = response.content
        
        # Update history
        self.conversations[room_name].append({
            "role": "user",
            "content": user_message
        })
        self.conversations[room_name].append({
            "role": "assistant", 
            "content": assistant_message
        })
        
        return assistant_message
    
    def _default_system_prompt(self) -> str:
        return """You are a helpful e-commerce voice assistant.
Be concise and friendly (max 2-3 sentences per response).
Help users with orders, returns, and product questions."""
    
    def reset_conversation(self, room_name: str):
        """Reset conversation history"""
        if room_name in self.conversations:
            self.conversations[room_name] = []


# Factory function to create LLM client
def create_llm_client() -> ChatOpenAI:
    """Create ChatOpenAI client with OpenRouter"""
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS,
        streaming=False
    )


# Singleton instances
llm_client = create_llm_client()
llm_service = LLMService(client=llm_client)
conversational_llm = ConversationalLLMService(llm_service)