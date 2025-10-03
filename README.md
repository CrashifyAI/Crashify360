# 🚗 Crashify360 - Total Loss Evaluation System

## Overview

Crashify360 is a comprehensive proof-of-concept system for evaluating vehicle total loss claims in the insurance industry. It automates the decision-making process, integrates with external APIs, manages salvage requests, and provides detailed audit trails.

### Key Features

- ✅ **Dual Loss Type Support**: Client and Third-Party loss calculations
- 📊 **Intelligent Valuation Engine**: 70% threshold rule with configurable parameters
- 🔌 **API Integration**: Auto Grap API for market valuations
- 📧 **Automated Email System**: Salvage request templates and notifications
- 🔍 **Smart Salvage Parser**: Extract values from emails with confidence scoring
- 💾 **Data Persistence**: JSON-based storage with full audit trail
- 🧪 **Comprehensive Testing**: 20+ test scenarios covering all edge cases
- 🖥️ **Modern Web UI**: Streamlit interface with real-time validation
- 📝 **Detailed Logging**: Audit trail for compliance and debugging
- 🔒 **Input Validation**: Robust validation with Australian-specific formats

---

## 📂 Project Structure

```
Crashify360-PoC/
├── README.md                  # This file
├── .env                       # Environment variables (create from .env.example)
├── requirements.txt           # Python dependencies
│
├── main.py                    # CLI entry point
├── web_ui.py                  # Streamlit web interface
│
├── config.py                  # Configuration management
├── logger.py                  # Logging and audit trail
├── validator.py               # Input validation
│
├── valuation_engine.py        # Core valuation logic
├── autograp_api.py           # Auto Grap API client
├── salvage_email.py          # Email generation and sending
├── salvage_parser.py         # Salvage value extraction
├── data_storage.py           # Data persistence layer
│
├── test_suite.py             # Comprehensive test suite
│
├── output/                    # Generated reports and exports
│   └── result.txt
├── logs/                      # Application and audit logs
│   ├── application.log
│   └── audit.log
├── data/                      # Stored decisions and photos
│   ├── decisions.json
│   └── photos/
└── test_cases/                # Sample test data
    ├── sample_input.json
    └── batch_input.json
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/crashify360-poc.git
cd crashify360-poc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
# Auto Grap API
AUTO_GRAP_KEY=your_autograp_api_key

# Email Configuration
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_specific_password

# Twilio Configuration (for SMS notifications)
TWILIO_SID=your_twilio_account_sid
TWILIO_TOKEN=your_twilio_auth_token
TWILIO_FROM=+61412345678
```

### 3. Run the Web Interface

```bash
streamlit run web_ui.py
```

The web interface will open at `http://localhost:8501`

### 4. Run CLI Commands

```bash
# Single assessment
python main.py assess \
  --vin 1HGBH41JXMN109186 \
  --policy-value 25000 \
  --salvage-value 5000 \
  --repair-quote 18000 \
  --loss-type client

# Batch assessment
python main.py batch \
  --input test_cases/batch_input.json \
  --output output/results.json

# View statistics
python main.py stats

# Run tests
python main.py test
```

---

## 📖 Total Loss Logic Explained

### Client Loss (Own Damage)

**Formula**: `Threshold = Policy Value × 70%`

**Example**:
- Policy Value: $20,000
- Threshold: $14,000 (70% of $20,000)
- Repair Quote: $15,000
- **Decision**: Total Loss (repair exceeds threshold)

**Rationale**: For the client's own vehicle, salvage value is not deducted from the threshold calculation because the insurer will recover salvage value after declaring total loss.

### Third Party Loss

**Formula**: `Threshold = (Policy Value - Salvage Value) × 70%`

**Example**:
- Policy Value: $25,000
- Salvage Value: $7,000
- Net Value: $18,000 ($25,000 - $7,000)
- Threshold: $12,600 (70% of $18,000)
- Repair Quote: $13,000
- **Decision**: Total Loss (repair exceeds threshold)

**Rationale**: For third-party vehicles, the insurer must pay out the vehicle owner minus salvage, so the net value forms the basis for the threshold.

---

## 🧪 Test Scenarios

### ✅ Basic Functional Tests

#### Scenario 1: Client Total Loss
```json
{
  "vin": "1HGBH41JXMN109186",
  "policy_type": "comprehensive",
  "policy_value": 20000,
  "salvage_value": 5000,
  "repair_quote": 15000,
  "loss_type": "client"
}
```
**Expected**: Total Loss (Threshold = $14,000)

