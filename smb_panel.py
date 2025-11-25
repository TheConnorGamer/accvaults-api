import requests
from typing import Dict, List, Optional, Union, Any
import json

class SMBApiClient:
    BASE_URL = 'https://smbpanel.net/api/v2'
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SMBPanel-Discord-Bot/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def _make_request(self, action: str, data: Optional[Dict] = None) -> Dict:
        if data is None:
            data = {}
            
        data.update({
            'key': self.api_key,
            'action': action
        })
        
        try:
            response = self.session.post(self.BASE_URL, data=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': f'API request failed: {str(e)}'}
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        return self._make_request('balance')
    
    def get_services(self) -> List[Dict]:
        """Get list of available services"""
        result = self._make_request('services')
        return result if isinstance(result, list) else []
    
    def create_order(self, service_id: int, link: str, quantity: int, **kwargs) -> Dict:
        """Create a new order"""
        data = {
            'service': service_id,
            'link': link,
            'quantity': quantity,
            **kwargs
        }
        return self._make_request('add', data)
    
    def get_order_status(self, order_id: Union[int, List[int]]) -> Dict:
        """Get status of one or multiple orders"""
        if isinstance(order_id, list):
            return self._make_request('status', {'orders': ','.join(map(str, order_id))})
        return self._make_request('status', {'order': order_id})
    
    def refill_order(self, order_id: Union[int, List[int]]) -> Dict:
        """Request refill for one or multiple orders"""
        if isinstance(order_id, list):
            return self._make_request('refill', {'orders': ','.join(map(str, order_id))})
        return self._make_request('refill', {'order': order_id})
    
    def get_refill_status(self, refill_id: Union[int, List[int]]) -> Dict:
        """Get status of one or multiple refills"""
        if isinstance(refill_id, list):
            return self._make_request('refill_status', {'refills': ','.join(map(str, refill_id))})
        return self._make_request('refill_status', {'refill': refill_id})
    
    def cancel_orders(self, order_ids: List[int]) -> Dict:
        """Cancel one or multiple orders"""
        return self._make_request('cancel', {'orders': ','.join(map(str, order_ids))})
