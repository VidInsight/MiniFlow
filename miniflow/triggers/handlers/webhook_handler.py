from typing import Dict, Any
import hashlib
import hmac
from datetime import datetime, timezone
from ..base_handler import BaseTriggerHandler


class WebhookTriggerHandler(BaseTriggerHandler):
    """
    Handler for webhook triggers
    
    Webhook triggers listen for HTTP requests on specific endpoints
    and execute workflows when valid requests are received.
    """
    
    def __init__(self, trigger_data: Dict[str, Any], database_orchestrator):
        super().__init__(trigger_data, database_orchestrator)
        
        # Extract webhook-specific config
        self.webhook_id = self.config.get('webhook_id')
        self.secret = self.config.get('secret')
        self.content_type = self.config.get('content_type', 'application/json')
        self.signature_validation = self.config.get('signature_validation', True)
    
    async def start(self) -> bool:
        """
        Start webhook trigger handler
        
        For webhook triggers, 'starting' means the handler is ready to receive requests.
        The actual HTTP endpoint registration happens at the application level.
        """
        if not self.webhook_id:
            self.logger.error("Webhook trigger missing webhook_id")
            return False
        
        self.is_running = True
        self.logger.info(f"Webhook trigger '{self.trigger_name}' started with ID: {self.webhook_id}")
        return True
    
    async def stop(self) -> bool:
        """
        Stop webhook trigger handler
        """
        self.is_running = False
        self.logger.info(f"Webhook trigger '{self.trigger_name}' stopped")
        return True
    
    def get_trigger_type(self) -> str:
        return "WEBHOOK"
    
    async def handle_webhook(self, payload: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Handle incoming webhook request
        
        Args:
            payload: Request payload (parsed JSON)
            headers: Request headers
            
        Returns:
            Dict containing execution information
            
        Raises:
            RuntimeError: If webhook trigger is not active
            ValueError: If webhook signature validation fails
            Exception: If workflow execution fails
        """
        if not self.is_running:
            raise RuntimeError("Webhook trigger is not active")
        
        headers = headers or {}
        
        # Validate webhook signature if secret is provided
        if self.secret and self.signature_validation:
            if not self._validate_signature(payload, headers):
                raise ValueError("Invalid webhook signature")
        
        # Prepare source data with webhook context
        source_data = {
            "webhook_payload": payload,
            "webhook_headers": headers,
            "webhook_timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_id": self.webhook_id,
            "trigger_type": "WEBHOOK",
            "trigger_name": self.trigger_name,
            "trigger_id": self.trigger_id
        }
        
        self.logger.info(f"Processing webhook for workflow {self.workflow_id}", 
                        extra={
                            "webhook_id": self.webhook_id, 
                            "payload_size": len(str(payload)),
                            "trigger_id": self.trigger_id
                        })
        
        return await self.execute_workflow(source_data)
    
    def _validate_signature(self, payload: Dict[str, Any], headers: Dict[str, str]) -> bool:
        """
        Validate webhook signature
        
        Supports common webhook signature formats:
        - X-Webhook-Signature: sha256=<signature>
        - X-Hub-Signature-256: sha256=<signature>
        
        Args:
            payload: Request payload
            headers: Request headers
            
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            # Get signature from headers (try common header names)
            signature_header = (
                headers.get('X-Webhook-Signature') or 
                headers.get('X-Hub-Signature-256') or
                headers.get('x-webhook-signature') or
                headers.get('x-hub-signature-256')
            )
            
            if not signature_header:
                self.logger.warning("No signature header found in webhook request")
                return False
            
            # Create expected signature
            import json
            payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')
            expected_signature = hmac.new(
                self.secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            # Extract signature from header (remove 'sha256=' prefix if present)
            received_signature = signature_header.replace('sha256=', '')
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(expected_signature, received_signature)
            
            if not is_valid:
                self.logger.warning("Webhook signature validation failed",
                                  extra={"webhook_id": self.webhook_id})
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Signature validation error: {str(e)}", 
                            extra={"webhook_id": self.webhook_id})
            return False
    
    def get_webhook_endpoint(self) -> str:
        """
        Get the webhook endpoint URL
        
        Returns:
            str: Webhook endpoint path
        """
        return f"/api/bff/triggers/webhook/{self.webhook_id}"
    
    def get_webhook_info(self) -> Dict[str, Any]:
        """
        Get webhook configuration information
        
        Returns:
            Dict with webhook info (safe for external consumption)
        """
        return {
            "webhook_id": self.webhook_id,
            "endpoint": self.get_webhook_endpoint(),
            "content_type": self.content_type,
            "signature_validation": self.signature_validation,
            "secret_configured": bool(self.secret),
            "trigger_name": self.trigger_name,
            "workflow_id": self.workflow_id
        }
