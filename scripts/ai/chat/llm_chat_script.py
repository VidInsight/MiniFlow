"""
LLM Chat Script for webhook-based chatbot
Processes incoming chat messages and generates responses using a language model
"""

import requests
import json
from typing import Dict, Any, Optional


def module():
    return LLMChatModule()


class LLMChatModule:
    def __init__(self):
        self.api_key = None  # Will be set from environment variables
        self.model = "gpt-3.5-turbo"  # Default model
        self.max_tokens = 150
        self.temperature = 0.7
        
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process chat message and generate response
        
        Expected context:
        {
            "user_message": str,  # The user message
            "chat_history": list, # Optional chat history
            "webhook_payload": dict,  # Original webhook data
            "api_key": str,  # OpenAI API key (from env vars)
            "model": str,  # Optional model override
            "max_tokens": int,  # Optional max tokens override
            "temperature": float,  # Optional temperature override
            "system_prompt": str  # Optional system prompt
        }
        
        Returns:
        {
            "bot_response": str,
            "user_message": str,
            "timestamp": str,
            "model_used": str,
            "tokens_used": int,
            "webhook_response": dict  # Formatted response for webhook
        }
        """
        try:
            # Extract parameters from context
            user_message = context.get("user_message", "")
            chat_history = context.get("chat_history", [])
            webhook_payload = context.get("webhook_payload", {})
            
            # Check if we have a user message
            if not user_message:
                # Try to extract message from webhook payload
                user_message = self._extract_message_from_webhook(webhook_payload)
            
            if not user_message:
                return {
                    "error": "No user message found",
                    "bot_response": "I am sorry, I did not receive a message to respond to.",
                    "webhook_response": {
                        "text": "I am sorry, I did not receive a message to respond to.",
                        "type": "error"
                    }
                }
            
            # Set up API parameters
            self.api_key = context.get("api_key")
            self.model = context.get("model", self.model)
            self.max_tokens = context.get("max_tokens", self.max_tokens)
            self.temperature = context.get("temperature", self.temperature)
            system_prompt = context.get("system_prompt", "You are a helpful AI assistant.")
            
            if not self.api_key:
                # Fallback response without OpenAI - intelligent fallback
                bot_response = self._generate_fallback_response(user_message, system_prompt)
            else:
                # Generate response using OpenAI API
                bot_response = self._generate_response(
                    user_message, 
                    chat_history, 
                    system_prompt
                )
            
            # Format webhook response
            webhook_response = self._format_webhook_response(bot_response, webhook_payload)
            
            return {
                "bot_response": bot_response,
                "user_message": user_message,
                "timestamp": self._get_timestamp(),
                "model_used": self.model,
                "tokens_used": self._estimate_tokens(user_message + bot_response),
                "webhook_response": webhook_response,
                "success": True
            }
            
        except Exception as e:
            error_message = f"Error processing chat: {str(e)}"
            return {
                "error": error_message,
                "bot_response": "I am sorry, I encountered an error while processing your message.",
                "webhook_response": {
                    "text": "I am sorry, I encountered an error while processing your message.",
                    "type": "error"
                },
                "success": False
            }
    
    def _extract_message_from_webhook(self, webhook_payload: Dict[str, Any]) -> str:
        """Extract user message from webhook payload"""
        # Common webhook formats
        message_fields = [
            "message", "text", "content", "body", 
            "user_message", "query", "input"
        ]
        
        for field in message_fields:
            if field in webhook_payload:
                return str(webhook_payload[field])
        
        # Check nested structures
        if "message" in webhook_payload and isinstance(webhook_payload["message"], dict):
            for field in message_fields:
                if field in webhook_payload["message"]:
                    return str(webhook_payload["message"][field])
        
        return ""
    
    def _generate_response(self, user_message: str, chat_history: list, system_prompt: str) -> str:
        """Generate response using OpenAI API"""
        try:
            # Prepare messages for the API
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add chat history if provided
            for history_item in chat_history[-10:]:  # Limit to last 10 messages
                if "user" in history_item:
                    messages.append({"role": "user", "content": history_item["user"]})
                if "assistant" in history_item:
                    messages.append({"role": "assistant", "content": history_item["assistant"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Make API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                error_detail = response.text
                raise Exception(f"OpenAI API error ({response.status_code}): {error_detail}")
                
        except requests.exceptions.Timeout:
            return "I am sorry, my response took too long. Please try again."
        except requests.exceptions.ConnectionError:
            return "I am sorry, I am having trouble connecting to my language model. Please try again later."
        except Exception as e:
            raise Exception(f"Failed to generate response: {str(e)}")
    
    def _format_webhook_response(self, bot_response: str, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for webhook caller"""
        # Basic response format
        response = {
            "text": bot_response,
            "type": "bot_response",
            "timestamp": self._get_timestamp()
        }
        
        # Add platform-specific formatting if needed
        webhook_source = webhook_payload.get("source", "").lower()
        
        if "slack" in webhook_source:
            response["slack"] = {
                "text": bot_response,
                "response_type": "in_channel"
            }
        elif "discord" in webhook_source:
            response["discord"] = {
                "content": bot_response,
                "type": 4  # CHANNEL_MESSAGE_WITH_SOURCE
            }
        elif "telegram" in webhook_source:
            response["telegram"] = {
                "method": "sendMessage",
                "text": bot_response
            }
        
        return response
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def _generate_fallback_response(self, user_message: str, system_prompt: str) -> str:
        """Generate intelligent fallback response without OpenAI API"""
        user_lower = user_message.lower()
        
        # Turkish/English detection
        turkish_keywords = ['merhaba', 'nasıl', 'nedir', 'türkçe', 'miniflow', 'workflow', 'teşekkür']
        is_turkish = any(keyword in user_lower for keyword in turkish_keywords)
        
        # MiniFlow-specific responses
        if 'miniflow' in user_lower:
            if is_turkish:
                return "Merhaba! MiniFlow hakkında sorularınız var mı? Ben MiniFlow chatbot'uyum ve workflow otomasyonu konularında yardımcı olabilirim. API key ekleyerek daha gelişmiş AI yeteneklerimi aktif edebilirsiniz!"
            else:
                return "Hello! I'm the MiniFlow chatbot! I can help you with workflow automation questions. Add an OpenAI API key to unlock my full AI capabilities!"
        
        if any(word in user_lower for word in ['workflow', 'automation', 'trigger', 'node']):
            if is_turkish:
                return f"'{user_message}' konusunda size yardımcı olmaya çalışacağım. MiniFlow workflow otomasyon sistemi ile ilgili sorularınız varsa çekinmeyin!"
            else:
                return f"I'd be happy to help with '{user_message}'. I'm here to assist with MiniFlow workflow automation questions!"
        
        if any(word in user_lower for word in ['merhaba', 'hello', 'hi', 'hey']):
            if is_turkish:
                return "Merhaba! MiniFlow AI asistanınızım. Size nasıl yardımcı olabilirim? Workflow, trigger ve automation konularında uzmanım!"
            else:
                return "Hello! I'm your MiniFlow AI assistant. How can I help you? I specialize in workflows, triggers, and automation!"
        
        if any(word in user_lower for word in ['teşekkür', 'thanks', 'thank you', 'sağol']):
            if is_turkish:
                return "Rica ederim! MiniFlow ile ilgili başka sorularınız olursa her zaman buradayım."
            else:
                return "You're welcome! I'm always here if you have more MiniFlow questions."
        
        # Default intelligent response
        if is_turkish:
            return f"Mesajınızı aldım: '{user_message}'. Ben MiniFlow'un AI chatbot'uyum. Daha akıllı yanıtlar için OpenAI API key ekleyebilirsiniz, ama şimdilik elimden geldiğince yardımcı olmaya çalışacağım!"
        else:
            return f"I received your message: '{user_message}'. I'm MiniFlow's AI chatbot. While I can give smarter responses with an OpenAI API key, I'll do my best to help you now!"

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count"""
        # Rough approximation: 1 token ≈ 4 characters
        return len(text) // 4