"""
Crashify360 - Comprehensive Test Suite
All functional, edge case, and integration tests
"""

import unittest
import json
from typing import Dict, Any
from valuation_engine import ValuationEngine, ValuationResult
from validator import InputValidator, ValidationResult
import config

class TestEmailTemplates(unittest.TestCase):
    """Test cases for email template generation"""
    
    def test_client_loss_email_template(self):
        """
        Scenario 7: Salvage email for Client Total Loss
        Expected: Email includes "Tender Type: Standard Salvage (Client)"
        """
        from salvage_email import generate_salvage_email_body
        
        vehicle_info = {
            "vin": "1HGBH41JXMN109186",
            "year": 2020,
            "make": "Toyota",
            "model": "Camry"
        }
        
        email_body = generate_salvage_email_body(
            vehicle_info=vehicle_info,
            policy_value=20000,
            loss_type="client"
        )
        
        self.assertIn("Standard Salvage (Client)", email_body, 
                     "Should specify client salvage type")
        self.assertNotIn("Firm Buy Tender", email_body,
                        "Should not mention third party tender")
        print("✅ Test 7 PASSED: Client loss email template correct")
    
    def test_third_party_loss_email_template(self):
        """
        Scenario 8: Salvage email for Third Party Total Loss
        Expected: Email includes "Tender Type: Firm Buy Tender (Third Party)"
        """
        from salvage_email import generate_salvage_email_body
        
        vehicle_info = {
            "vin": "2HGBH41JXMN109187",
            "year": 2019,
            "make": "Honda",
            "model": "Civic"
        }
        
        email_body = generate_salvage_email_body(
            vehicle_info=vehicle_info,
            policy_value=25000,
            loss_type="third_party"
        )
        
        self.assertIn("Firm Buy Tender (Third Party)", email_body,
                     "Should specify third party tender type")
        self.assertNotIn("Standard Salvage (Client)", email_body,
                        "Should not mention client salvage")
        print("✅ Test 8 PASSED: Third party loss email template correct")

class TestAIExplanation(unittest.TestCase):
    """Test cases for AI-generated explanations"""
    
    def test_third_party_explanation_logic(self):
        """
        Scenario 9: Explanation reflects correct logic for third party
        Expected: Explanation includes "after deducting salvage value"
        """
        engine = ValuationEngine()
        result, validation = engine.calculate_total_loss(
            vin="3HGBH41JXMN109188",
            policy_type="comprehensive",
            policy_value=25000,
            salvage_value=7000,
            repair_quote=13000,
            loss_type="third_party"
        )
        
        explanation = result.generate_explanation()
        
        self.assertIn("Net Value", explanation,
                     "Should mention net value calculation")
        self.assertIn("Policy - Salvage", explanation,
                     "Should explain salvage deduction")
        print("✅ Test 9 PASSED: Third party explanation includes correct logic")
    
    def test_client_explanation_logic(self):
        """
        Scenario 10: Explanation for Client Total Loss
        Expected: Explanation mentions policy value basis
        """
        engine = ValuationEngine()
        result, validation = engine.calculate_total_loss(
            vin="4HGBH41JXMN109189",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=5000,
            repair_quote=15000,
            loss_type="client"
        )
        
        explanation = result.generate_explanation()
        
        self.assertIn("Policy Value", explanation,
                     "Should mention policy value")
        self.assertIn("70%", explanation,
                     "Should mention 70% threshold")
        # For client loss, salvage is not part of threshold calculation
        self.assertIn("policy value", explanation.lower(),
                     "Should reference policy value as basis")
        print("✅ Test 10 PASSED: Client explanation includes correct logic")

