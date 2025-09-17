from typing import Dict, Any
from datetime import datetime, timezone
from ..base_handler import BaseTriggerHandler


class ManualTriggerHandler(BaseTriggerHandler):
    def __init__(self, trigger_data: Dict[str, Any], database_orchestrator):
        super().__init__(trigger_data, database_orchestrator)
    
    async def start(self) -> bool:
        self.is_running = True
        self.logger.info(f"Manual trigger '{self.trigger_name}' is ready for execution")
        return True
    
    async def stop(self) -> bool:
        self.is_running = False
        self.logger.info(f"Manual trigger '{self.trigger_name}' stopped")
        return True
    
    def get_trigger_type(self) -> str:
        return "MANUAL"
    
    async def trigger_manually(self, manual_input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.is_running:
            raise RuntimeError("Manual trigger is not active")
        
        # Use provided data or empty dict
        source_data = manual_input_data or {}
        
        # Add some metadata about the manual trigger
        source_data.update({
            "trigger_type": "MANUAL",
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "trigger_name": self.trigger_name,
            "trigger_id": self.trigger_id
        })
        
        self.logger.info(f"Manually triggering workflow {self.workflow_id}", 
                        extra={"manual_data": manual_input_data, "trigger_id": self.trigger_id})
        
        return await self.execute_workflow(source_data)