#### Scenario 2: Third Party Total Loss
```json
{
  "vin": "2HGBH41JXMN109187",
  "policy_type": "comprehensive",
  "policy_value": 25000,
  "salvage_value": 7000,
  "repair_quote": 13000,
  "loss_type": "third_party"
}
```
**Expected**: Total Loss (Threshold = $12,600)

#### Scenario 3: Client Repairable
```json
{
  "vin": "3HGBH41JXMN109188",
  "policy_type": "comprehensive",
  "policy_value": 30000,
  "salvage_value": 5000,
  "repair_quote": 18000,
  "loss_type": "client"
}
```
**Expected**: Repairable (Threshold = $21,000)

### ⚠️ Edge Case Tests

#### Scenario 4: Zero Salvage Value
```json
{
  "policy_value": 20000,
  "salvage_value": 0,
  "repair_quote": 14000,
  "loss_type": "third_party"
}
```
**Expected**: Repairable (repair equals threshold, must exceed)

#### Scenario 5: Salvage Equals Policy
```json
{
  "policy_value": 20000,
  "salvage_value": 20000,
  "repair_quote": 1000,
  "loss_type": "third_party"
}
```
**Expected**: Total Loss (threshold = $0, any repair exceeds)

#### Scenario 6: Invalid Inputs
- Negative repair quote → Validation error
- Salvage exceeds policy → Validation error
- Invalid VIN format → Validation error
- Extremely high repair (>200% policy) → Warning

### 📧 Email Template Tests

#### Scenario 7: Client Loss Email
**Expected Template**: "Standard Salvage (Client)"

#### Scenario 8: Third Party Loss Email
**Expected Template**: "Firm Buy Tender (Third Party)"

### 🧠 AI Explanation Tests

#### Scenario 9: Third Party Explanation
**Expected**: Mentions "Net Value (Policy - Salvage)"

#### Scenario 10: Client Explanation
**Expected**: Mentions "Policy Value" as basis

---

## 🖥️ Web Interface Guide

### New Assessment Page

1. **Manual Entry Tab**
   - Enter VIN (validated format)
   - Select policy type and loss type
   - Input financial values
   - Optional: Owner contact details
   - Click "Evaluate Total Loss"

2. **VIN Lookup Tab**
   - Enter VIN
   - Click "Lookup VIN" to fetch market data
   - Use auto-populated values in assessment

### Features

- **Real-time Validation**: Immediate feedback on inputs
- **Dynamic Results**: Updates as you change values
- **Visual Indicators**: Color-coded decisions
- **Progress Bars**: Visual representation of thresholds
- **Export Options**: Download reports in TXT or JSON
- **Salvage Requests**: Send emails directly from UI
- **Email Preview**: Preview before sending

### View History Page

- Filter by loss type, decision, date range
- Search and export decisions
- View detailed JSON data
- Download individual reports

### Salvage Parser Page

- Paste email text or upload file
- Extract salvage values with confidence scoring
- Multiple extraction strategies
- Validation against policy value

### Statistics Dashboard

- Total decisions count
- Loss vs repairable ratio
- Financial metrics and averages
- Charts and visualizations
- Export to CSV

---

## 🔌 API Integration

### Auto Grap API

The system integrates with Auto Grap for vehicle valuations:

```python
from autograp_api import AutoGrapAPI

api = AutoGrapAPI()
result = api.get_market_value("1HGBH41JXMN109186")

print(f"Market Value: ${result['market_value']:,.2f}")
print(f"Trade-In: ${result['trade_in_value']:,.2f}")
```

**Features**:
- Automatic retry logic with exponential backoff
- Rate limiting (100 calls/hour)
- Error handling and logging
- Timeout management

---

## 📧 Email System

### Sending Salvage Requests

```python
from salvage_email import send_salvage_request

vehicle_info = {
    "vin": "1HGBH41JXMN109186",
    "year": 2020,
    "make": "Toyota",
    "model": "Camry"
}

send_salvage_request(
    to_email="salvage@example.com",
    vehicle_info=vehicle_info,
    policy_value=25000,
    loss_type="client",
    photos=["photo1.jpg", "photo2.jpg"]
)
```

### Email Templates

- **Client Loss**: Standard salvage tender
- **Third Party Loss**: Firm buy tender
- HTML formatted with vehicle details
- Automatic photo attachments
- Professional branding

---

## 🔍 Salvage Value Parser

Extract salvage values from email responses:

