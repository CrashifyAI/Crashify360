"""
Crashify360 - Auto Grap API Client
Enhanced API client with retry logic, rate limiting, and error handling
"""

import requests
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import config
from logger import get_logger

logger = get_logger()

class APIError(Exception):
    """Custom API error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 100, time_window: int = 3600):
        self.max_calls = max_calls
        self.time_window = time_window  # seconds
        self.calls = []
    
    def can_call(self) -> bool:
        """Check if we can make another API call"""
        now = datetime.now()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < timedelta(seconds=self.time_window)]
        return len(self.calls) < self.max_calls
    
    def add_call(self):
        """Record an API call"""
        self.calls.append(datetime.now())
    
    def wait_time(self) -> float:
        """Get seconds to wait before next call is available"""
        if self.can_call():
            return 0
        
        oldest_call = min(self.calls)
        wait_until = oldest_call + timedelta(seconds=self.time_window)
        return (wait_until - datetime.now()).total_seconds()

class AutoGrapAPI:
    """Enhanced Auto Grap API client"""
    
    def __init__(self):
        self.api_key = config.AUTO_GRAP_CONFIG["api_key"]
        self.base_url = config.AUTO_GRAP_CONFIG["base_url"]
        self.timeout = config.AUTO_GRAP_CONFIG["timeout"]
        self.max_retries = config.AUTO_GRAP_CONFIG["max_retries"]
        self.retry_delay = config.AUTO_GRAP_CONFIG["retry_delay"]
        self.rate_limiter = RateLimiter(max_calls=100, time_window=3600)
        self.logger = logger
        
        if not self.api_key:
            self.logger.warning("Auto Grap API key not configured")
    
    def _make_request(self, 
                     endpoint: str,
                     method: str = "GET",
                     params: Optional[Dict] = None,
                     data: Optional[Dict] = None,
                     retry_count: int = 0) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body
            retry_count: Current retry attempt
        
        Returns:
            Response data as dictionary
        """
        # Check rate limit
        if not self.rate_limiter.can_call():
            wait_time = self.rate_limiter.wait_time()
            self.logger.warning(f"Rate limit reached. Waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        try:
            self.logger.info(f"Making {method} request to {endpoint}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            duration = (time.time() - start_time) * 1000  # ms
            self.rate_limiter.add_call()
            
            # Log API call
            self.logger.log_api_call(
                api_name="Auto Grap",
                endpoint=endpoint,
                status_code=response.status_code,
                duration=duration,
                success=response.status_code == 200
            )
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            
            elif response.status_code == 429:  # Rate limited
                if retry_count < self.max_retries:
                    retry_after = int(response.headers.get('Retry-After', self.retry_delay * (retry_count + 1)))
                    self.logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
                    time.sleep(retry_after)
                    return self._make_request(endpoint, method, params, data, retry_count + 1)
                else:
                    raise APIError("Rate limit exceeded", status_code=429)
            
            elif response.status_code >= 500:  # Server error
                if retry_count < self.max_retries:
                    wait_time = self.retry_delay * (2 ** retry_count)  # Exponential backoff
                    self.logger.warning(f"Server error {response.status_code}. Retrying in {wait_time} seconds")
                    time.sleep(wait_time)
                    return self._make_request(endpoint, method, params, data, retry_count + 1)
                else:
                    raise APIError(f"Server error: {response.status_code}", status_code=response.status_code)
            
            else:
                error_msg = f"API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', '')}"
                except:
                    error_msg += f" - {response.text}"
                
                raise APIError(error_msg, status_code=response.status_code)
        
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                self.logger.warning(f"Request timeout. Retry {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)
                return self._make_request(endpoint, method, params, data, retry_count + 1)
            else:
                raise APIError("Request timeout after retries")
        
        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                self.logger.warning(f"Connection error. Retry {retry_count + 1}/{self.max_retries}")
                time.sleep(self.retry_delay)
                return self._make_request(endpoint, method, params, data, retry_count + 1)
            else:
                raise APIError(f"Connection error: {str(e)}")
        
        except APIError:
            raise
        
        except Exception as e:
            self.logger.error(f"Unexpected error in API request", error=e)
            raise APIError(f"Unexpected error: {str(e)}")
    
    def get_market_value(self, vin: str, year: Optional[int] = None, make: Optional[str] = None, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get market value for a vehicle
        
        Args:
            vin: Vehicle Identification Number
            year: Vehicle year (optional)
            make: Vehicle make (optional)
            model: Vehicle model (optional)
        
        Returns:
            Dictionary with valuation data
        """
        if not self.api_key:
            raise APIError("Auto Grap API key not configured")
        
        params = {"vin": vin}
        if year:
            params["year"] = year
        if make:
            params["make"] = make
        if model:
            params["model"] = model
        
        try:
            response = self._make_request("valuation", params=params)
            
            # Extract relevant data
            result = {
                "vin": vin,
                "market_value": response.get("market_value", 0),
                "trade_in_value": response.get("trade_in_value", 0),
                "retail_value": response.get("retail_value", 0),
                "year": response.get("year"),
                "make": response.get("make"),
                "model": response.get("model"),
                "variant": response.get("variant"),
                "odometer": response.get("odometer"),
                "confidence": response.get("confidence", "medium"),
                "last_updated": response.get("last_updated")
            }
            
            self.logger.info(f"Retrieved market value for VIN {vin}",
                           market_value=result["market_value"],
                           confidence=result["confidence"])
            
            return result
        
        except APIError as e:
            self.logger.error(f"Failed to get market value for VIN {vin}", error=e)
            raise
    
    def get_vehicle_details(self, vin: str) -> Dict[str, Any]:
        """
        Get detailed vehicle information
        
        Args:
            vin: Vehicle Identification Number
        
        Returns:
            Dictionary with vehicle details
        """
        if not self.api_key:
            raise APIError("Auto Grap API key not configured")
        
        try:
            response = self._make_request(f"vehicles/{vin}")
            
            self.logger.info(f"Retrieved vehicle details for VIN {vin}")
            
            return response
        
        except APIError as e:
            self.logger.error(f"Failed to get vehicle details for VIN {vin}", error=e)
            raise
    
    def health_check(self) -> bool:
        """
        Check if API is accessible
        
        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self._make_request("health")
            return response.get("status") == "ok"
        except:
            return False

# Global API instance
api_client = AutoGrapAPI()

if __name__ == "__main__":
    # Test API client
    print("Testing Auto Grap API Client...")
    
    # Health check
    print(f"API Health: {'✅ OK' if api_client.health_check() else '❌ Failed'}")
    
    # Test VIN lookup (will fail without valid API key)
    try:
        result = api_client.get_market_value("1HGBH41JXMN109186")
        print(f"\nMarket Value: ${result['market_value']:,.2f}")
        print(f"Vehicle: {result['year']} {result['make']} {result['model']}")
    except APIError as e:
        print(f"\n❌ API Error: {e.message}")

