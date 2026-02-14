"""
Error tracking and alerting system for SmartShelf AI
"""

import os
import traceback
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from .logger import get_logger
from .metrics import metrics

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    NETWORK = "network"
    PERFORMANCE = "performance"


@dataclass
class ErrorEvent:
    """Error event data structure"""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ErrorTracker:
    """Central error tracking system"""
    
    def __init__(self, sentry_dsn: Optional[str] = None):
        self.sentry_dsn = sentry_dsn or os.getenv('SENTRY_DSN')
        self.error_events: List[ErrorEvent] = []
        self.error_thresholds = {
            ErrorSeverity.LOW: 100,      # 100 errors per hour
            ErrorSeverity.MEDIUM: 50,    # 50 errors per hour
            ErrorSeverity.HIGH: 10,      # 10 errors per hour
            ErrorSeverity.CRITICAL: 1    # 1 error per hour
        }
        
        self._setup_sentry()
        self._start_monitoring()
    
    def _setup_sentry(self):
        """Setup Sentry for error tracking"""
        if self.sentry_dsn:
            try:
                sentry_sdk.init(
                    dsn=self.sentry_dsn,
                    integrations=[
                        FastApiIntegration(auto_enabling_integrations=False),
                        SqlalchemyIntegration(),
                    ],
                    traces_sample_rate=0.1,
                    environment=os.getenv('ENVIRONMENT', 'development'),
                    release=os.getenv('APP_VERSION', '1.0.0'),
                )
                logger.info("Sentry error tracking initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Sentry: {e}")
    
    def _start_monitoring(self):
        """Start background monitoring for error thresholds"""
        async def monitor_errors():
            while True:
                try:
                    await self._check_error_thresholds()
                    await asyncio.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(60)
        
        # Start monitoring task when event loop is available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(monitor_errors())
            else:
                loop.run_until_complete(monitor_errors())
        except RuntimeError:
            # No event loop running yet, will be started later
            pass
    
    def track_error(
        self,
        error: Exception,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        component: str = "unknown",
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Track an error event
        
        Args:
            error: Exception object
            severity: Error severity level
            category: Error category
            component: Component where error occurred
            user_id: User ID if applicable
            session_id: Session ID if applicable
            request_id: Request ID if applicable
            context: Additional context information
        
        Returns:
            Error ID
        """
        try:
            # Generate error ID
            error_id = f"err_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{hash(str(error)) % 10000:04d}"
            
            # Create error event
            error_event = ErrorEvent(
                error_id=error_id,
                error_type=type(error).__name__,
                error_message=str(error),
                severity=severity,
                category=category,
                component=component,
                user_id=user_id,
                session_id=session_id,
                request_id=request_id,
                stack_trace=traceback.format_exc(),
                context=context or {}
            )
            
            # Store error event
            self.error_events.append(error_event)
            
            # Keep only last 1000 errors in memory
            if len(self.error_events) > 1000:
                self.error_events = self.error_events[-1000:]
            
            # Update metrics
            metrics.increment_errors(
                error_type=error_event.error_type,
                component=component
            )
            
            # Log error
            log_level = {
                ErrorSeverity.LOW: logger.warning,
                ErrorSeverity.MEDIUM: logger.error,
                ErrorSeverity.HIGH: logger.error,
                ErrorSeverity.CRITICAL: logger.critical
            }.get(severity, logger.error)
            
            log_level(
                f"Error tracked: {error_event.error_type} - {error_event.error_message}",
                extra={
                    'error_id': error_id,
                    'severity': severity.value,
                    'category': category.value,
                    'component': component,
                    'user_id': user_id,
                    'session_id': session_id,
                    'request_id': request_id
                }
            )
            
            # Send to Sentry if configured
            if self.sentry_dsn:
                try:
                    with sentry_sdk.configure_scope() as scope:
                        scope.set_tag('error_id', error_id)
                        scope.set_tag('severity', severity.value)
                        scope.set_tag('category', category.value)
                        scope.set_tag('component', component)
                        
                        if user_id:
                            scope.set_user({'id': user_id})
                        if context:
                            scope.set_context('error_context', context)
                    
                    sentry_sdk.capture_exception(error)
                except Exception as e:
                    logger.error(f"Failed to send error to Sentry: {e}")
            
            # Check for immediate alerts
            if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                # Schedule alert for async execution
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self._send_immediate_alert(error_event))
                    else:
                        loop.run_until_complete(self._send_immediate_alert(error_event))
                except RuntimeError:
                    # No event loop, log instead
                    logger.critical(f"CRITICAL ERROR (no async loop): {error_event.error_type} - {error_event.error_message}")
                except Exception as e:
                    logger.error(f"Failed to schedule immediate alert: {e}")
            
            return error_id
            
        except Exception as e:
            logger.error(f"Failed to track error: {e}")
            return f"err_failed_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    async def _check_error_thresholds(self):
        """Check error thresholds and send alerts if needed"""
        try:
            now = datetime.utcnow()
            one_hour_ago = now - timedelta(hours=1)
            
            # Count errors by severity in the last hour
            recent_errors = [
                error for error in self.error_events
                if error.timestamp >= one_hour_ago
            ]
            
            for severity, threshold in self.error_thresholds.items():
                count = len([
                    error for error in recent_errors
                    if error.severity == severity
                ])
                
                if count >= threshold:
                    await self._send_threshold_alert(severity, count, threshold)
        
        except Exception as e:
            logger.error(f"Error checking thresholds: {e}")
    
    async def _send_immediate_alert(self, error_event: ErrorEvent):
        """Send immediate alert for high/critical errors"""
        try:
            alert_message = f"""
🚨 IMMEDIATE ERROR ALERT 🚨

Error ID: {error_event.error_id}
Severity: {error_event.severity.value.upper()}
Category: {error_event.category.value}
Component: {error_event.component}
Time: {error_event.timestamp.isoformat()}

Error: {error_event.error_type}
Message: {error_event.error_message}

User ID: {error_event.user_id or 'N/A'}
Session ID: {error_event.session_id or 'N/A'}

Stack Trace:
{error_event.stack_trace}
            """
            
            # Send alert (implement your alerting mechanism here)
            await self._send_alert(alert_message, f"IMMEDIATE: {error_event.error_type}")
            
        except Exception as e:
            logger.error(f"Failed to send immediate alert: {e}")
    
    async def _send_threshold_alert(self, severity: ErrorSeverity, count: int, threshold: int):
        """Send threshold breach alert"""
        try:
            alert_message = f"""
⚠️ ERROR THRESHOLD BREACHED ⚠️

Severity: {severity.value.upper()}
Count: {count} errors in the last hour
Threshold: {threshold} errors per hour
Time: {datetime.utcnow().isoformat()}

Recent errors of this severity:
{chr(10).join([f"- {err.error_type}: {err.error_message}" for err in self.error_events[-5:] if err.severity == severity])}
            """
            
            # Send alert
            await self._send_alert(alert_message, f"THRESHOLD: {severity.value.upper()} errors")
            
        except Exception as e:
            logger.error(f"Failed to send threshold alert: {e}")
    
    async def _send_alert(self, message: str, subject: str):
        """Send alert notification (implement your preferred alerting method)"""
        try:
            # Example: Send to Slack, email, SMS, etc.
            # This is a placeholder - implement your actual alerting system
            
            # Log the alert
            logger.critical(f"ALERT - {subject}: {message}")
            
            # You could integrate with:
            # - Slack webhook
            # - Email service
            # - SMS service
            # - PagerDuty
            # - Discord webhook
            # etc.
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def get_error_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None
    ) -> Dict[str, Any]:
        """
        Get error summary for specified period
        
        Args:
            start_date: Start date for summary
            end_date: End date for summary
            severity: Filter by severity
            category: Filter by category
        
        Returns:
            Error summary data
        """
        try:
            # Filter errors
            filtered_errors = self.error_events.copy()
            
            if start_date:
                filtered_errors = [e for e in filtered_errors if e.timestamp >= start_date]
            
            if end_date:
                filtered_errors = [e for e in filtered_errors if e.timestamp <= end_date]
            
            if severity:
                filtered_errors = [e for e in filtered_errors if e.severity == severity]
            
            if category:
                filtered_errors = [e for e in filtered_errors if e.category == category]
            
            # Calculate summary
            total_errors = len(filtered_errors)
            
            # Errors by severity
            errors_by_severity = {}
            for sev in ErrorSeverity:
                errors_by_severity[sev.value] = len([
                    e for e in filtered_errors if e.severity == sev
                ])
            
            # Errors by category
            errors_by_category = {}
            for cat in ErrorCategory:
                errors_by_category[cat.value] = len([
                    e for e in filtered_errors if e.category == cat
                ])
            
            # Errors by component
            errors_by_component = {}
            for error in filtered_errors:
                errors_by_component[error.component] = errors_by_component.get(error.component, 0) + 1
            
            # Recent errors (last 10)
            recent_errors = [
                {
                    'error_id': e.error_id,
                    'error_type': e.error_type,
                    'error_message': e.error_message,
                    'severity': e.severity.value,
                    'category': e.category.value,
                    'component': e.component,
                    'timestamp': e.timestamp.isoformat()
                }
                for e in sorted(filtered_errors, key=lambda x: x.timestamp, reverse=True)[:10]
            ]
            
            return {
                'total_errors': total_errors,
                'errors_by_severity': errors_by_severity,
                'errors_by_category': errors_by_category,
                'errors_by_component': errors_by_component,
                'recent_errors': recent_errors
            }
            
        except Exception as e:
            logger.error(f"Error getting error summary: {e}")
            return {}
    
    def resolve_error(self, error_id: str, resolution_notes: str) -> bool:
        """
        Mark an error as resolved
        
        Args:
            error_id: Error ID to resolve
            resolution_notes: Notes about the resolution
        
        Returns:
            True if resolved successfully
        """
        try:
            for error in self.error_events:
                if error.error_id == error_id:
                    error.resolved = True
                    error.resolved_at = datetime.utcnow()
                    error.resolution_notes = resolution_notes
                    
                    logger.info(f"Error {error_id} marked as resolved")
                    return True
            
            logger.warning(f"Error {error_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error resolving error: {e}")
            return False


# Global error tracker instance
error_tracker = ErrorTracker()


def track_error(
    error: Exception,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    component: str = "unknown",
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> str:
    """
    Convenience function to track an error
    
    Args:
        error: Exception object
        severity: Error severity level
        category: Error category
        component: Component where error occurred
        user_id: User ID if applicable
        session_id: Session ID if applicable
        request_id: Request ID if applicable
        context: Additional context information
    
    Returns:
        Error ID
    """
    return error_tracker.track_error(
        error=error,
        severity=severity,
        category=category,
        component=component,
        user_id=user_id,
        session_id=session_id,
        request_id=request_id,
        context=context
    )


def error_tracking_decorator(
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    component: str = "unknown"
):
    """
    Decorator to automatically track errors in functions
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                track_error(
                    error=e,
                    severity=severity,
                    category=category,
                    component=component,
                    context={
                        'function': func.__name__,
                        'module': func.__module__,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys())
                    }
                )
                raise
        return wrapper
    return decorator
