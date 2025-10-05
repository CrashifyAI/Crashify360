"""
Crashify360 - Enhanced Salvage Value Parser
Extract salvage values from emails with multiple strategies and confidence scoring
"""

import re
from typing import List, Dict, Optional, Tuple
import config
from logger import get_logger

logger = get_logger()

class SalvageParseResult:
    """Result of salvage value extraction"""
    
    def __init__(self, 
                 values: List[float],
                 confidence: float,
                 method: str,
                 raw_text: Optional[str] = None):
        self.values = values
        self.best_value = max(values) if values else 0
        self.confidence = confidence
        self.method = method
        self.raw_text = raw_text
    
    def to_dict(self) -> Dict:
        return {
            "values_found": self.values,
            "best_value": self.best_value,
            "confidence": self.confidence,
            "method": self.method,
            "success": len(self.values) > 0
        }

class SalvageParser:
    """Enhanced salvage value parser with multiple extraction strategies"""
    
    def __init__(self):
        self.patterns = config.SALVAGE_PARSER_CONFIG["patterns"]
        self.confidence_threshold = config.SALVAGE_PARSER_CONFIG["confidence_threshold"]
        self.logger = logger
    
    def parse(self, email_text: str, vin: Optional[str] = None) -> SalvageParseResult:
        """
        Parse salvage value from email text
        
        Args:
            email_text: Email body text
            vin: Optional VIN for logging
        
        Returns:
            SalvageParseResult with extracted values
        """
        if not email_text:
            return SalvageParseResult([], 0.0, "empty_input")
        
        # Try different extraction methods in order of confidence
        methods = [
            self._extract_structured_value,
            self._extract_currency_patterns,
            self._extract_contextual_value,
            self._extract_number_near_keywords
        ]
        
        all_values = []
        best_result = None
        highest_confidence = 0
        
        for method in methods:
            result = method(email_text)
            if result.confidence > highest_confidence:
                highest_confidence = result.confidence
                best_result = result
            all_values.extend(result.values)
        
        # Use best result or aggregate if no high confidence match
        if best_result and best_result.confidence >= self.confidence_threshold:
            final_result = best_result
        else:
            # Aggregate all found values
            unique_values = list(set(all_values))
            final_result = SalvageParseResult(
                unique_values,
                0.5 if unique_values else 0.0,
                "aggregated"
            )
        
        # Log result
        if vin:
            self.logger.log_salvage_response(
                vin=vin,
                salvage_value=final_result.best_value,
                confidence=final_result.confidence
            )
        
        self.logger.info(f"Parsed salvage value: ${final_result.best_value:,.2f}",
                        confidence=final_result.confidence,
                        method=final_result.method,
                        values_found=len(final_result.values))
        
        return final_result
    
    def _extract_structured_value(self, text: str) -> SalvageParseResult:
        """
        Extract from structured formats like:
        - Salvage Value: $5,000
        - Our offer is $5,000.00
        - Price: AUD 5,000
        """
        patterns = [
            r'salvage\s+(?:value|offer|price)[\s:]+\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:our|final)\s+offer\s+is\s+\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'(?:price|amount)[\s:]+AUD\s+\$?\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'total\s+salvage[\s:]+\$?\s*([0-9,]+(?:\.[0-9]{2})?)'
        ]
        
        values = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1).replace(',', ''))
                    if self._is_reasonable_salvage_value(value):
                        values.append(value)
                except (ValueError, IndexError):
                    continue
        
        confidence = 0.9 if values else 0.0
        return SalvageParseResult(values, confidence, "structured_format")
    
    def _extract_currency_patterns(self, text: str) -> SalvageParseResult:
        """
        Extract currency patterns: $5,000 or $5000.00
        """
        patterns = [
            r'\$\s*([0-9,]+(?:\.[0-9]{2})?)',
            r'([0-9,]+(?:\.[0-9]{2})?)\s*(?:dollars|AUD)',
        ]
        
        values = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)
                    if self._is_reasonable_salvage_value(value):
                        values.append(value)
                except (ValueError, IndexError):
                    continue
        
        confidence = 0.7 if values else 0.0
        return SalvageParseResult(values, confidence, "currency_pattern")
    
    def _extract_contextual_value(self, text: str) -> SalvageParseResult:
        """
        Extract values appearing near salvage-related keywords
        """
        keywords = [
            'salvage', 'offer', 'bid', 'quote', 'valuation', 
            'tender', 'price', 'value', 'worth'
        ]
        
        values = []
        
        # Split text into sentences
        sentences = re.split(r'[.!?\n]+', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Check if sentence contains salvage keywords
            if any(keyword in sentence_lower for keyword in keywords):
                # Extract numbers from this sentence
                numbers = re.findall(r'([0-9,]+(?:\.[0-9]{2})?)', sentence)
                for num_str in numbers:
                    try:
                        value = float(num_str.replace(',', ''))
                        if self._is_reasonable_salvage_value(value):
                            values.append(value)
                    except ValueError:
                        continue
        
        confidence = 0.6 if values else 0.0
        return SalvageParseResult(values, confidence, "contextual")
    
    def _extract_number_near_keywords(self, text: str) -> SalvageParseResult:
        """
        Extract numbers within N words of salvage keywords
        """
        values = []
        words = text.split()
        
        keywords = {'salvage', 'offer', 'bid', 'quote', 'value', 'price', 'tender'}
        window = 5  # Look within 5 words
        
        for i, word in enumerate(words):
            if word.lower() in keywords:
                # Look at surrounding words
                start = max(0, i - window)
                end = min(len(words), i + window + 1)
                context = ' '.join(words[start:end])
                
                # Extract numbers from context
                numbers = re.findall(r'\$?\s*([0-9,]+(?:\.[0-9]{2})?)', context)
                for num_str in numbers:
                    try:
                        value = float(num_str.replace(',', '').replace(', ''))
                        if self._is_reasonable_salvage_value(value):
                            values.append(value)
                    except ValueError:
                        continue
        
        confidence = 0.5 if values else 0.0
        return SalvageParseResult(values, confidence, "keyword_proximity")
    
    def _is_reasonable_salvage_value(self, value: float) -> bool:
        """
        Check if value is within reasonable range for salvage
        """
        # Salvage values typically between $500 and $100,000
        return 500 <= value <= 100000
    
    def parse_multiple_offers(self, email_text: str) -> List[Dict]:
        """
        Parse multiple salvage offers from a single email
        Useful when comparing offers from different salvage yards
        """
        # Split by common delimiters for multiple offers
        sections = re.split(r'\n\s*\n|---+|===+', email_text)
        
        offers = []
        for i, section in enumerate(sections):
            if len(section.strip()) < 20:  # Skip very short sections
                continue
            
            result = self.parse(section)
            if result.values:
                offers.append({
                    "section": i + 1,
                    "value": result.best_value,
                    "confidence": result.confidence,
                    "method": result.method,
                    "text_snippet": section[:100] + "..." if len(section) > 100 else section
                })
        
        return offers
    
    def validate_salvage_value(self, 
                               salvage_value: float,
                               policy_value: float,
                               loss_type: str = "client") -> Tuple[bool, Optional[str]]:
        """
        Validate that salvage value is reasonable
        
        Args:
            salvage_value: Extracted salvage value
            policy_value: Vehicle policy value
            loss_type: Type of loss
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if salvage_value < 0:
            return False, "Salvage value cannot be negative"
        
        if salvage_value > policy_value:
            return False, f"Salvage value (${salvage_value:,.2f}) exceeds policy value (${policy_value:,.2f})"
        
        # Salvage typically 10-40% of policy value
        min_expected = policy_value * 0.05
        max_expected = policy_value * 0.60
        
        if salvage_value < min_expected:
            return True, f"Warning: Salvage value seems low ({salvage_value/policy_value*100:.1f}% of policy value)"
        
        if salvage_value > max_expected:
            return True, f"Warning: Salvage value seems high ({salvage_value/policy_value*100:.1f}% of policy value)"
        
        return True, None

# Global parser instance
parser = SalvageParser()

def extract_salvage_value(email_text: str, 
                         vin: Optional[str] = None,
                         policy_value: Optional[float] = None) -> Dict:
    """
    Convenience function to extract and validate salvage value
    
    Args:
        email_text: Email body text
        vin: Optional VIN for logging
        policy_value: Optional policy value for validation
    
    Returns:
        Dictionary with extraction results
    """
    result = parser.parse(email_text, vin)
    
    response = result.to_dict()
    
    # Add validation if policy value provided
    if policy_value and result.best_value > 0:
        is_valid, message = parser.validate_salvage_value(
            result.best_value,
            policy_value
        )
        response["validation"] = {
            "is_valid": is_valid,
            "message": message
        }
    
    return response

if __name__ == "__main__":
    # Test salvage parser
    print("Testing Salvage Parser...")
    
    test_emails = [
        # Test 1: Structured format
        """
        Dear Claims Handler,
        
        Thank you for your salvage request. After inspecting the vehicle,
        we are pleased to offer the following:
        
        Salvage Value: $6,500.00
        
        This offer is valid for 7 days.
        
        Best regards,
        Salvage Yard
        """,
        
        # Test 2: Natural language
        """
        Hi there,
        
        We've looked at the Toyota Camry and we can offer you $5,200 for it.
        Let us know if this works for you.
        
        Thanks
        """,
        
        # Test 3: Multiple values
        """
        Salvage Assessment Report
        
        Market value: $25,000
        Repair estimate: $18,000
        Our salvage offer: $7,800
        
        Please confirm acceptance.
        """,
        
        # Test 4: Complex format
        """
        TENDER RESPONSE
        
        Vehicle: 2020 Toyota Camry
        Condition: Damaged front end
        
        We submit our tender as follows:
        Price: AUD $6,250.00
        Collection: Within 48 hours
        Payment: 7 days from collection
        """,
    ]
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n--- Test {i} ---")
        result = extract_salvage_value(email, vin=f"TEST{i}VIN", policy_value=25000)
        print(f"Best Value: ${result['best_value']:,.2f}")
        print(f"Confidence: {result['confidence']:.1%}")
        print(f"Method: {result['method']}")
        print(f"All Values Found: {result['values_found']}")
        if 'validation' in result:
            print(f"Validation: {result['validation']}")
    
    print("\n✅ Salvage parser tests complete")

