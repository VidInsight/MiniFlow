"""
Webhook Response Script
Handles sending responses back to webhook callers
"""

import requests
import json
from typing import Dict, Any


def module():
    return WebhookResponseModule()


class WebhookResponseModule:
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send response back to webhook caller
        
        Expected context:
        {
            "webhook_response": dict,  # Response data from LLM
            "webhook_payload": dict,   # Original webhook data
            "webhook_headers": dict,   # Original webhook headers
            "response_url": str,       # Optional response URL
            "response_method": str     # HTTP method (default: POST)
        }
        
        Returns:
        {
            "response_sent": bool,
            "response_status": int,
            "response_data": dict,
            "webhook_response": dict  # Echo back the response that was sent
        }
        """
        try:
            webhook_response = context.get("webhook_response", {})
            webhook_payload = context.get("webhook_payload", {})
            webhook_headers = context.get("webhook_headers", {})
            response_url = context.get("response_url")
            response_method = context.get("response_method", "POST").upper()
            
            # If no explicit response URL, try to extract from webhook payload
            if not response_url:
                response_url = self._extract_response_url(webhook_payload, webhook_headers)
            
            # If we have a response URL, send the response
            if response_url:
                response_data = self._send_webhook_response(
                    response_url, 
                    webhook_response, 
                    response_method,
                    webhook_payload
                )
                
                return {
                    "response_sent": True,
                    "response_status": response_data.get("status_code", 200),
                    "response_data": response_data,
                    "webhook_response": webhook_response,
                    "response_url": response_url,
                    "success": True
                }
            else:
                # No response URL available, just return the response
                return {
                    "response_sent": False,
                    "response_status": 200,
                    "webhook_response": webhook_response,
                    "message": "No response URL available, response data prepared",
                    "success": True
                }
                
        except Exception as e:
            return {
                "response_sent": False,
                "error": f"Error sending webhook response: {str(e)}",
                "webhook_response": webhook_response,
                "success": False
            }
    
    def _extract_response_url(self, webhook_payload: Dict[str, Any], webhook_headers: Dict[str, Any]) -> str:
        """Extract response URL from webhook data"""
        # Common response URL fields
        url_fields = [
            "response_url", "callback_url", "reply_url", 
            "webhook_url", "response_endpoint"
        ]
        
        # Check payload for response URL
        for field in url_fields:
            if field in webhook_payload:
                return webhook_payload[field]
        
        # Check headers for response URL
        for field in url_fields:
            header_key = f"x-{field.replace('_', '-')}"
            if header_key in webhook_headers:
                return webhook_headers[header_key]
        
        # Platform-specific response URL extraction
        if "slack" in str(webhook_payload).lower():
            return webhook_payload.get("response_url")
        
        return None
    
    def _send_webhook_response(self, url: str, response_data: Dict[str, Any], 
                              method: str, original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send HTTP response to webhook URL"""
        try:
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "MiniFlow-Chatbot/1.0"
            }
            
            # Platform-specific formatting
            formatted_response = self._format_platform_response(response_data, original_payload)
            
            if method == "POST":
                response = requests.post(url, json=formatted_response, headers=headers, timeout=10)
            elif method == "PUT":
                response = requests.put(url, json=formatted_response, headers=headers, timeout=10)
            elif method == "PATCH":
                response = requests.patch(url, json=formatted_response, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return {
                "status_code": response.status_code,
                "response_text": response.text,
                "success": response.status_code < 400,
                "sent_data": formatted_response
            }
            
        except requests.exceptions.Timeout:
            raise Exception("Response request timed out")
        except requests.exceptions.ConnectionError:
            raise Exception("Failed to connect to response URL")
        except Exception as e:
            raise Exception(f"Failed to send response: {str(e)}")
    
    def _format_platform_response(self, response_data: Dict[str, Any], 
                                 original_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Format response for specific platforms"""
        
        # Check if platform-specific formatting is already included
        if "slack" in response_data:
            return response_data["slack"]
        elif "discord" in response_data:
            return response_data["discord"]
        elif "telegram" in response_data:
            return response_data["telegram"]
        
        # Default formatting based on original payload analysis
        webhook_source = str(original_payload).lower()
        
        if "slack" in webhook_source:
            return {
                "text": response_data.get("text", ""),
                "response_type": "in_channel"
            }
        elif "discord" in webhook_source:
            return {
                "type": 4,  # CHANNEL_MESSAGE_WITH_SOURCE
                "data": {
                    "content": response_data.get("text", "")
                }
            }
        elif "telegram" in webhook_source:
            return {
                "method": "sendMessage",
                "text": response_data.get("text", ""),
                "chat_id": original_payload.get("message", {}).get("chat", {}).get("id")
            }
        else:
            # Generic JSON response
            return {
                "message": response_data.get("text", ""),
                "type": "bot_response",
                "timestamp": response_data.get("timestamp")
            }