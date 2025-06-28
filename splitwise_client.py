"""Splitwise API client with OAuth authentication."""

import logging
import json
import webbrowser
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse
import requests
from requests_oauthlib import OAuth2Session

from config import config
from models import SplitwiseExpense, SplitwiseExpenseResponse

logger = logging.getLogger(__name__)

class SplitwiseClient:
    """Client for interacting with Splitwise API using OAuth2."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize Splitwise client."""
        if not config.SPLITWISE_CLIENT_ID or not config.SPLITWISE_CLIENT_SECRET:
            raise ValueError("Splitwise client ID and secret are required")
        
        self.client_id = config.SPLITWISE_CLIENT_ID
        self.client_secret = config.SPLITWISE_CLIENT_SECRET
        self.redirect_uri = config.SPLITWISE_REDIRECT_URI
        self.base_url = config.SPLITWISE_BASE_URL
        self.auth_url = config.SPLITWISE_AUTH_URL
        self.token_url = config.SPLITWISE_TOKEN_URL
        
        self.access_token = access_token
        self.session = requests.Session()
        
        if self.access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
    
    def get_authorization_url(self) -> str:
        """Get the authorization URL for OAuth flow."""
        oauth = OAuth2Session(
            client_id=self.client_id,
            redirect_uri=self.redirect_uri,
            scope=['user', 'expenses']
        )
        
        authorization_url, state = oauth.authorization_url(self.auth_url)
        logger.info(f"Authorization URL: {authorization_url}")
        return authorization_url
    
    def authorize_interactive(self) -> str:
        """Interactive OAuth authorization flow."""
        auth_url = self.get_authorization_url()
        
        print(f"\nPlease visit this URL to authorize the application:")
        print(f"{auth_url}")
        print("\nOpening browser...")
        
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
        
        # Get authorization code from user
        callback_url = input("\nPaste the full callback URL here: ").strip()
        
        # Extract authorization code
        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' not in query_params:
            raise ValueError("Authorization code not found in callback URL")
        
        auth_code = query_params['code'][0]
        return self.exchange_code_for_token(auth_code)
    
    def exchange_code_for_token(self, auth_code: str) -> str:
        """Exchange authorization code for access token."""
        try:
            # Prepare token request data
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': self.redirect_uri
            }
            
            # Make token request
            response = requests.post(
                self.token_url,
                data=token_data,
                headers={'Accept': 'application/json'}
            )
            
            logger.info(f"Token response status: {response.status_code}")
            logger.info(f"Token response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            token_response = response.json()
            
            logger.info(f"Token response: {token_response}")
            
            if 'access_token' not in token_response:
                raise ValueError(f"Access token not found in response: {token_response}")
            
            self.access_token = token_response['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
            
            logger.info("Successfully obtained access token")
            return self.access_token
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error during token exchange: {e}")
            logger.error(f"Response content: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise
    
    def _make_request(self, method: str, endpoint: str, 
                     data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Splitwise API."""
        if not self.access_token:
            raise ValueError("Access token is required. Please authenticate first.")
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=data)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response content: {response.text}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            raise
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user information."""
        return self._make_request('GET', 'get_current_user')
    
    def get_friends(self) -> List[Dict[str, Any]]:
        """Get list of friends."""
        response = self._make_request('GET', 'get_friends')
        return response.get('friends', [])
    
    def get_groups(self) -> List[Dict[str, Any]]:
        """Get list of groups."""
        response = self._make_request('GET', 'get_groups')
        return response.get('groups', [])
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get list of expense categories."""
        response = self._make_request('GET', 'get_categories')
        return response.get('categories', [])
    
    def find_user_by_name_or_email(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find a user by name or email from friends list."""
        friends = self.get_friends()
        
        for friend in friends:
            # Check email match
            if friend.get('email', '').lower() == identifier.lower():
                return friend
            
            # Check name match (first name, last name, or full name)
            first_name = friend.get('first_name', '').lower()
            last_name = friend.get('last_name', '').lower()
            full_name = f"{first_name} {last_name}".strip()
            
            if (first_name == identifier.lower() or 
                last_name == identifier.lower() or 
                full_name == identifier.lower()):
                return friend
        
        return None
    
    def find_category_by_name(self, category_name: str) -> Optional[int]:
        """Find category ID by name."""
        if not category_name:
            return None
        
        categories = self.get_categories()
        category_name_lower = category_name.lower()
        
        # Search in main categories and subcategories
        for category in categories:
            if category['name'].lower() == category_name_lower:
                # This is a parent category, look for "Other" subcategory
                subcategories = category.get('subcategories', [])
                for subcat in subcategories:
                    if subcat['name'].lower() == 'other':
                        return subcat['id']
            
            # Search subcategories
            subcategories = category.get('subcategories', [])
            for subcat in subcategories:
                if subcat['name'].lower() == category_name_lower:
                    return subcat['id']
        
        return None
    
    def create_expense(self, expense: SplitwiseExpense) -> SplitwiseExpenseResponse:
        """Create a new expense in Splitwise."""
        expense_data = expense.dict(exclude_none=True)
        
        # Convert users list to the format expected by Splitwise API
        if 'users' in expense_data:
            users_list = []
            for user in expense_data['users']:
                user_data = {
                    'user_id': user['user_id'],
                    'paid_share': user['paid_share'],
                    'owed_share': user['owed_share']
                }
                users_list.append(user_data)
            expense_data['users'] = users_list
        
        logger.info(f"Creating expense with data: {json.dumps(expense_data, indent=2)}")
        
        response = self._make_request('POST', 'create_expense', expense_data)
        logger.info(f"Splitwise response: {json.dumps(response, indent=2)}")
        
        # Check if response contains errors
        if 'errors' in response and response['errors']:
            raise ValueError(f"Splitwise API error: {response['errors']}")
        
        return SplitwiseExpenseResponse(**response)
    
    def get_expenses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of recent expenses."""
        params = {'limit': limit}
        response = self._make_request('GET', 'get_expenses', params)
        return response.get('expenses', [])

# Factory function for creating client instance
def create_splitwise_client(access_token: Optional[str] = None) -> SplitwiseClient:
    """Create and return a SplitwiseClient instance."""
    return SplitwiseClient(access_token=access_token) 