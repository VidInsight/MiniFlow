from typing import Dict, Any, Optional, List
import asyncio
from miniflow.core.logger import get_logger
from miniflow.core.monitoring.components import MonitorableComponent

from .base_handler import BaseTriggerHandler
from .handlers.manual_handler import ManualTriggerHandler
from .handlers.scheduled_handler import ScheduledTriggerHandler
from .handlers.webhook_handler import WebhookTriggerHandler


class TriggerManager(MonitorableComponent):
    """
    Central trigger management system
    
    Manages the lifecycle of all trigger handlers:
    - Loads active triggers from database
    - Creates and starts appropriate handlers
    - Manages handler lifecycle (start/stop/reload)
    - Provides API for manual trigger execution and webhook handling
    """
    
    def __init__(self, database_orchestrator):
        self.orchestrator = database_orchestrator
        self.logger = get_logger("trigger_manager")
        self.active_handlers: Dict[str, BaseTriggerHandler] = {}
        self.running = False
        
        # Handler registry - maps trigger types to handler classes
        self.handler_registry = {
            "MANUAL": ManualTriggerHandler,
            "SCHEDULED": ScheduledTriggerHandler,
            "WEBHOOK": WebhookTriggerHandler,
        }
        
        # Metrics for monitoring
        self.metrics = {
            'active_triggers': 0,
            'total_executions': 0,
            'failed_executions': 0,
            'handlers_started': 0,
            'handlers_failed': 0,
            'by_type': {
                'manual': 0,
                'scheduled': 0,
                'webhook': 0
            }
        }
    
    def get_component_name(self) -> str:
        return "TriggerManager"

    def get_component_metrics(self) -> Dict[str, Any]:
        return self.metrics

    def is_running(self) -> bool:
        return self.running

    def get_component_config(self) -> Dict[str, Any]:
        """Get component configuration"""
        return {
            'handler_registry': list(self.handler_registry.keys()),
            'active_handlers_count': len(self.active_handlers),
            'running': self.running
        }

    def set_component_config(self, config: Dict[str, Any]) -> bool:
        """Set component configuration"""
        # TriggerManager config is mostly runtime state, not configurable
        return True

    async def start(self) -> bool:
        """
        Start trigger manager and load all active triggers
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.running:
            self.logger.warning("TriggerManager already running")
            return True
            
        self.logger.info("Starting TriggerManager")
        
        try:
            # Load all active triggers from database
            active_triggers = self.orchestrator.trigger_orchestrator.get_active_triggers()
            
            # Initialize and start each trigger handler
            started_count = 0
            failed_count = 0
            
            for trigger in active_triggers:
                success = await self._start_trigger_handler(trigger)
                if success:
                    started_count += 1
                    # Update type metrics
                    trigger_type = trigger['trigger_type'].lower()
                    if trigger_type in self.metrics['by_type']:
                        self.metrics['by_type'][trigger_type] += 1
                else:
                    failed_count += 1
            
            self.running = True
            self.metrics['handlers_started'] = started_count
            self.metrics['handlers_failed'] = failed_count
            self.metrics['active_triggers'] = len(self.active_handlers)
            
            self.logger.info(f"TriggerManager started successfully: {started_count} handlers started, {failed_count} failed")
            # Return true even if no triggers - system is ready
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start TriggerManager: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop trigger manager and all handlers
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.running:
            return True
        
        self.logger.info("Stopping TriggerManager")
        
        try:
            # Stop all handlers
            stop_tasks = []
            for handler in self.active_handlers.values():
                stop_tasks.append(handler.stop())
            
            if stop_tasks:
                await asyncio.gather(*stop_tasks, return_exceptions=True)
            
            self.active_handlers.clear()
            self.running = False
            self.metrics['active_triggers'] = 0
            self.metrics['by_type'] = {'manual': 0, 'scheduled': 0, 'webhook': 0}
            
            self.logger.info("TriggerManager stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping TriggerManager: {str(e)}")
            return False
    
    async def _start_trigger_handler(self, trigger: Dict[str, Any]) -> bool:
        """
        Start individual trigger handler
        
        Args:
            trigger: Trigger data from database
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        trigger_type = trigger['trigger_type']
        handler_class = self.handler_registry.get(trigger_type)
        
        if not handler_class:
            self.logger.warning(f"No handler found for trigger type: {trigger_type}")
            return False
        
        try:
            handler = handler_class(trigger, self.orchestrator)
            success = await handler.start()
            
            if success:
                self.active_handlers[trigger['id']] = handler
                self.logger.info(f"Started trigger handler: {trigger['name']} ({trigger_type})")
                return True
            else:
                self.logger.error(f"Failed to start trigger handler: {trigger['name']}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting trigger handler {trigger['name']}: {str(e)}")
            return False
    
    async def reload_trigger(self, trigger_id: str) -> bool:
        """
        Reload a specific trigger
        
        Stops existing handler (if running) and starts new one with current database state.
        
        Args:
            trigger_id: ID of trigger to reload
            
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        try:
            # Stop existing handler if running
            if trigger_id in self.active_handlers:
                await self.active_handlers[trigger_id].stop()
                del self.active_handlers[trigger_id]
                
                # Update metrics
                self.metrics['active_triggers'] = len(self.active_handlers)
            
            # Load updated trigger data
            trigger = self.orchestrator.trigger_orchestrator.get_by_id(trigger_id)
            if not trigger:
                self.logger.info(f"Trigger {trigger_id} not found - removed from handlers")
                return True
            
            if trigger['status'] != 'ACTIVE':
                self.logger.info(f"Trigger {trigger_id} is not active - not starting handler")
                return True
            
            # Start new handler
            success = await self._start_trigger_handler(trigger)
            if success:
                self.metrics['active_triggers'] = len(self.active_handlers)
                # Update type metrics
                self._update_type_metrics()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error reloading trigger {trigger_id}: {str(e)}")
            return False
    
    def _update_type_metrics(self):
        """Update metrics by trigger type"""
        type_counts = {'manual': 0, 'scheduled': 0, 'webhook': 0}
        
        for handler in self.active_handlers.values():
            trigger_type = handler.get_trigger_type().lower()
            if trigger_type in type_counts:
                type_counts[trigger_type] += 1
        
        self.metrics['by_type'] = type_counts
    
    # ==========================================
    # API METHODS FOR TRIGGER EXECUTION
    # ==========================================
    
    async def trigger_manual(self, trigger_id: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Manually trigger a MANUAL type trigger
        
        Args:
            trigger_id: ID of manual trigger
            input_data: Optional input data for the trigger
            
        Returns:
            Dict containing execution information
            
        Raises:
            ValueError: If trigger not found or not manual type
            RuntimeError: If trigger not active
        """
        handler = self.active_handlers.get(trigger_id)
        if not handler:
            # Try to load the trigger on-demand
            trigger_data = self.orchestrator.trigger_orchestrator.get_by_id(trigger_id)
            if not trigger_data or trigger_data.get('status') != 'ACTIVE':
                raise ValueError(f"Trigger {trigger_id} not found or not active")
            
            # Start the handler for this trigger
            success = await self._start_trigger_handler(trigger_data)
            if not success:
                raise ValueError(f"Failed to start handler for trigger {trigger_id}")
            
            handler = self.active_handlers.get(trigger_id)
            if not handler:
                raise ValueError(f"Trigger {trigger_id} handler could not be loaded")
        
        if not isinstance(handler, ManualTriggerHandler):
            raise ValueError(f"Trigger {trigger_id} is not a manual trigger")
        
        self.metrics['total_executions'] += 1
        
        try:
            result = await handler.trigger_manually(input_data)
            return result
        except Exception as e:
            self.metrics['failed_executions'] += 1
            raise
    
    async def handle_webhook(self, webhook_id: str, payload: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Handle incoming webhook
        
        Args:
            webhook_id: Webhook ID from URL
            payload: Request payload
            headers: Request headers
            
        Returns:
            Dict containing execution information
            
        Raises:
            ValueError: If webhook not found or multiple webhooks found
            RuntimeError: If webhook trigger not active
        """
        # Find webhook trigger by webhook_id
        webhook_handler = None
        matching_handlers = []
        
        for handler in self.active_handlers.values():
            if (isinstance(handler, WebhookTriggerHandler) and 
                handler.webhook_id == webhook_id):
                matching_handlers.append(handler)
        
        if not matching_handlers:
            raise ValueError(f"Webhook {webhook_id} not found or not active")
        
        if len(matching_handlers) > 1:
            # Multiple triggers can share same webhook_id - execute all
            self.logger.info(f"Multiple triggers found for webhook {webhook_id}, executing all")
            results = []
            
            for handler in matching_handlers:
                self.metrics['total_executions'] += 1
                try:
                    result = await handler.handle_webhook(payload, headers)
                    results.append(result)
                except Exception as e:
                    self.metrics['failed_executions'] += 1
                    self.logger.error(f"Failed to execute webhook trigger {handler.trigger_id}: {str(e)}")
                    # Continue with other triggers
            
            return {"executions": results, "webhook_id": webhook_id}
        
        else:
            # Single trigger
            webhook_handler = matching_handlers[0]
            self.metrics['total_executions'] += 1
            
            try:
                result = await webhook_handler.handle_webhook(payload, headers)
                return result
            except Exception as e:
                self.metrics['failed_executions'] += 1
                raise
    
    def get_webhook_info(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """
        Get webhook information
        
        Args:
            webhook_id: Webhook ID
            
        Returns:
            Dict with webhook info, or None if not found
        """
        for handler in self.active_handlers.values():
            if (isinstance(handler, WebhookTriggerHandler) and 
                handler.webhook_id == webhook_id):
                return handler.get_webhook_info()
        
        return None
    
    def get_all_webhooks(self) -> List[Dict[str, Any]]:
        """
        Get information about all active webhooks
        
        Returns:
            List of webhook info dictionaries
        """
        webhooks = []
        for handler in self.active_handlers.values():
            if isinstance(handler, WebhookTriggerHandler):
                webhooks.append(handler.get_webhook_info())
        
        return webhooks
    
    def get_handler_status(self, trigger_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific trigger handler
        
        Args:
            trigger_id: Trigger ID
            
        Returns:
            Dict with handler status, or None if not found
        """
        handler = self.active_handlers.get(trigger_id)
        if handler:
            return handler.get_status()
        return None
    
    def get_all_handlers_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all active handlers
        
        Returns:
            List of handler status dictionaries
        """
        return [handler.get_status() for handler in self.active_handlers.values()]
