"""
Crashify360 - Enhanced Valuation Engine
Calculates total loss decisions with comprehensive logic and audit trail
"""

from typing import Dict, Any, Tuple
from datetime import datetime
import config
from logger import get_logger
from validator import validator, ValidationResult

logger = get_logger()

class ValuationResult:
    """Structured result from valuation calculation"""
    
    def __init__(self,
                 is_total_loss: bool,
                 threshold: float,
                 policy_value: float,
                 salvage_value: float,
                 repair_quote: float,
                 loss_type: str,
                 policy_type: str,
                 vin: str,
                 calculation_method: str):
        self.is_total_loss = is_total_loss
        self.threshold = threshold
        self.policy_value = policy_value
        self.salvage_value = salvage_value
        self.repair_quote = repair_quote
        self.loss_type = loss_type
        self.policy_type = policy_type
        self.vin = vin
        self.calculation_method = calculation_method
        self.timestamp = datetime.now()
        self.threshold_percentage = (repair_quote / threshold * 100) if threshold > 0 else 0
        self.decision_margin = repair_quote - threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "vin": self.vin,
            "timestamp": self.timestamp.isoformat(),
            "decision": "TOTAL LOSS" if self.is_total_loss else "REPAIRABLE",
            "loss_type": self.loss_type,
            "policy_type": self.policy_type,
            "policy_value": round(self.policy_value, 2),
            "salvage_value": round(self.salvage_value, 2),
            "repair_quote": round(self.repair_quote, 2),
            "threshold": round(self.threshold, 2),
            "threshold_percentage": round(self.threshold_percentage, 2),
            "decision_margin": round(self.decision_margin, 2),
            "calculation_method": self.calculation_method
        }
    
    def generate_explanation(self) -> str:
        """Generate human-readable explanation"""
        decision_icon = "🔴" if self.is_total_loss else "🟢"
        
        explanation = f"""
╔══════════════════════════════════════════════════════════════════╗
║                    TOTAL LOSS EVALUATION REPORT                   ║
╚══════════════════════════════════════════════════════════════════╝

📋 CASE INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  VIN:                {self.vin}
  Evaluation Date:    {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
  Loss Type:          {config.LOSS_TYPES[self.loss_type]}
  Policy Type:        {self.policy_type.replace('_', ' ').title()}

💰 FINANCIAL BREAKDOWN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Policy Value:       ${self.policy_value:,.2f}
  Salvage Value:      ${self.salvage_value:,.2f}
  Repair Quote:       ${self.repair_quote:,.2f}

📊 CALCULATION METHOD: {self.calculation_method}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Threshold (70%):    ${self.threshold:,.2f}
  Repair vs Threshold: {self.threshold_percentage:.1f}%
  Decision Margin:    ${abs(self.decision_margin):,.2f} {'over' if self.decision_margin > 0 else 'under'} threshold

⚖️  DECISION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  {decision_icon} {('TOTAL LOSS' if self.is_total_loss else 'REPAIRABLE').center(60)} {decision_icon}

📝 RATIONALE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        if self.is_total_loss:
            explanation += f"""  The repair quote of ${self.repair_quote:,.2f} exceeds the threshold of 
  ${self.threshold:,.2f}, which is 70% of the {'policy value' if self.loss_type == 'client' else 'net value (policy - salvage)'}.
  
  This vehicle is classified as an ECONOMIC TOTAL LOSS as repair costs
  are not economically viable compared to the vehicle's value.
"""
        else:
            explanation += f"""  The repair quote of ${self.repair_quote:,.2f} is below the threshold of 
  ${self.threshold:,.2f}, which is 70% of the {'policy value' if self.loss_type == 'client' else 'net value (policy - salvage)'}.
  
  This vehicle is REPAIRABLE and repair is the economically viable option.
