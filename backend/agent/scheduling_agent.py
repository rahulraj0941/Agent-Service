from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from typing import List, Dict, Any
import os
import json

from backend.agent.prompts import SYSTEM_PROMPT
from backend.tools.availability_tool import availability_tool
from backend.tools.booking_tool import booking_tool
from backend.rag.faq_rag import FAQRetrieval


class SchedulingAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,
            google_api_key=api_key
        ).bind_tools([availability_tool, booking_tool])
        
        self.faq_retrieval = None
        
        self.tools = {
            "check_availability": availability_tool,
            "book_appointment": booking_tool
        }
    
    def _get_faq_retrieval(self):
        if self.faq_retrieval is None:
            self.faq_retrieval = FAQRetrieval()
        return self.faq_retrieval
    
    def _convert_history_to_messages(self, history: List[Dict[str, str]]) -> List[Any]:
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages
    
    def _extract_text_content(self, content: Any) -> str:
        """Extract text from response content - handles both string and list formats."""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and 'text' in part:
                    text_parts.append(part['text'])
                elif isinstance(part, str):
                    text_parts.append(part)
            return ''.join(text_parts)
        return str(content)
    
    def _check_if_faq_query(self, user_message: str) -> bool:
        faq_keywords = [
            "insurance", "accepted", "billing", "payment", "cost", "price",
            "location", "address", "directions", "parking", "where",
            "hours", "open", "closed", "when",
            "bring", "documents", "need", "prepare", "preparation",
            "policy", "policies", "cancellation", "cancel", "late", "covid",
            "what to", "how do", "do you", "can i", "is there"
        ]
        
        message_lower = user_message.lower()
        return any(keyword in message_lower for keyword in faq_keywords)
    
    async def process_message(self, user_message: str, 
                             conversation_history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        if conversation_history is None:
            conversation_history = []
        
        try:
            additional_context = ""
            if self._check_if_faq_query(user_message):
                try:
                    faq_retrieval = self._get_faq_retrieval()
                    faq_context = faq_retrieval.get_context_for_query(user_message)
                    additional_context = f"\n\nRelevant Clinic Information:\n{faq_context}\n"
                except Exception as e:
                    print(f"FAQ retrieval failed: {e}. Using fallback response.")
                    additional_context = "\n\nNote: For detailed clinic information, please call +1-555-123-4567.\n"
            
            enhanced_message = user_message
            if additional_context:
                enhanced_message = f"{user_message}\n{additional_context}"
            
            chat_history = self._convert_history_to_messages(conversation_history)
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + chat_history + [
                HumanMessage(content=enhanced_message)
            ]
            
            response_message = await self.llm.ainvoke(messages)
            
            tools_used = 0
            if hasattr(response_message, 'tool_calls') and response_message.tool_calls:
                tools_used = len(response_message.tool_calls)
                messages.append(response_message)
                
                for tool_call in response_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_input = tool_call['args']
                    
                    if tool_name in self.tools:
                        tool = self.tools[tool_name]
                        tool_result = await tool.ainvoke(tool_input)
                        
                        messages.append(
                            ToolMessage(
                                content=tool_result,
                                tool_call_id=tool_call['id']
                            )
                        )
                
                final_response = await self.llm.ainvoke(messages)
                response = self._extract_text_content(final_response.content)
            else:
                response = self._extract_text_content(response_message.content)
            
            updated_history = conversation_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ]
            
            return {
                "response": response,
                "conversation_history": updated_history,
                "metadata": {
                    "used_faq": bool(additional_context),
                    "tools_used": tools_used
                }
            }
        
        except Exception as e:
            error_response = (
                "I apologize, but I encountered an error while processing your request. "
                "Please try again, or if you need immediate assistance, you can call our office "
                "at +1-555-123-4567."
            )
            
            return {
                "response": error_response,
                "conversation_history": conversation_history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": error_response}
                ],
                "metadata": {
                    "error": str(e),
                    "used_faq": False,
                    "tools_used": 0
                }
            }