```python
from salvage_parser import extract_salvage_value

email_text = """
Dear Claims Handler,
We are pleased to offer $6,500.00 for the salvage.
Best regards
"""

result = extract_salvage_value(email_text, policy_value=25000)

print(f"Extracted Value: ${result['best_value']:,.2f}")
print(f"Confidence: {result['confidence']:.1%}")
```

**Features**:
- Multiple extraction strategies
- Confidence scoring
- Validation against policy value
- Handles various formats

---

## 💾 Data Persistence

### Storing Decisions

```python
from data_storage import DecisionStorage

storage = DecisionStorage()

# Save decision
decision_id = storage.save_decision(decision_data)

# Retrieve decision
decision = storage.get_decision(decision_id)

# Search decisions
results = storage.search_decisions(
    loss_type="client",
    min_policy_value=20000
)

# Get statistics
stats = storage.get_statistics()

# Export to CSV
storage.export_to_csv("output/decisions.csv")
```

---

## 📝 Logging and Audit Trail

All operations are logged for compliance:

```python
from logger import get_logger

logger = get_logger()

# Info logging
logger.info("Assessment started", vin="1HGBH41JXMN109186")

# Audit logging
logger.audit("TOTAL_LOSS_DECISION", {
    "vin": "1HGBH41JXMN109186",
    "decision": "TOTAL LOSS",
    "policy_value": 25000
})

# Error logging
logger.error("API call failed", error=exception)
```

**Log Files**:
- `logs/application.log` - General application logs
- `logs/audit.log` - Audit trail for compliance

---

## 🧪 Running Tests

### Full Test Suite

```bash
python main.py test
```

### Individual Test Classes

```bash
# Run specific test class
pytest test_suite.py::TestValuationEngine -v

# Run with coverage
pytest test_suite.py --cov=. --cov-report=html
```

### Test Categories

1. **Valuation Engine Tests**: 10 scenarios
2. **Validator Tests**: Input validation
3. **Email Template Tests**: Template generation
4. **AI Explanation Tests**: Logic verification
5. **Integration Tests**: End-to-end workflows
6. **Performance Tests**: Speed benchmarks

---

## 📊 Configuration

### Threshold Configuration

Edit `config.py` to adjust thresholds:

```python
THRESHOLDS = {
    "client": 0.7,           # 70% for client loss
    "third_party": 0.7,      # 70% for third party
    "commercial": 0.65,      # 65% for commercial
    "luxury": 0.75           # 75% for luxury vehicles
}
```

### Validation Rules

```python
VALIDATION_RULES = {
    "min_policy_value": 1000,
    "max_policy_value": 500000,
    "min_salvage_value": 0,
    "max_repair_quote_ratio": 2.0
}
```

---

## 🔒 Security Considerations

1. **API Keys**: Store in `.env`, never commit
2. **Input Sanitization**: All inputs validated
3. **Email Security**: Use app-specific passwords
4. **Rate Limiting**: Prevent API abuse
5. **Audit Logging**: Track all decisions

---

## 🐛 Troubleshooting

### Common Issues

#### API Connection Failed
```bash
# Test API configuration
python main.py lookup --vin TEST123VIN4567890
```

#### Email Not Sending
- Check SMTP settings in `.env`
- Use app-specific password for Gmail
- Verify firewall settings

#### Validation Errors
- Check VIN format (17 chars, no I/O/Q)
- Ensure values are positive
- Verify salvage < policy value

---

## 📈 Future Enhancements

### Planned Features

- [ ] Machine learning for threshold optimization
- [ ] Integration with more valuation APIs
- [ ] Mobile app for field assessors
- [ ] Real-time notifications dashboard
- [ ] Advanced analytics and reporting
- [ ] Multi-currency support
- [ ] Photo damage assessment AI
- [ ] Blockchain audit trail

---

## 🤝 Contributing

This is a proof-of-concept system. For production use:

1. Add authentication and authorization
2. Implement database backend (PostgreSQL)
3. Add API rate limiting middleware
4. Enhance error recovery
5. Add comprehensive monitoring
6. Implement backup strategies

---

## 📄 License

Copyright © 2025 Crashify360. All rights reserved.

This is a proof-of-concept system for demonstration purposes.

---

## 📞 Support

For questions or issues:
- Email: info@crashify.com.au


---

## 🙏 Acknowledgments

- Auto Grap API for vehicle valuations
- Streamlit for the web framework
- Python community for excellent libraries

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Status**: Proof of Concept ✅
