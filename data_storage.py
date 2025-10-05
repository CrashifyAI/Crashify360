"""
Crashify360 - Data Persistence Layer
Store and retrieve decision data with JSON backend
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import config
from logger import get_logger

logger = get_logger()

class DecisionStorage:
    """Persistent storage for total loss decisions"""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or config.PATHS["decisions"]
        self.logger = logger
        
        # Ensure directory exists
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize storage file if it doesn't exist
        if not os.path.exists(self.storage_path):
            self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize empty storage file"""
        data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "decisions": []
        }
        self._write_data(data)
        self.logger.info(f"Initialized storage at {self.storage_path}")
    
    def _read_data(self) -> Dict:
        """Read data from storage file"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f"Error reading storage", error=e)
            self._initialize_storage()
            return self._read_data()
    
    def _write_data(self, data: Dict):
        """Write data to storage file"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error writing storage", error=e)
            raise
    
    def save_decision(self, decision_data: Dict[str, Any]) -> str:
        """
        Save a decision to storage
        
        Args:
            decision_data: Decision data dictionary
        
        Returns:
            Decision ID
        """
        data = self._read_data()
        
        # Generate decision ID
        decision_id = f"DEC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(data['decisions']) + 1:04d}"
        
        # Add metadata
        decision_record = {
            "id": decision_id,
            "stored_at": datetime.now().isoformat(),
            **decision_data
        }
        
        # Append to decisions
        data['decisions'].append(decision_record)
        
        # Write back
        self._write_data(data)
        
        self.logger.info(f"Saved decision {decision_id}",
                        vin=decision_data.get('vin'),
                        decision=decision_data.get('decision'))
        
        return decision_id
    
    def get_decision(self, decision_id: str) -> Optional[Dict]:
        """
        Retrieve a decision by ID
        
        Args:
            decision_id: Decision ID
        
        Returns:
            Decision data or None if not found
        """
        data = self._read_data()
        
        for decision in data['decisions']:
            if decision['id'] == decision_id:
                return decision
        
        return None
    
    def get_decisions_by_vin(self, vin: str) -> List[Dict]:
        """
        Get all decisions for a specific VIN
        
        Args:
            vin: Vehicle Identification Number
        
        Returns:
            List of decisions
        """
        data = self._read_data()
        
        return [d for d in data['decisions'] if d.get('vin') == vin]
    
    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """
        Get most recent decisions
        
        Args:
            limit: Maximum number of decisions to return
        
        Returns:
            List of recent decisions
        """
        data = self._read_data()
        
        # Sort by stored_at descending
        sorted_decisions = sorted(
            data['decisions'],
            key=lambda x: x.get('stored_at', ''),
            reverse=True
        )
        
        return sorted_decisions[:limit]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored decisions
        
        Returns:
            Dictionary with statistics
        """
        data = self._read_data()
        decisions = data['decisions']
        
        if not decisions:
            return {
                "total_decisions": 0,
                "total_losses": 0,
                "repairable": 0,
                "avg_policy_value": 0,
                "avg_repair_quote": 0,
                "loss_types": {}
            }
        
        total_losses = sum(1 for d in decisions if d.get('decision') == 'TOTAL LOSS')
        repairable = sum(1 for d in decisions if d.get('decision') == 'REPAIRABLE')
        
        policy_values = [d.get('policy_value', 0) for d in decisions if d.get('policy_value')]
        repair_quotes = [d.get('repair_quote', 0) for d in decisions if d.get('repair_quote')]
        
        # Count by loss type
        loss_types = {}
        for d in decisions:
            lt = d.get('loss_type', 'unknown')
            loss_types[lt] = loss_types.get(lt, 0) + 1
        
        return {
            "total_decisions": len(decisions),
            "total_losses": total_losses,
            "repairable": repairable,
            "total_loss_percentage": (total_losses / len(decisions) * 100) if decisions else 0,
            "avg_policy_value": sum(policy_values) / len(policy_values) if policy_values else 0,
            "avg_repair_quote": sum(repair_quotes) / len(repair_quotes) if repair_quotes else 0,
            "loss_types": loss_types,
            "first_decision": decisions[0].get('stored_at') if decisions else None,
            "last_decision": decisions[-1].get('stored_at') if decisions else None
        }
    
    def search_decisions(self, 
                        min_policy_value: Optional[float] = None,
                        max_policy_value: Optional[float] = None,
                        loss_type: Optional[str] = None,
                        decision: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """
        Search decisions with filters
        
        Args:
            min_policy_value: Minimum policy value
            max_policy_value: Maximum policy value
            loss_type: Filter by loss type
            decision: Filter by decision (TOTAL LOSS or REPAIRABLE)
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
        
        Returns:
            List of matching decisions
        """
        data = self._read_data()
        results = data['decisions']
        
        # Apply filters
        if min_policy_value is not None:
            results = [d for d in results if d.get('policy_value', 0) >= min_policy_value]
        
        if max_policy_value is not None:
            results = [d for d in results if d.get('policy_value', 0) <= max_policy_value]
        
        if loss_type:
            results = [d for d in results if d.get('loss_type') == loss_type]
        
        if decision:
            results = [d for d in results if d.get('decision') == decision]
        
        if start_date:
            results = [d for d in results if d.get('stored_at', '') >= start_date]
        
        if end_date:
            results = [d for d in results if d.get('stored_at', '') <= end_date]
        
        return results
    
    def export_to_csv(self, output_path: str):
        """
        Export decisions to CSV file
        
        Args:
            output_path: Path for CSV file
        """
        import csv
        
        data = self._read_data()
        decisions = data['decisions']
        
        if not decisions:
            self.logger.warning("No decisions to export")
            return
        
        # Get all keys from first decision
        fieldnames = list(decisions[0].keys())
        
        try:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(decisions)
            
            self.logger.info(f"Exported {len(decisions)} decisions to {output_path}")
        
        except Exception as e:
            self.logger.error(f"Error exporting to CSV", error=e)
            raise
    
    def clear_all_decisions(self, confirm: bool = False):
        """
        Clear all decisions (USE WITH CAUTION)
        
        Args:
            confirm: Must be True to actually clear
        """
        if not confirm:
            raise ValueError("Must confirm to clear all decisions")
        
        self._initialize_storage()
        self.logger.warning("All decisions cleared from storage")

# Global storage instance
storage = DecisionStorage()

if __name__ == "__main__":
    # Test storage
    print("Testing Data Storage...")
    
    # Create test decision
    test_decision = {
        "vin": "TEST123VIN4567890",
        "timestamp": datetime.now().isoformat(),
        "decision": "TOTAL LOSS",
        "loss_type": "client",
        "policy_type": "comprehensive",
        "policy_value": 25000.00,
        "salvage_value": 5000.00,
        "repair_quote": 18000.00,
        "threshold": 17500.00
    }
    
    # Save decision
    decision_id = storage.save_decision(test_decision)
    print(f"✅ Saved decision: {decision_id}")
    
    # Retrieve decision
    retrieved = storage.get_decision(decision_id)
    print(f"✅ Retrieved decision: {retrieved['vin']}")
    
    # Get statistics
    stats = storage.get_statistics()
    print(f"✅ Statistics: {stats['total_decisions']} total decisions")
    
    # Search decisions
    results = storage.search_decisions(loss_type="client")
    print(f"✅ Search found {len(results)} client loss decisions")
    
    print("\n✅ Storage tests complete")

