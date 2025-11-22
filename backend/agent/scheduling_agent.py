from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Any
import os

from backend.agent.prompts import SYSTEM_PROMPT
from backend.tools.availability_tool import availability_tool
from backend.tools.booking_tool import booking_tool
from backend.rag.faq_rag import FAQRetrieval


class SchedulingAgent:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        model_name = os.getenv("LLM_MODEL", "gpt-4o-mini")
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=0.7,
            openai_api_key=api_key
        )
        
        self.faq_retrieval = FAQRetrieval()
        
        self.tools = [availability_tool, booking_tool]
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5
        )
    
    def _convert_history_to_messages(self, history: List[Dict[str, str]]) -> List[Any]:
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        return messages
    
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
                             conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        if conversation_history is None:
            conversation_history = []
        
        try:
            additional_context = ""
            if self._check_if_faq_query(user_message):
                faq_context = self.faq_retrieval.get_context_for_query(user_message)
                additional_context = f"\n\nRelevant Clinic Information:\n{faq_context}\n"
            
            enhanced_message = user_message
            if additional_context:
                enhanced_message = f"{user_message}\n{additional_context}"
            
            chat_history = self._convert_history_to_messages(conversation_history)
            
            result = await self.agent_executor.ainvoke({
                "input": enhanced_message,
                "chat_history": chat_history
            })
            
            response = result.get("output", "I apologize, but I'm having trouble processing your request. Could you please rephrase that?")
            
            updated_history = conversation_history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": response}
            ]
            
            return {
                "response": response,
                "conversation_history": updated_history,
                "metadata": {
                    "used_faq": bool(additional_context),
                    "tools_used": len(result.get("intermediate_steps", []))
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
