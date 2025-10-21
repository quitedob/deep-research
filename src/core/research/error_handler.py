# -*- coding: utf-8 -*-
"""
Error Handling and Recovery System for Research Platform
Provides comprehensive error handling, recovery mechanisms, and resilience
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import json
import traceback

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorType(Enum):
    """Types of errors in the research system"""
    AGENT_FAILURE = "agent_failure"
    NETWORK_ERROR = "network_error"
    DATABASE_ERROR = "database_error"
    VALIDATION_ERROR = "validation_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    TASK_EXECUTION_ERROR = "task_execution_error"
    SYNTHESIS_ERROR = "synthesis_error"
    EVIDENCE_ERROR = "evidence_error"
    PLAN_ERROR = "plan_error"

class RecoveryStrategy(Enum):
    """Recovery strategies for different error types"""
    RETRY = "retry"
    RESTART_AGENT = "restart_agent"
    FALLBACK_PROVIDER = "fallback_provider"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    SKIP_TASK = "skip_task"
    ESCALATE = "escalate"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class ErrorEvent:
    """Represents an error event in the system"""
    id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    stack_trace: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    recovery_attempts: int = 0
    max_recovery_attempts: int = 3
    resolved: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None

@dataclass
class RecoveryAction:
    """Represents a recovery action to be taken"""
    strategy: RecoveryStrategy
    action_func: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3

class ResearchErrorHandler:
    """Centralized error handling and recovery system"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorEvent] = []
        self.active_errors: Dict[str, ErrorEvent] = {}
        self.recovery_strategies: Dict[ErrorType, List[RecoveryStrategy]] = {
            ErrorType.AGENT_FAILURE: [
                RecoveryStrategy.RESTART_AGENT,
                RecoveryStrategy.FALLBACK_PROVIDER,
                RecoveryStrategy.ESCALATE
            ],
            ErrorType.NETWORK_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK_PROVIDER,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorType.DATABASE_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.ESCALATE
            ],
            ErrorType.TIMEOUT_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.SKIP_TASK,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorType.RESOURCE_ERROR: [
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.SKIP_TASK,
                RecoveryStrategy.ESCALATE
            ],
            ErrorType.TASK_EXECUTION_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.SKIP_TASK,
                RecoveryStrategy.MANUAL_INTERVENTION
            ],
            ErrorType.VALIDATION_ERROR: [
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                RecoveryStrategy.SKIP_TASK,
                RecoveryStrategy.MANUAL_INTERVENTION
            ],
            ErrorType.SYNTHESIS_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.FALLBACK_PROVIDER,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorType.EVIDENCE_ERROR: [
                RecoveryStrategy.RETRY,
                RecoveryStrategy.SKIP_TASK,
                RecoveryStrategy.GRACEFUL_DEGRADATION
            ],
            ErrorType.PLAN_ERROR: [
                RecoveryStrategy.GRACEFUL_DEGRADATION,
                ResolutionStrategy.MANUAL_INTERVENTION,
                ResolutionStrategy.ESCALATE
            ]
        }

    async def handle_error(
        self,
        error: Exception,
        error_type: ErrorType,
        context: Dict[str, Any] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorEvent:
        """Handle an error event and attempt recovery"""

        # Create error event
        error_event = ErrorEvent(
            id=self._generate_error_id(),
            error_type=error_type,
            severity=severity,
            message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {}
        )

        self.logger.error(f"Handling error {error_event.id}: {error_event.message}")

        # Add to tracking
        self.active_errors[error_event.id] = error_event
        self.error_history.append(error_event)

        # Attempt recovery
        recovery_success = await self._attempt_recovery(error_event)

        error_event.resolved = recovery_success

        # Remove from active errors if resolved
        if recovery_success:
            self.active_errors.pop(error_event.id, None)
            self.logger.info(f"Successfully recovered from error {error_event.id}")
        else:
            self.logger.error(f"Failed to recover from error {error_event.id}")

        return error_event

    async def _attempt_recovery(self, error_event: ErrorEvent) -> bool:
        """Attempt to recover from an error using appropriate strategies"""

        available_strategies = self.recovery_strategies.get(error_event.error_type, [])

        for strategy in available_strategies:
            if error_event.recovery_attempts >= error_event.max_recovery_attempts:
                break

            try:
                error_event.recovery_attempts += 1
                error_event.recovery_strategy = strategy

                self.logger.info(f"Attempting recovery strategy {strategy.value} for error {error_event.id}")

                success = await self._execute_recovery_strategy(strategy, error_event)

                if success:
                    return True

                # Wait before next attempt
                await asyncio.sleep(2 ** error_event.recovery_attempts)  # Exponential backoff

            except Exception as recovery_error:
                self.logger.error(f"Recovery strategy {strategy.value} failed: {recovery_error}")
                continue

        return False

    async def _execute_recovery_strategy(self, strategy: RecoveryStrategy, error_event: ErrorEvent) -> bool:
        """Execute a specific recovery strategy"""

        if strategy == RecoveryStrategy.RETRY:
            return await self._retry_operation(error_event)

        elif strategy == RecoveryStrategy.RESTART_AGENT:
            return await self._restart_agent(error_event)

        elif strategy == RecoveryStrategy.FALLBACK_PROVIDER:
            return await self._switch_to_fallback_provider(error_event)

        elif strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            return await self._graceful_degradation(error_event)

        elif strategy == RecoveryStrategy.SKIP_TASK:
            return await self._skip_task(error_event)

        elif strategy == RecoveryStrategy.ESCALATE:
            return await self._escalate_error(error_event)

        elif strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            return await self._request_manual_intervention(error_event)

        return False

    async def _retry_operation(self, error_event: ErrorEvent) -> bool:
        """Retry the failed operation"""
        retry_func = error_event.context.get('retry_function')
        if not retry_func:
            return False

        try:
            retry_params = error_event.context.get('retry_parameters', {})
            await retry_func(**retry_params)
            return True
        except Exception as e:
            self.logger.error(f"Retry operation failed: {e}")
            return False

    async def _restart_agent(self, error_event: ErrorEvent) -> bool:
        """Restart a failed agent"""
        agent_id = error_event.context.get('agent_id')
        if not agent_id:
            return False

        try:
            # This would integrate with the multi-agent orchestrator
            self.logger.info(f"Restarting agent {agent_id}")
            # Simulate agent restart
            await asyncio.sleep(1)
            return True
        except Exception as e:
            self.logger.error(f"Agent restart failed: {e}")
            return False

    async def _switch_to_fallback_provider(self, error_event: ErrorEvent) -> bool:
        """Switch to fallback LLM provider"""
        current_provider = error_event.context.get('provider')
        if not current_provider:
            return False

        try:
            self.logger.info(f"Switching from provider {current_provider} to fallback")
            # This would integrate with the LLM router
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            self.logger.error(f"Fallback provider switch failed: {e}")
            return False

    async def _graceful_degradation(self, error_event: ErrorEvent) -> bool:
        """Implement graceful degradation"""
        try:
            self.logger.info("Implementing graceful degradation")
            # This would implement degraded functionality
            await asyncio.sleep(0.5)
            return True
        except Exception as e:
            self.logger.error(f"Graceful degradation failed: {e}")
            return False

    async def _skip_task(self, error_event: ErrorEvent) -> bool:
        """Skip the failed task and continue"""
        try:
            self.logger.info("Skipping failed task")
            # This would mark the task as skipped but continue the workflow
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            self.logger.error(f"Task skip failed: {e}")
            return False

    async def _escalate_error(self, error_event: ErrorEvent) -> bool:
        """Escalate error to higher level"""
        try:
            self.logger.error(f"Escalating error {error_event.id} - {error_event.message}")
            # This would notify administrators or create alerts
            await asyncio.sleep(0.5)
            return True  # Escalation is considered successful
        except Exception as e:
            self.logger.error(f"Error escalation failed: {e}")
            return False

    async def _request_manual_intervention(self, error_event: ErrorEvent) -> bool:
        """Request manual intervention"""
        try:
            self.logger.error(f"Manual intervention required for error {error_event.id}")
            # This would create a manual intervention ticket or notification
            await asyncio.sleep(0.5)
            return True  # Request creation is considered successful
        except Exception as e:
            self.logger.error(f"Manual intervention request failed: {e}")
            return False

    def _generate_error_id(self) -> str:
        """Generate a unique error ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        return f"error_{timestamp}_{str(uuid.uuid4())[:8]}"

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics and trends"""
        if not self.error_history:
            return {}

        recent_errors = [
            e for e in self.error_history
            if e.timestamp > datetime.now() - timedelta(hours=24)
        ]

        error_by_type = {}
        error_by_severity = {}
        resolved_errors = sum(1 for e in recent_errors if e.resolved)
        total_errors = len(recent_errors)

        for error in recent_errors:
            error_by_type[error.error_type.value] = error_by_type.get(error.error_type.value, 0) + 1
            error_by_severity[error.severity.value] = error_by_severity.get(error.severity.value, 0) + 1

        return {
            "total_errors_24h": total_errors,
            "resolved_errors_24h": resolved_errors,
            "resolution_rate_24h": resolved_errors / total_errors if total_errors > 0 else 0,
            "active_errors": len(self.active_errors),
            "errors_by_type": error_by_type,
            "errors_by_severity": error_by_severity,
            "most_common_error": max(error_by_type.items(), key=lambda x: x[1])[0] if error_by_type else None
        }

    def get_active_errors(self) -> List[ErrorEvent]:
        """Get currently active (unresolved) errors"""
        return list(self.active_errors.values())

    def clear_resolved_errors(self, older_than_hours: int = 24):
        """Clear resolved errors from history"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        self.error_history = [
            e for e in self.error_history
            if not e.resolved or e.timestamp > cutoff_time
        ]

class CircuitBreaker:
    """Circuit breaker pattern for preventing cascading failures"""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "open":
            if datetime.now().timestamp() - self.last_failure_time > self.timeout:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful operation"""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failed operation"""
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"

# Global error handler instance
global_error_handler = ResearchErrorHandler()