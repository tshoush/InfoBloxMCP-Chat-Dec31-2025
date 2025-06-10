"""InfoBlox API client for WAPI integration."""

import json
import logging
import time
from typing import Dict, Any, Optional, List, Union
from urllib.parse import urljoin, quote
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import InfoBloxConfig


logger = logging.getLogger(__name__)


class InfoBloxAPIError(Exception):
    """InfoBlox API specific error."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class InfoBloxClient:
    """InfoBlox WAPI client."""
    
    def __init__(self, config: InfoBloxConfig):
        """Initialize InfoBlox client."""
        self.config = config
        self.base_url = f"https://{config.grid_master_ip}/wapi/{config.wapi_version}/"
        self.session = requests.Session()
        self.session_cookie = None
        self._setup_session()
        self._authenticate()
    
    def _setup_session(self):
        """Setup HTTP session with retry strategy."""
        # Setup retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set timeout and SSL verification
        self.session.timeout = self.config.timeout
        self.session.verify = self.config.verify_ssl
        
        # Set headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'InfoBlox-MCP-Server/1.0.0'
        })
    
    def _authenticate(self):
        """Authenticate with InfoBlox and get session cookie."""
        try:
            # Use basic auth for initial authentication
            auth = (self.config.username, self.config.password)
            
            # Make a simple request to get session cookie
            response = self.session.get(
                urljoin(self.base_url, "grid"),
                auth=auth,
                params={'_return_type': 'json'}
            )
            
            if response.status_code == 200:
                # Extract session cookie
                if 'ibapauth' in response.cookies:
                    self.session_cookie = response.cookies['ibapauth']
                    # Remove basic auth and use cookie for subsequent requests
                    self.session.auth = None
                    logger.info("Successfully authenticated with InfoBlox")
                else:
                    logger.warning("Authentication successful but no session cookie received")
            else:
                self._handle_error_response(response, "Authentication failed")
                
        except requests.exceptions.RequestException as e:
            raise InfoBloxAPIError(f"Connection error during authentication: {str(e)}")
    
    def _handle_error_response(self, response: requests.Response, context: str = "API request"):
        """Handle error responses from InfoBlox API."""
        try:
            error_data = response.json()
        except (json.JSONDecodeError, ValueError):
            error_data = {"text": response.text}
        
        # Map HTTP status codes to user-friendly messages
        error_messages = {
            400: "Invalid request parameters",
            401: "Authentication required or failed",
            403: "Insufficient permissions for this operation",
            404: "Requested object not found",
            409: "Object already exists or conflict detected",
            500: "InfoBlox server internal error",
            502: "InfoBlox server unavailable (Bad Gateway)",
            503: "InfoBlox server temporarily unavailable",
            504: "Request timeout (Gateway Timeout)"
        }
        
        base_message = error_messages.get(response.status_code, f"HTTP {response.status_code} error")
        
        # Extract InfoBlox specific error details
        if isinstance(error_data, dict):
            if 'Error' in error_data:
                infoblox_error = error_data['Error']
                message = f"{context}: {base_message} - {infoblox_error}"
            elif 'text' in error_data:
                message = f"{context}: {base_message} - {error_data['text']}"
            else:
                message = f"{context}: {base_message}"
        else:
            message = f"{context}: {base_message}"
        
        logger.error(f"InfoBlox API Error: {message}")
        raise InfoBloxAPIError(message, response.status_code, error_data)
    
    def _refresh_session(self):
        """Refresh session if needed."""
        if self.session_cookie is None:
            logger.info("Session cookie not found, re-authenticating")
            self._authenticate()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_auth: bool = True
    ) -> Dict[str, Any]:
        """Make HTTP request to InfoBlox API."""
        url = urljoin(self.base_url, endpoint)
        
        # Prepare request parameters
        request_params = params or {}
        if '_return_type' not in request_params:
            request_params['_return_type'] = 'json'
        
        # Prepare request data
        request_data = None
        if data is not None:
            request_data = json.dumps(data)
        
        try:
            logger.debug(f"Making {method} request to {endpoint}")
            response = self.session.request(
                method=method,
                url=url,
                params=request_params,
                data=request_data
            )
            
            # Handle authentication errors with retry
            if response.status_code == 401 and retry_auth:
                logger.info("Authentication expired, refreshing session")
                self._authenticate()
                return self._make_request(method, endpoint, params, data, retry_auth=False)
            
            # Handle successful responses
            if response.status_code in [200, 201]:
                try:
                    return response.json()
                except (json.JSONDecodeError, ValueError):
                    # Some responses might not be JSON
                    return {"result": response.text}
            
            # Handle error responses
            self._handle_error_response(response, f"{method} {endpoint}")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {str(e)}")
            raise InfoBloxAPIError(f"Network error: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", endpoint, params=params, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, params=params, data=data)
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, params=params)
    
    def logout(self):
        """Logout and invalidate session."""
        try:
            if self.session_cookie:
                self.post("logout")
                self.session_cookie = None
                logger.info("Successfully logged out from InfoBlox")
        except Exception as e:
            logger.warning(f"Error during logout: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test connection to InfoBlox."""
        try:
            result = self.get("grid")
            return isinstance(result, (list, dict))
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    # Utility methods for common operations
    
    def search_objects(self, object_type: str, search_params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search for objects of a specific type."""
        params = search_params or {}
        result = self.get(object_type, params=params)
        return result if isinstance(result, list) else [result]
    
    def get_object_by_ref(self, object_ref: str, return_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get object by reference."""
        params = {}
        if return_fields:
            params['_return_fields'] = ','.join(return_fields)
        return self.get(object_ref, params=params)
    
    def create_object(self, object_type: str, object_data: Dict[str, Any]) -> str:
        """Create new object and return its reference."""
        result = self.post(object_type, data=object_data)
        if isinstance(result, str):
            return result  # Object reference
        elif isinstance(result, dict) and '_ref' in result:
            return result['_ref']
        else:
            raise InfoBloxAPIError("Unexpected response format for object creation")
    
    def update_object(self, object_ref: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing object."""
        return self.put(object_ref, data=update_data)
    
    def delete_object(self, object_ref: str) -> Dict[str, Any]:
        """Delete object by reference."""
        return self.delete(object_ref)
    
    def get_next_available_ip(self, network: str, num_ips: int = 1) -> List[str]:
        """Get next available IP addresses in a network."""
        params = {
            '_function': 'next_available_ip',
            'num': num_ips
        }
        result = self.post(f"network/{quote(network, safe='')}", params=params)
        if isinstance(result, dict) and 'ips' in result:
            return result['ips']
        return []
    
    def get_network_utilization(self, network_ref: str) -> Dict[str, Any]:
        """Get network utilization statistics."""
        return self.get(f"{network_ref}?_function=utilization")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.logout()