class IntegrationTests(unittest.TestCase):
    """End-to-end integration tests"""
    
    def test_complete_workflow_client_loss(self):
        """Test complete workflow for client total loss"""
        from valuation_engine import ValuationEngine
        from data_storage import DecisionStorage
        
        engine = ValuationEngine()
        storage = DecisionStorage()
        
        # Calculate decision
        result, validation = engine.calculate_total_loss(
            vin="TEST123VIN4567890",
            policy_type="comprehensive",
            policy_value=30000,
            salvage_value=6000,
            repair_quote=22000,
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertTrue(result.is_total_loss)
        
        # Store decision
        decision_id = storage.save_decision(result.to_dict())
        self.assertIsNotNone(decision_id)
        
        # Retrieve decision
        retrieved = storage.get_decision(decision_id)
        self.assertEqual(retrieved['vin'], "TEST123VIN4567890")
        
        print("✅ Integration Test 1 PASSED: Complete workflow with storage")
    
    def test_batch_processing(self):
        """Test batch processing of multiple cases"""
        engine = ValuationEngine()
        
        test_cases = [
            {
                "vin": "BATCH001VIN123456",
                "policy_type": "comprehensive",
                "policy_value": 20000,
                "salvage_value": 5000,
                "repair_quote": 15000,
                "loss_type": "client"
            },
            {
                "vin": "BATCH002VIN123457",
                "policy_type": "comprehensive",
                "policy_value": 25000,
                "salvage_value": 7000,
                "repair_quote": 13000,
                "loss_type": "third_party"
            },
            {
                "vin": "BATCH003VIN123458",
                "policy_type": "comprehensive",
                "policy_value": 30000,
                "salvage_value": 8000,
                "repair_quote": 18000,
                "loss_type": "client"
            }
        ]
        
        results = engine.calculate_batch(test_cases)
        
        self.assertEqual(len(results), 3, "Should process all 3 cases")
        
        # Check results
        self.assertTrue(results[0]['result']['decision'] == "TOTAL LOSS")
        self.assertTrue(results[1]['result']['decision'] == "TOTAL LOSS")
        self.assertFalse(results[2]['result']['decision'] == "TOTAL LOSS")
        
        print("✅ Integration Test 2 PASSED: Batch processing successful")

class PerformanceTests(unittest.TestCase):
    """Performance and load tests"""
    
    def test_calculation_performance(self):
        """Test calculation performance for single operation"""
        import time
        engine = ValuationEngine()
        
        start = time.time()
        result, validation = engine.calculate_total_loss(
            vin="PERF001VIN1234567",
            policy_type="comprehensive",
            policy_value=25000,
            salvage_value=5000,
            repair_quote=18000,
            loss_type="client"
        )
        duration = time.time() - start
        
        self.assertTrue(validation.is_valid)
        self.assertLess(duration, 0.1, "Calculation should take less than 100ms")
        print(f"✅ Performance Test PASSED: Calculation completed in {duration*1000:.2f}ms")
    
    def test_bulk_calculation_performance(self):
        """Test performance for bulk calculations"""
        import time
        engine = ValuationEngine()
        
        # Generate 100 test cases
        test_cases = []
        for i in range(100):
            test_cases.append({
                "vin": f"BULK{i:03d}VIN123456{i}",
                "policy_type": "comprehensive",
                "policy_value": 20000 + (i * 100),
                "salvage_value": 5000,
                "repair_quote": 15000 + (i * 50),
                "loss_type": "client" if i % 2 == 0 else "third_party"
            })
        
        start = time.time()
        results = engine.calculate_batch(test_cases)
        duration = time.time() - start
        
        self.assertEqual(len(results), 100, "Should process all 100 cases")
        avg_time = duration / 100
        self.assertLess(avg_time, 0.05, "Average time should be under 50ms per calculation")
        print(f"✅ Bulk Performance Test PASSED: 100 calculations in {duration:.2f}s ({avg_time*1000:.2f}ms avg)")

def run_test_suite():
    """Run all test suites and generate report"""
    import sys
    
    print("\n" + "="*70)
    print("CRASHIFY360 COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestValuationEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailTemplates))
    suite.addTests(loader.loadTestsFromTestCase(TestAIExplanation))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTests))
    suite.addTests(loader.loadTestsFromTestCase(PerformanceTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"✅ Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Failed: {len(result.failures)}")
    print(f"⚠️  Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(run_test_suite()) TestValuationEngine(unittest.TestCase):
    """Test cases for valuation engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ValuationEngine()
        self.validator = InputValidator()
    
    # ✅ 1. BASIC FUNCTIONAL TESTS
    
    def test_scenario_1_client_total_loss(self):
        """
        Scenario 1: Client Total Loss – Repair quote exceeds threshold
        Policy Type: Market
        Policy Value: $20,000
        Salvage Value: $5,000
        Repair Quote: $15,000
        Loss Type: Client
        Expected: Total Loss (Threshold = $14,000)
        """
        result, validation = self.engine.calculate_total_loss(
            vin="1HGBH41JXMN109186",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=5000,
            repair_quote=15000,
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid, "Validation should pass")
        self.assertIsNotNone(result, "Result should not be None")
        self.assertTrue(result.is_total_loss, "Should be total loss")
        self.assertEqual(result.threshold, 14000, "Threshold should be $14,000")
        self.assertEqual(result.repair_quote, 15000, "Repair quote should be $15,000")
        print(f"✅ Test 1 PASSED: Client Total Loss - {result.decision_margin:,.2f} over threshold")
    
    def test_scenario_2_third_party_total_loss(self):
        """
        Scenario 2: Third Party Total Loss – Repair quote exceeds threshold
        Policy Type: Agreed
        Policy Value: $25,000
        Salvage Value: $7,000
        Repair Quote: $13,000
        Loss Type: Third Party
        Expected: Total Loss (Threshold = $12,600)
        """
        result, validation = self.engine.calculate_total_loss(
            vin="2HGBH41JXMN109187",
            policy_type="comprehensive",
            policy_value=25000,
            salvage_value=7000,
            repair_quote=13000,
            loss_type="third_party"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertIsNotNone(result)
        self.assertTrue(result.is_total_loss, "Should be total loss")
        # Net value = 25000 - 7000 = 18000, threshold = 18000 * 0.7 = 12600
        self.assertEqual(result.threshold, 12600, "Threshold should be $12,600")
        self.assertEqual(result.repair_quote, 13000, "Repair quote should be $13,000")
        print(f"✅ Test 2 PASSED: Third Party Total Loss - {result.decision_margin:,.2f} over threshold")
    
    def test_scenario_3_client_repairable(self):
        """
        Scenario 3: Client Repairable – Repair quote below threshold
        Policy Value: $30,000
        Repair Quote: $18,000
        Expected: Repairable (Threshold = $21,000)
        """
        result, validation = self.engine.calculate_total_loss(
            vin="3HGBH41JXMN109188",
            policy_type="comprehensive",
            policy_value=30000,
            salvage_value=5000,
            repair_quote=18000,
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertIsNotNone(result)
        self.assertFalse(result.is_total_loss, "Should be repairable")
        self.assertEqual(result.threshold, 21000, "Threshold should be $21,000")
        self.assertEqual(result.repair_quote, 18000, "Repair quote should be $18,000")
        print(f"✅ Test 3 PASSED: Client Repairable - {abs(result.decision_margin):,.2f} under threshold")
    
    # ⚠️ 2. EDGE CASE TESTS
    
    def test_scenario_4_zero_salvage_value(self):
        """
        Scenario 4: Salvage value is zero
        Loss Type: Third Party
        Policy Value: $20,000
        Salvage Value: $0
        Repair Quote: $14,000
        Expected: Total Loss (Threshold = $14,000)
        """
        result, validation = self.engine.calculate_total_loss(
            vin="4HGBH41JXMN109189",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=0,
            repair_quote=14000,
            loss_type="third_party"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertIsNotNone(result)
        # Net value = 20000 - 0 = 20000, threshold = 20000 * 0.7 = 14000
        self.assertEqual(result.threshold, 14000, "Threshold should be $14,000")
        # Repair quote equals threshold, so should NOT be total loss (must exceed)
        self.assertFalse(result.is_total_loss, "Should NOT be total loss when repair equals threshold")
        print(f"✅ Test 4 PASSED: Zero Salvage - Repair exactly at threshold (Repairable)")
    
    def test_scenario_5_salvage_equals_policy(self):
        """
        Scenario 5: Salvage value equals policy value
        Loss Type: Third Party
        Policy Value: $20,000
        Salvage Value: $20,000
        Repair Quote: $1,000
        Expected: Repairable (Threshold = $0)
        """
        result, validation = self.engine.calculate_total_loss(
            vin="5HGBH41JXMN109190",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=20000,
            repair_quote=1000,
            loss_type="third_party"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertIsNotNone(result)
        # Net value = 20000 - 20000 = 0, threshold = 0 * 0.7 = 0
        self.assertEqual(result.threshold, 0, "Threshold should be $0")
        # Any positive repair quote > 0 threshold, so should be total loss
        self.assertTrue(result.is_total_loss, "Should be total loss when threshold is $0")
        print(f"✅ Test 5 PASSED: Salvage equals policy - Any repair exceeds $0 threshold")
    
    def test_scenario_6_negative_repair_quote(self):
        """
        Scenario 6: Negative repair quote (invalid input)
        Expected: Raise validation error or handle gracefully
        """
        result, validation = self.engine.calculate_total_loss(
            vin="6HGBH41JXMN109191",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=5000,
            repair_quote=-1000,  # Invalid
            loss_type="client"
        )
        
        self.assertFalse(validation.is_valid, "Validation should fail")
        self.assertIsNone(result, "Result should be None for invalid input")
        self.assertTrue(len(validation.errors) > 0, "Should have validation errors")
        
        # Check specific error
        error_fields = [e['field'] for e in validation.errors]
        self.assertIn('repair_quote', error_fields, "Should have error for repair_quote")
        print(f"✅ Test 6 PASSED: Negative repair quote rejected with validation error")
    
    def test_scenario_7_exact_threshold_client(self):
        """
        Edge case: Repair quote exactly at threshold (Client)
        Expected: Repairable (must EXCEED threshold)
        """
        policy_value = 20000
        threshold = policy_value * 0.7  # 14000
        
        result, validation = self.engine.calculate_total_loss(
            vin="7HGBH41JXMN109192",
            policy_type="comprehensive",
            policy_value=policy_value,
            salvage_value=5000,
            repair_quote=threshold,  # Exactly at threshold
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid)
        self.assertIsNotNone(result)
        self.assertFalse(result.is_total_loss, "Should NOT be total loss when exactly at threshold")
        self.assertEqual(result.decision_margin, 0, "Decision margin should be exactly 0")
        print(f"✅ Test 7 PASSED: Exact threshold - Repairable (must exceed to be total loss)")
    
    def test_scenario_8_salvage_exceeds_policy(self):
        """
        Edge case: Salvage value exceeds policy value (invalid)
        Expected: Validation error
        """
        result, validation = self.engine.calculate_total_loss(
            vin="8HGBH41JXMN109193",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=25000,  # Exceeds policy
            repair_quote=10000,
            loss_type="third_party"
        )
        
        self.assertFalse(validation.is_valid, "Validation should fail")
        self.assertIsNone(result, "Result should be None")
        error_fields = [e['field'] for e in validation.errors]
        self.assertIn('salvage_value', error_fields, "Should have error for salvage_value")
        print(f"✅ Test 8 PASSED: Salvage exceeding policy rejected")
    
    def test_scenario_9_extremely_high_repair_quote(self):
        """
        Edge case: Repair quote is 200% of policy value
        Expected: Total loss with warning
        """
        result, validation = self.engine.calculate_total_loss(
            vin="9HGBH41JXMN109194",
            policy_type="comprehensive",
            policy_value=20000,
            salvage_value=5000,
            repair_quote=40000,  # 200% of policy
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid, "Should be valid but with warnings")
        self.assertIsNotNone(result)
        self.assertTrue(result.is_total_loss, "Should be total loss")
        # Check for warning about high repair quote
        self.assertTrue(len(validation.warnings) > 0, "Should have warnings")
        print(f"✅ Test 9 PASSED: Extremely high repair quote flagged with warning")
    
    def test_scenario_10_minimum_valid_values(self):
        """
        Edge case: Minimum valid values
        Expected: Pass validation
        """
        result, validation = self.engine.calculate_total_loss(
            vin="AHGBH41JXMN109195",
            policy_type="comprehensive",
            policy_value=config.VALIDATION_RULES["min_policy_value"],  # $1,000
            salvage_value=0,
            repair_quote=0,
            loss_type="client"
        )
        
        self.assertTrue(validation.is_valid, "Should pass validation with minimum values")
        self.assertIsNotNone(result)
        self.assertFalse(result.is_total_loss, "Should be repairable with $0 repair quote")
        print(f"✅ Test 10 PASSED: Minimum valid values accepted")

class TestValidator(unittest.TestCase):
    """Test cases for input validator"""
    
    def setUp(self):
        self.validator = InputValidator()
    
    def test_valid_vin(self):
        """Test valid VIN validation"""
        self.assertTrue(self.validator.validate_vin("1HGBH41JXMN109186"))
        self.assertTrue(self.validator.validate_vin("WBADT43452G812293"))
        print("✅ Valid VIN test passed")
    
    def test_invalid_vin_length(self):
        """Test VIN with wrong length"""
        self.assertFalse(self.validator.validate_vin("1HGBH41JX"))  # Too short
        self.assertFalse(self.validator.validate_vin("1HGBH41JXMN109186XX"))  # Too long
        print("✅ Invalid VIN length test passed")
    
    def test_invalid_vin_characters(self):
        """Test VIN with invalid characters (I, O, Q)"""
        self.assertFalse(self.validator.validate_vin("1HGBH41IXMN109186"))  # Contains I
        self.assertFalse(self.validator.validate_vin("1HGBH41OXMN109186"))  # Contains O
        self.assertFalse(self.validator.validate_vin("1HGBH41QXMN109186"))  # Contains Q
        print("✅ Invalid VIN characters test passed")
    
    def test_valid_email(self):
        """Test email validation"""
        self.assertTrue(self.validator.validate_email("test@example.com"))
        self.assertTrue(self.validator.validate_email("user.name+tag@domain.com.au"))
        print("✅ Valid email test passed")
    
    def test_invalid_email(self):
        """Test invalid email formats"""
        self.assertFalse(self.validator.validate_email("invalid.email"))
        self.assertFalse(self.validator.validate_email("@example.com"))
        self.assertFalse(self.validator.validate_email("user@"))
        print("✅ Invalid email test passed")
    
    def test_valid_australian_phone(self):
        """Test Australian phone number validation"""
        self.assertTrue(self.validator.validate_phone("0412345678"))
        self.assertTrue(self.validator.validate_phone("+61412345678"))
        self.assertTrue(self.validator.validate_phone("04 1234 5678"))
        self.assertTrue(self.validator.validate_phone("(04) 1234 5678"))
        print("✅ Valid phone test passed")
    
    def test_invalid_phone(self):
        """Test invalid phone numbers"""
        self.assertFalse(self.validator.validate_phone("1234"))
        self.assertFalse(self.validator.validate_phone("0000000000"))
        self.assertFalse(self.validator.validate_phone("+1234567890"))  # Wrong country
        print("✅ Invalid phone test passed")
    
    def test_sanitize_input(self):
        """Test input sanitization"""
        dirty_input = "Hello\x00World\nTest\t<script>"
        clean = self.validator.sanitize_input(dirty_input)
        self.assertNotIn('\x00', clean, "Should remove null bytes")
        self.assertIn('\n', clean, "Should preserve newlines")
        self.assertIn('\t', clean, "Should preserve tabs")
        print("✅ Input sanitization test passed")

class
