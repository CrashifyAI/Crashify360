"""
Crashify360 - Input Validation
Comprehensive validation for all inputs with detailed error messages
"""

import re
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
import config
from logger import get_logger

logger = get_logger()

class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
        super().__init__(f"{field}: {message}")

class ValidationResult:
    """Result of validation operation"""
    def __init__(self):
        self.errors: List[Dict[str, str]] = []
        self.warnings: List[Dict[str, str]] = []
    
    def add_error(self, field: str, message: str, value: Any = None):
        """Add validation error"""
        self.errors.append({
            "field": field,
            "message": message,
            "value": str(value) if value is not None else None
        })
        logger.log_validation_error(field, value, message)
    
    def add_warning(self, field: str, message: str):
        """Add validation warning"""
        self.warnings.append({
            "field": field,
            "message": message
        })
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0
    
    def get_summary(self) -> str:
        """Get human-readable validation summary"""
        if self.is_valid:
            summary = "✅ All validations passed"
            if self.warnings:
                summary += f" ({len(self.warnings)} warning(s))"
            return summary
        
        summary = f"❌ Validation failed with {len(self.errors)} error(s)"
        for error in self.errors:
            summary += f"\n  • {error['field']}: {error['message']}"
        return summary

class InputValidator:
    """Comprehensive input validator"""
    
    @staticmethod
    def validate_vin(vin: str) -> bool:
        """
        Validate Vehicle Identification Number (VIN)
        VIN must be 17 characters, alphanumeric, excluding I, O, Q
        """
        if not vin:
            return False
        
        # Remove whitespace
        vin = vin.strip().upper()
        
        # Check length
        if len(vin) != 17:
            return False
        
        # Check characters (no I, O, Q allowed in VIN)
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
            return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format"""
        if not email:
            return False
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email.strip()) is not None
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate Australian phone number"""
        if not phone:
            return False
        
        # Remove spaces, dashes, parentheses
        phone = re.sub(r'[\s\-\(\)]', '', phone)
        
        # Australian mobile: +61 or 0, followed by 4 and 8 digits
        # Landline: +61 or 0, followed by 2-3 and 8 digits
        patterns = [
            r'^\+?61[234578]\d{8}$',  # +61 format
            r'^0[234578]\d{8}$'        # 0 format
        ]
        
        return any(re.match(pattern, phone) for pattern in patterns)
    
    @staticmethod
    def validate_monetary_value(value: Any, 
                                field_name: str,
                                min_value: Optional[float] = None,
                                max_value: Optional[float] = None) -> Tuple[bool, Optional[str]]:
        """
        Validate monetary value
        Returns: (is_valid, error_message)
        """
        try:
            value = float(value)
        except (ValueError, TypeError):
            return False, f"{field_name} must be a valid number"
        
        if value < 0:
            return False, f"{field_name} cannot be negative"
        
        if min_value is not None and value < min_value:
            return False, f"{field_name} must be at least ${min_value:,.2f}"
        
        if max_value is not None and value > max_value:
            return False, f"{field_name} cannot exceed ${max_value:,.2f}"
        
        return True, None
    
    @staticmethod
    def validate_policy_type(policy_type: str) -> bool:
        """Validate policy type against allowed types"""
        return policy_type.lower() in config.POLICY_TYPES
    
    @staticmethod
    def validate_loss_type(loss_type: str) -> bool:
        """Validate loss type"""
        return loss_type.lower() in config.LOSS_TYPES
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input to prevent injection
        Remove potentially dangerous characters
        """
        if not text:
            return ""
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        text = text[:max_length]
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if char == '\n' or char == '\t' or ord(char) >= 32)
        
        return text.strip()
    
    def validate_total_loss_input(self, 
                                  vin: str,
                                  policy_type: str,
                                  policy_value: Any,
                                  salvage_value: Any,
                                  repair_quote: Any,
                                  loss_type: str,
                                  owner_email: Optional[str] = None,
                                  owner_phone: Optional[str] = None) -> ValidationResult:
        """
        Validate all inputs for total loss calculation
        Returns ValidationResult object
        """
        result = ValidationResult()
        
        # VIN validation
        if not self.validate_vin(vin):
            result.add_error("vin", 
                           "Invalid VIN format. Must be 17 characters, alphanumeric (no I, O, Q)",
                           vin)
        
        # Policy type validation
        if not self.validate_policy_type(policy_type):
            result.add_error("policy_type",
                           f"Invalid policy type. Must be one of: {', '.join(config.POLICY_TYPES)}",
                           policy_type)
        
        # Loss type validation
        if not self.validate_loss_type(loss_type):
            result.add_error("loss_type",
                           f"Invalid loss type. Must be one of: {', '.join(config.LOSS_TYPES.keys())}",
                           loss_type)
        
        # Policy value validation
        is_valid, error_msg = self.validate_monetary_value(
            policy_value,
            "Policy Value",
            min_value=config.VALIDATION_RULES["min_policy_value"],
            max_value=config.VALIDATION_RULES["max_policy_value"]
        )
        if not is_valid:
            result.add_error("policy_value", error_msg, policy_value)
        else:
            policy_value = float(policy_value)
        
        # Salvage value validation
        is_valid, error_msg = self.validate_monetary_value(
            salvage_value,
            "Salvage Value",
            min_value=config.VALIDATION_RULES["min_salvage_value"]
        )
        if not is_valid:
            result.add_error("salvage_value", error_msg, salvage_value)
        else:
            salvage_value = float(salvage_value)
            
            # Check salvage value doesn't exceed policy value
            try:
                if salvage_value > float(policy_value):
                    result.add_error("salvage_value",
                                   "Salvage value cannot exceed policy value",
                                   salvage_value)
            except (ValueError, TypeError):
                pass
        
        # Repair quote validation
        is_valid, error_msg = self.validate_monetary_value(
            repair_quote,
            "Repair Quote",
            min_value=config.VALIDATION_RULES["min_repair_quote"]
        )
        if not is_valid:
            result.add_error("repair_quote", error_msg, repair_quote)
        else:
            repair_quote = float(repair_quote)
            
            # Warning if repair quote seems unreasonably high
            try:
                if repair_quote > float(policy_value) * config.VALIDATION_RULES["max_repair_quote_ratio"]:
                    result.add_warning("repair_quote",
                                     f"Repair quote is {repair_quote/float(policy_value):.1f}x the policy value. Please verify.")
            except (ValueError, TypeError):
                pass
        
        # Email validation (optional)
        if owner_email and not self.validate_email(owner_email):
            result.add_error("owner_email", "Invalid email address format", owner_email)
        
        # Phone validation (optional)
        if owner_phone and not self.validate_phone(owner_phone):
            result.add_error("owner_phone", "Invalid phone number format (Australian format required)", owner_phone)
        
        return result

# Global validator instance
validator = InputValidator()

if __name__ == "__main__":
    # Test validations
    v = InputValidator()
    
    print("Testing VIN validation:")
    print(f"  Valid: {v.validate_vin('1HGBH41JXMN109186')}")
    print(f"  Invalid (too short): {v.validate_vin('1HGBH41JX')}")
    print(f"  Invalid (contains I): {v.validate_vin('1HGBH41IXMN109186')}")
    
    print("\nTesting email validation:")
    print(f"  Valid: {v.validate_email('test@example.com')}")
    print(f"  Invalid: {v.validate_email('invalid.email')}")
    
    print("\nTesting phone validation:")
    print(f"  Valid mobile: {v.validate_phone('0412345678')}")
    print(f"  Valid with +61: {v.validate_phone('+61412345678')}")
    print(f"  Invalid: {v.validate_phone('1234')}")
    
    print("\nTesting full input validation:")
    result = v.validate_total_loss_input(
        vin="1HGBH41JXMN109186",
        policy_type="comprehensive",
        policy_value=25000,
        salvage_value=5000,
        repair_quote=20000,
        loss_type="client",
        owner_email="owner@example.com",
        owner_phone="0412345678"
    )
    print(result.get_summary())

