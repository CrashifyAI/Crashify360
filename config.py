"""
Crashify360 - Configuration Management
Centralized configuration for thresholds, constants, and settings
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

# Valuation Thresholds
THRESHOLDS = {
    "client": 0.7,
    "third_party": 0.7,
    "commercial": 0.65,
    "luxury": 0.75
}

# Policy Types
POLICY_TYPES = [
    "comprehensive",
    "third_party_property",
    "third_party_fire_theft",
    "commercial"
]

# Loss Types
LOSS_TYPES = {
    "client": "Client Vehicle (Own Damage)",
    "third_party": "Third Party Vehicle"
}

# API Configuration
AUTO_GRAP_CONFIG = {
    "api_key": os.getenv("AUTO_GRAP_KEY"),
    "base_url": "https://api.autograp.com.au/v1",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 2
}

# Email Configuration
EMAIL_CONFIG = {
    "user": os.getenv("EMAIL_USER"),
    "password": os.getenv("EMAIL_PASS"),
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True
}

# Twilio Configuration
TWILIO_CONFIG = {
    "account_sid": os.getenv("TWILIO_SID"),
    "auth_token": os.getenv("TWILIO_TOKEN"),
    "from_number": os.getenv("TWILIO_FROM")
}

# File Paths
PATHS = {
    "output": "output/",
    "logs": "logs/",
    "test_cases": "test_cases/",
    "decisions": "data/decisions.json",
    "audit_log": "logs/audit.log",
    "photos": "data/photos/"
}

# Salvage Parser Configuration
SALVAGE_PARSER_CONFIG = {
    "patterns": [
        r'\$\s*([0-9,]+(?:\.\d{2})?)',
        r'salvage[:\s]+\$?([0-9,]+)',
        r'offer[:\s]+\$?([0-9,]+)',
        r'bid[:\s]+\$?([0-9,]+)',
        r'price[:\s]+\$?([0-9,]+)'
    ],
    "confidence_threshold": 0.6
}

# Validation Rules
VALIDATION_RULES = {
    "min_policy_value": 1000,
    "max_policy_value": 500000,
    "min_salvage_value": 0,
    "min_repair_quote": 0,
    "max_repair_quote_ratio": 2.0  # Max 200% of policy value
}

# Web UI Configuration
WEB_UI_CONFIG = {
    "page_title": "Crashify360 - Total Loss Evaluator",
    "page_icon": "🚗",
    "layout": "wide",
    "theme": {
        "primaryColor": "#FF4B4B",
        "backgroundColor": "#FFFFFF",
        "secondaryBackgroundColor": "#F0F2F6",
        "textColor": "#262730"
    }
}

def validate_config() -> Dict[str, Any]:
    """Validate all required configuration values are present"""
    errors = []
    
    if not AUTO_GRAP_CONFIG["api_key"]:
        errors.append("AUTO_GRAP_KEY not set in environment")
    
    if not EMAIL_CONFIG["user"] or not EMAIL_CONFIG["password"]:
        errors.append("Email credentials not set in environment")
    
    if not TWILIO_CONFIG["account_sid"] or not TWILIO_CONFIG["auth_token"]:
        errors.append("Twilio credentials not set in environment")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def get_threshold(policy_type: str) -> float:
    """Get threshold for a specific policy type"""
    return THRESHOLDS.get(policy_type, THRESHOLDS["client"])

# Create necessary directories
def initialize_directories():
    """Create required directories if they don't exist"""
    for path in PATHS.values():
        os.makedirs(path, exist_ok=True)

if __name__ == "__main__":
    validation = validate_config()
    if validation["valid"]:
        print("✅ Configuration valid")
    else:
        print("❌ Configuration errors:")
        for error in validation["errors"]:
            print(f"  - {error}")

