"""
Crashify360 - Logging and Audit Trail
Comprehensive logging for compliance and debugging
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import config

class AuditLogger:
    """Enhanced logger with audit trail capabilities"""
    
    def __init__(self, name: str = "Crashify360"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Ensure logs directory exists
        Path(config.PATHS["logs"]).mkdir(parents=True, exist_ok=True)
        
        # File handler for general logs
        file_handler = logging.FileHandler(
            Path(config.PATHS["logs"]) / "application.log"
        )
        file_handler.setLevel(logging.INFO)
        
        # File handler for audit logs
        self.audit_handler = logging.FileHandler(
            Path(config.PATHS["logs"]) / "audit.log"
        )
        self.audit_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        self.audit_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        extra = self._format_extra(kwargs)
        self.logger.info(f"{message} {extra}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra = self._format_extra(kwargs)
        self.logger.warning(f"{message} {extra}")
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message"""
        extra = self._format_extra(kwargs)
        if error:
            self.logger.error(f"{message} - Error: {str(error)} {extra}", exc_info=True)
        else:
            self.logger.error(f"{message} {extra}")
    
    def audit(self, action: str, data: Dict[str, Any], user: str = "system"):
        """Log audit trail entry"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "data": data
        }
        
        # Log to audit file
        audit_logger = logging.getLogger(f"{self.logger.name}.audit")
        if not audit_logger.handlers:
            audit_logger.addHandler(self.audit_handler)
            audit_logger.setLevel(logging.INFO)
        
        audit_logger.info(json.dumps(audit_entry))
        
        # Also log to main logger
        self.info(f"AUDIT: {action}", **data)
    
    def _format_extra(self, kwargs: Dict[str, Any]) -> str:
        """Format extra keyword arguments"""
        if not kwargs:
            return ""
        return "- " + " | ".join(f"{k}={v}" for k, v in kwargs.items())
    
    def log_decision(self, 
                    vin: str,
                    decision: str,
                    policy_value: float,
                    repair_quote: float,
                    salvage_value: float,
                    threshold: float,
                    loss_type: str,
                    policy_type: str):
        """Log total loss decision with all relevant data"""
        self.audit("TOTAL_LOSS_DECISION", {
            "vin": vin,
            "decision": decision,
            "policy_value": policy_value,
            "repair_quote": repair_quote,
            "salvage_value": salvage_value,
            "threshold": threshold,
            "loss_type": loss_type,
            "policy_type": policy_type,
            "threshold_percentage": (repair_quote / threshold * 100) if threshold > 0 else 0
        })
    
    def log_api_call(self, 
                     api_name: str,
                     endpoint: str,
                     status_code: Optional[int] = None,
                     duration: Optional[float] = None,
                     success: bool = True):
        """Log external API calls"""
        self.audit("API_CALL", {
            "api": api_name,
            "endpoint": endpoint,
            "status_code": status_code,
            "duration_ms": duration,
            "success": success
        })
    
    def log_notification(self,
                        notification_type: str,
                        recipient: str,
                        success: bool,
                        message: Optional[str] = None):
        """Log notification attempts"""
        self.audit("NOTIFICATION_SENT", {
            "type": notification_type,
            "recipient": recipient,
            "success": success,
            "message": message
        })
    
    def log_validation_error(self, field: str, value: Any, error: str):
        """Log validation errors"""
        self.warning(f"Validation error on {field}",
                    field=field,
                    value=value,
                    error=error)
    
    def log_salvage_request(self, vin: str, email_to: str, loss_type: str):
        """Log salvage request submission"""
        self.audit("SALVAGE_REQUEST_SENT", {
            "vin": vin,
            "recipient": email_to,
            "loss_type": loss_type
        })
    
    def log_salvage_response(self, vin: str, salvage_value: float, confidence: float):
        """Log salvage value extraction"""
        self.audit("SALVAGE_RESPONSE_RECEIVED", {
            "vin": vin,
            "salvage_value": salvage_value,
            "confidence": confidence
        })

# Global logger instance
logger = AuditLogger()

def get_logger() -> AuditLogger:
    """Get the global logger instance"""
    return logger

if __name__ == "__main__":
    # Test logging
    test_logger = AuditLogger("Test")
    test_logger.info("Test info message", test_param="value")
    test_logger.warning("Test warning")
    test_logger.error("Test error", error=Exception("Test exception"))
    test_logger.audit("TEST_ACTION", {"test": "data"})
    print("✅ Logging test complete - check logs/ directory")
