
import json
import logging
import time
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import urljoin

from .config import InfoBloxConfig

logger = logging.getLogger(__name__)

class SplunkClient:
    """Client for interacting with Splunk REST API."""
    
    def __init__(self, config: InfoBloxConfig):
        """Initialize Splunk client."""
        self.config = config
        self.base_url = config.splunk_url
        if not self.base_url:
            raise ValueError("Splunk URL not configured")
        
        # Ensure base URL ends correctly for joining. 
        # Usually Splunk API is at port 8089.
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        self.session = requests.Session()
        self.session.verify = config.verify_ssl
        
        # Determine Authentication Method
        if config.splunk_token:
            self.session.headers.update({"Authorization": f"Bearer {config.splunk_token}"})
        elif config.splunk_username and config.splunk_password:
            self.session.auth = (config.splunk_username, config.splunk_password)
        else:
            raise ValueError("Splunk credentials not configured. Please check config.")

    def search(self, query: str, earliest_time: str = "-30d", latest_time: str = "now", count: int = 100) -> List[Dict[str, Any]]:
        """
        Execute a Splunk search and return results.
        Uses the blocking mode for simplicity.
        """
        if not query.startswith("search"):
            query = f"search {query}"
            
        # Endpoint for blocking search
        endpoint = urljoin(self.base_url, "services/search/jobs/export")
        
        params = {
            "search": query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "output_mode": "json",
            "exec_mode": "blocking"
        }
        
        try:
            logger.info(f"Executing Splunk search: {query}")
            response = self.session.post(endpoint, data=params, timeout=60) # 60s timeout for search
            response.raise_for_status()
            
            # The export endpoint returns a stream of JSON objects, not a single JSON list.
            # We need to parse line by line.
            results = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        # Export endpoint sometimes returns metadata/progress, we just want results
                        if "result" in data:
                            results.append(data["result"])
                        elif isinstance(data, dict) and not "pk" in data: # Try direct dict if flattened
                            results.append(data)
                            
                        if len(results) >= count:
                            break
                    except json.JSONDecodeError:
                        continue
                        
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Splunk search failed: {str(e)}")
            if e.response is not None:
                logger.error(f"Splunk response: {e.response.text}")
            raise Exception(f"Splunk search failed: {str(e)}")