"""
        
        explanation += "\n" + "═" * 68
        
        return explanation

class ValuationEngine:
    """Enhanced valuation engine with comprehensive validation and logging"""
    
    def __init__(self):
        self.logger = logger
        self.validator = validator
    
    def calculate_total_loss(self,
                            vin: str,
                            policy_type: str,
                            policy_value: float,
                            salvage_value: float,
                            repair_quote: float,
                            loss_type: str = "client",
                            skip_validation: bool = False) -> Tuple[ValuationResult, ValidationResult]:
        """
        Calculate total loss decision
        
        Args:
            vin: Vehicle Identification Number
            policy_type: Type of insurance policy
            policy_value: Insured value of vehicle
            salvage_value: Expected salvage value
            repair_quote: Cost to repair vehicle
            loss_type: 'client' or 'third_party'
            skip_validation: Skip validation (use with caution)
        
        Returns:
            Tuple of (ValuationResult, ValidationResult)
        """
        # Validate inputs
        validation = ValidationResult()
        if not skip_validation:
            validation = self.validator.validate_total_loss_input(
                vin=vin,
                policy_type=policy_type,
                policy_value=policy_value,
                salvage_value=salvage_value,
                repair_quote=repair_quote,
                loss_type=loss_type
            )
            
            if not validation.is_valid:
                self.logger.error("Validation failed for total loss calculation",
                                vin=vin,
                                errors=len(validation.errors))
                # Return empty result with validation errors
                return None, validation
        
        # Convert to float for calculations
        policy_value = float(policy_value)
        salvage_value = float(salvage_value)
        repair_quote = float(repair_quote)
        
        # Get threshold percentage for policy type
        threshold_pct = config.get_threshold(policy_type)
        
        # Calculate threshold based on loss type
        if loss_type == "client":
            # Client loss: threshold is % of policy value
            threshold = policy_value * threshold_pct
            calculation_method = f"{threshold_pct*100:.0f}% of Policy Value"
        elif loss_type == "third_party":
            # Third party loss: threshold is % of (policy value - salvage)
            net_value = policy_value - salvage_value
            threshold = net_value * threshold_pct
            calculation_method = f"{threshold_pct*100:.0f}% of Net Value (Policy - Salvage)"
        else:
            raise ValueError(f"Invalid loss type: {loss_type}")
        
        # Make decision
        is_total_loss = repair_quote > threshold
        
        # Create result object
        result = ValuationResult(
            is_total_loss=is_total_loss,
            threshold=threshold,
            policy_value=policy_value,
            salvage_value=salvage_value,
            repair_quote=repair_quote,
            loss_type=loss_type,
            policy_type=policy_type,
            vin=vin,
            calculation_method=calculation_method
        )
        
        # Log decision
        self.logger.log_decision(
            vin=vin,
            decision="TOTAL_LOSS" if is_total_loss else "REPAIRABLE",
            policy_value=policy_value,
            repair_quote=repair_quote,
            salvage_value=salvage_value,
            threshold=threshold,
            loss_type=loss_type,
            policy_type=policy_type
        )
        
        return result, validation
    
    def calculate_batch(self, cases: list) -> list:
        """Calculate multiple valuations in batch"""
        results = []
        for case in cases:
            result, validation = self.calculate_total_loss(**case)
            results.append({
                "case": case,
                "result": result.to_dict() if result else None,
                "validation": validation.get_summary()
            })
        return results

# Global engine instance
engine = ValuationEngine()

if __name__ == "__main__":
    # Test the engine
    print("Testing Valuation Engine...")
    
    result, validation = engine.calculate_total_loss(
        vin="1HGBH41JXMN109186",
        policy_type="comprehensive",
        policy_value=25000,
        salvage_value=5000,
        repair_quote=20000,
        loss_type="client"
    )
    
    if result:
        print(result.generate_explanation())
        print("\n" + "="*68)
        print("JSON Output:")
        import json
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print("Validation failed:")
        print(validation.get_summary())
