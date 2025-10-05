"""
Crashify360 - Main Entry Point
CLI interface for running assessments and tests
"""

import argparse
import json
import sys
from pathlib import Path

import config
from valuation_engine import ValuationEngine
from validator import InputValidator
from data_storage import DecisionStorage
from logger import get_logger
from autograp_api import AutoGrapAPI

logger = get_logger()

def run_assessment(args):
    """Run a single assessment from CLI"""
    engine = ValuationEngine()
    
    print("\n" + "="*70)
    print("CRASHIFY360 - TOTAL LOSS ASSESSMENT")
    print("="*70 + "\n")
    
    result, validation = engine.calculate_total_loss(
        vin=args.vin,
        policy_type=args.policy_type,
        policy_value=args.policy_value,
        salvage_value=args.salvage_value,
        repair_quote=args.repair_quote,
        loss_type=args.loss_type
    )
    
    if not validation.is_valid:
        print("❌ VALIDATION FAILED:")
        print(validation.get_summary())
        return 1
    
    if validation.warnings:
        print("⚠️  WARNINGS:")
        for warning in validation.warnings:
            print(f"  • {warning['field']}: {warning['message']}")
        print()
    
    # Display result
    print(result.generate_explanation())
    
    # Save to storage
    if not args.no_save:
        storage = DecisionStorage()
        decision_id = storage.save_decision(result.to_dict())
        print(f"\n✅ Decision saved with ID: {decision_id}")
    
    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            if args.format == 'json':
                json.dump(result.to_dict(), f, indent=2)
            else:
                f.write(result.generate_explanation())
        
        print(f"✅ Output saved to: {output_path}")
    
    return 0

def run_batch(args):
    """Run batch assessment from JSON file"""
    engine = ValuationEngine()
    
    print("\n" + "="*70)
    print("CRASHIFY360 - BATCH ASSESSMENT")
    print("="*70 + "\n")
    
    # Load input file
    try:
        with open(args.input_file, 'r') as f:
            cases = json.load(f)
    except FileNotFoundError:
        print(f"❌ Input file not found: {args.input_file}")
        return 1
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in input file")
        return 1
    
    if not isinstance(cases, list):
        print(f"❌ Input file must contain a list of cases")
        return 1
    
    print(f"Processing {len(cases)} cases...\n")
    
    results = engine.calculate_batch(cases)
    
    # Summary
    successful = sum(1 for r in results if r['result'] is not None)
    failed = len(results) - successful
    total_losses = sum(1 for r in results if r['result'] and r['result']['decision'] == 'TOTAL LOSS')
    
    print(f"\n{'='*70}")
    print("BATCH SUMMARY")
    print("="*70)
    print(f"Total Cases: {len(cases)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"🔴 Total Losses: {total_losses}")
    print(f"🟢 Repairable: {successful - total_losses}")
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {args.output}")
    
    return 0

def run_vin_lookup(args):
    """Lookup vehicle by VIN"""
    api_client = AutoGrapAPI()
    
    print("\n" + "="*70)
    print("CRASHIFY360 - VIN LOOKUP")
    print("="*70 + "\n")
    
    try:
        result = api_client.get_market_value(args.vin)
        
        print(f"Vehicle: {result['year']} {result['make']} {result['model']}")
        print(f"Variant: {result.get('variant', 'N/A')}")
        print(f"\nValuation:")
        print(f"  Market Value:   ${result['market_value']:,.2f}")
        print(f"  Trade-In Value: ${result['trade_in_value']:,.2f}")
        print(f"  Retail Value:   ${result['retail_value']:,.2f}")
        print(f"\nConfidence: {result['confidence']}")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✅ Data saved to: {args.output}")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

def run_statistics(args):
    """Display statistics"""
    storage = DecisionStorage()
    stats = storage.get_statistics()
    
    print("\n" + "="*70)
    print("CRASHIFY360 - STATISTICS")
    print("="*70 + "\n")
    
    print(f"Total Decisions: {stats['total_decisions']}")
    print(f"Total Losses: {stats['total_losses']} ({stats['total_loss_percentage']:.1f}%)")
    print(f"Repairable: {stats['repairable']}")
    print(f"\nFinancial Metrics:")
    print(f"  Average Policy Value: ${stats['avg_policy_value']:,.2f}")
    print(f"  Average Repair Quote: ${stats['avg_repair_quote']:,.2f}")
    print(f"\nLoss Types:")
    for loss_type, count in stats['loss_types'].items():
        print(f"  {loss_type}: {count}")
    
    if stats['first_decision']:
        print(f"\nFirst Decision: {stats['first_decision'][:10]}")
        print(f"Last Decision: {stats['last_decision'][:10]}")
    
    return 0

def run_tests(args):
    """Run test suite"""
    print("\n" + "="*70)
    print("CRASHIFY360 - RUNNING TESTS")
    print("="*70 + "\n")
    
    from test_suite import run_test_suite
    return run_test_suite()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Crashify360 - Total Loss Assessment System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single assessment
  python main.py assess --vin 1HGBH41JXMN109186 --policy-value 25000 --salvage-value 5000 --repair-quote 18000 --loss-type client
  
  # Run batch assessment
  python main.py batch --input test_cases/batch_input.json --output output/batch_results.json
  
  # VIN lookup
  python main.py lookup --vin 1HGBH41JXMN109186 --output output/vin_data.json
  
  # View statistics
  python main.py stats
  
  # Run tests
  python main.py test
  
  # Start web UI
  streamlit run web_ui.py
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Assessment command
    assess_parser = subparsers.add_parser('assess', help='Run single assessment')
    assess_parser.add_argument('--vin', required=True, help='Vehicle VIN')
    assess_parser.add_argument('--policy-type', default='comprehensive', 
                              choices=config.POLICY_TYPES, help='Policy type')
    assess_parser.add_argument('--policy-value', type=float, required=True, help='Policy value')
    assess_parser.add_argument('--salvage-value', type=float, required=True, help='Salvage value')
    assess_parser.add_argument('--repair-quote', type=float, required=True, help='Repair quote')
    assess_parser.add_argument('--loss-type', choices=['client', 'third_party'], 
                              default='client', help='Loss type')
    assess_parser.add_argument('--output', help='Output file path')
    assess_parser.add_argument('--format', choices=['txt', 'json'], default='txt', 
                              help='Output format')
    assess_parser.add_argument('--no-save', action='store_true', 
                              help='Do not save to database')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Run batch assessment')
    batch_parser.add_argument('--input', dest='input_file', required=True, 
                             help='Input JSON file with cases')
    batch_parser.add_argument('--output', help='Output JSON file for results')
    
    # VIN lookup command
    lookup_parser = subparsers.add_parser('lookup', help='Lookup vehicle by VIN')
    lookup_parser.add_argument('--vin', required=True, help='Vehicle VIN')
    lookup_parser.add_argument('--output', help='Output JSON file')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Display statistics')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run test suite')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize directories
    config.initialize_directories()
    
    # Route to appropriate function
    if args.command == 'assess':
        return run_assessment(args)
    elif args.command == 'batch':
        return run_batch(args)
    elif args.command == 'lookup':
        return run_vin_lookup(args)
    elif args.command == 'stats':
        return run_statistics(args)
    elif args.command == 'test':
        return run_tests(args)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
