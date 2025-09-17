from typing import Dict, Any
import asyncio
from datetime import datetime, timezone
from ..base_handler import BaseTriggerHandler


class ScheduledTriggerHandler(BaseTriggerHandler):
    """
    Handler for scheduled (time-based) triggers
    
    Scheduled triggers execute workflows automatically based on:
    - Cron expressions (e.g., "0 9 * * *" for daily at 9 AM)
    - Interval seconds (e.g., 3600 for every hour)
    """
    
    def __init__(self, trigger_data: Dict[str, Any], database_orchestrator):
        super().__init__(trigger_data, database_orchestrator)
        
        # Extract schedule-specific config
        self.cron_expression = self.config.get('cron')
        self.interval_seconds = self.config.get('interval_seconds')
        self.timezone = self.config.get('timezone', 'UTC')
        
        # Runtime state
        self.scheduler_task = None
        self.next_execution_time = None
    
    async def start(self) -> bool:
        """
        Start scheduled trigger handler
        
        Creates background task for scheduling logic.
        """
        if not self.cron_expression and not self.interval_seconds:
            self.logger.error("Scheduled trigger missing cron or interval_seconds")
            return False
        
        try:
            # Start scheduler task
            self.scheduler_task = asyncio.create_task(self._scheduler_loop())
            self.is_running = True
            
            schedule_info = f"cron: {self.cron_expression}" if self.cron_expression else f"interval: {self.interval_seconds}s"
            self.logger.info(f"Scheduled trigger '{self.trigger_name}' started with {schedule_info}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduled trigger: {str(e)}")
            return False
    
    async def stop(self) -> bool:
        """
        Stop scheduled trigger handler
        
        Cancels the background scheduler task.
        """
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(f"Scheduled trigger '{self.trigger_name}' stopped")
        return True
    
    def get_trigger_type(self) -> str:
        return "SCHEDULED"
    
    async def _scheduler_loop(self):
        """
        Main scheduler loop
        
        Runs continuously and executes the trigger based on schedule.
        """
        try:
            if self.cron_expression:
                await self._cron_scheduler()
            else:
                await self._interval_scheduler()
        except asyncio.CancelledError:
            self.logger.info(f"Scheduled trigger '{self.trigger_name}' cancelled")
        except Exception as e:
            self.logger.error(f"Scheduler loop error: {str(e)}")
            # Mark trigger as error status
            try:
                self.orchestrator.trigger_orchestrator.mark_error(self.trigger_id, str(e))
            except Exception:
                pass  # Don't fail on status update error
    
    async def _cron_scheduler(self):
        """
        Cron-based scheduler
        
        Uses croniter library for cron expression parsing.
        Note: croniter needs to be added to requirements.txt
        """
        try:
            from croniter import croniter
        except ImportError:
            self.logger.error("croniter library not available. Install with: pip install croniter")
            return
        
        cron = croniter(self.cron_expression, datetime.now(timezone.utc))
        
        while self.is_running:
            try:
                next_run = cron.get_next(datetime)
                self.next_execution_time = next_run
                now = datetime.now(timezone.utc)
                
                # Calculate sleep time until next execution
                sleep_seconds = (next_run - now).total_seconds()
                
                self.logger.debug(f"Next execution scheduled for {next_run} (in {sleep_seconds:.1f} seconds)")
                
                if sleep_seconds > 0:
                    await asyncio.sleep(sleep_seconds)
                
                if self.is_running:
                    await self._execute_scheduled_trigger()
                    
            except Exception as e:
                self.logger.error(f"Error in cron scheduler: {str(e)}")
                # Wait a bit before retrying to avoid rapid loops
                await asyncio.sleep(60)
    
    async def _interval_scheduler(self):
        """
        Interval-based scheduler
        
        Executes the trigger every N seconds.
        """
        while self.is_running:
            try:
                # Calculate next execution time
                self.next_execution_time = datetime.now(timezone.utc)
                
                await asyncio.sleep(self.interval_seconds)
                
                if self.is_running:
                    await self._execute_scheduled_trigger()
                    
            except Exception as e:
                self.logger.error(f"Error in interval scheduler: {str(e)}")
                # Wait a bit before retrying
                await asyncio.sleep(min(60, self.interval_seconds // 2))
    
    async def _execute_scheduled_trigger(self):
        """
        Execute the scheduled trigger
        
        Creates execution context and triggers the workflow.
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            source_data = {
                "scheduled_time": current_time.isoformat(),
                "trigger_name": self.trigger_name,
                "trigger_type": "SCHEDULED",
                "trigger_id": self.trigger_id,
                "cron_expression": self.cron_expression,
                "interval_seconds": self.interval_seconds,
                "timezone": self.timezone
            }
            
            self.logger.info(f"Executing scheduled trigger for workflow {self.workflow_id}",
                           extra={"scheduled_time": current_time.isoformat(), "trigger_id": self.trigger_id})
            
            execution_result = await self.execute_workflow(source_data)
            
            if execution_result:
                self.logger.info(f"Scheduled trigger executed successfully",
                               extra={
                                   "trigger_id": self.trigger_id,
                                   "execution_id": execution_result.get('id'),
                                   "workflow_id": self.workflow_id
                               })
            else:
                self.logger.warning(f"Scheduled trigger execution returned no result",
                                  extra={"trigger_id": self.trigger_id, "workflow_id": self.workflow_id})
            
        except Exception as e:
            self.logger.error(f"Scheduled trigger execution failed: {str(e)}", 
                            extra={
                                "trigger_id": self.trigger_id,
                                "workflow_id": self.workflow_id,
                                "error_type": type(e).__name__
                            }, exc_info=True)
            
            # Try to mark trigger as error status for monitoring
            try:
                if hasattr(self.orchestrator, 'trigger_orchestrator'):
                    self.orchestrator.trigger_orchestrator.mark_execution_error(
                        self.trigger_id, str(e)
                    )
            except Exception as mark_error:
                self.logger.warning(f"Failed to mark trigger error status: {str(mark_error)}")
            
            # Don't re-raise - we want the scheduler to continue running
    
    def get_schedule_info(self) -> Dict[str, Any]:
        """
        Get schedule information
        
        Returns:
            Dict with schedule details
        """
        return {
            "trigger_type": "SCHEDULED",
            "cron_expression": self.cron_expression,
            "interval_seconds": self.interval_seconds,
            "timezone": self.timezone,
            "next_execution_time": self.next_execution_time.isoformat() if self.next_execution_time else None,
            "is_running": self.is_running
        }
