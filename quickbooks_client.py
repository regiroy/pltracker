import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from config import QuickBooksConfig

class QuickBooksClient:
    """Client for interacting with QuickBooks API to fetch projects and expenses"""
    
    def __init__(self):
        self.config = QuickBooksConfig()
        self.access_token = None
        self.refresh_token = None
        self.realm_id = None
        self.base_url = self.config.API_BASE_URL
        
        # Load existing tokens if available
        self._load_tokens()
    
    def _load_tokens(self):
        """Load existing access and refresh tokens from file"""
        if os.path.exists(self.config.TOKEN_FILE):
            try:
                with open(self.config.TOKEN_FILE, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get('access_token')
                    self.refresh_token = tokens.get('refresh_token')
                    self.realm_id = tokens.get('realm_id')
            except Exception as e:
                print(f"Error loading tokens: {e}")
    
    def _save_tokens(self):
        """Save current tokens to file"""
        tokens = {
            'access_token': self.access_token,
            'refresh_token': self.refresh_token,
            'realm_id': self.realm_id,
            'timestamp': datetime.now().isoformat()
        }
        
        os.makedirs(os.path.dirname(self.config.TOKEN_FILE), exist_ok=True)
        with open(self.config.TOKEN_FILE, 'w') as f:
            json.dump(tokens, f, indent=2)
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Dict:
        """Make HTTP request to QuickBooks API"""
        if not self.access_token or not self.realm_id:
            raise Exception("Not authenticated. Please authenticate first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}/v3/company/{self.realm_id}/{endpoint}"
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            if response.status_code == 401:
                # Token expired, try to refresh
                if self.refresh_token:
                    self._refresh_access_token()
                    return self._make_request(endpoint, method, params, data)
            raise
    
    def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise Exception("No refresh token available")
        
        # This would typically involve calling QuickBooks OAuth endpoint
        # For now, we'll just raise an exception to indicate re-authentication is needed
        raise Exception("Access token expired. Please re-authenticate.")
    
    def get_projects(self, max_results: int = 1000) -> List[Dict]:
        """Fetch all projects from QuickBooks"""
        projects = []
        start_position = 1
        
        while True:
            params = {
                'query': 'SELECT * FROM Project ORDER BY Name',
                'start_position': start_position,
                'max_results': min(max_results, 1000)
            }
            
            try:
                response = self._make_request('query', params=params)
                
                if 'QueryResponse' in response and 'Project' in response['QueryResponse']:
                    batch = response['QueryResponse']['Project']
                    projects.extend(batch)
                    
                    # Check if we've reached the end
                    if len(batch) < max_results:
                        break
                    
                    start_position += len(batch)
                else:
                    break
                    
            except Exception as e:
                print(f"Error fetching projects: {e}")
                break
        
        return projects
    
    def get_expenses(self, project_id: str = None, start_date: str = None, end_date: str = None, max_results: int = 1000) -> List[Dict]:
        """Fetch expenses from QuickBooks, optionally filtered by project and date range"""
        expenses = []
        start_position = 1
        
        # Build query based on filters
        query = "SELECT * FROM Purchase"
        
        if project_id:
            query += f" WHERE ProjectRef = '{project_id}'"
        
        if start_date or end_date:
            if 'WHERE' in query:
                query += " AND"
            else:
                query += " WHERE"
            
            if start_date and end_date:
                query += f" TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
            elif start_date:
                query += f" TxnDate >= '{start_date}'"
            elif end_date:
                query += f" TxnDate <= '{end_date}'"
        
        query += " ORDER BY TxnDate DESC"
        
        while True:
            params = {
                'query': query,
                'start_position': start_position,
                'max_results': min(max_results, 1000)
            }
            
            try:
                response = self._make_request('query', params=params)
                
                if 'QueryResponse' in response and 'Purchase' in response['QueryResponse']:
                    batch = response['QueryResponse']['Purchase']
                    expenses.extend(batch)
                    
                    # Check if we've reached the end
                    if len(batch) < max_results:
                        break
                    
                    start_position += len(batch)
                else:
                    break
                    
            except Exception as e:
                print(f"Error fetching expenses: {e}")
                break
        
        return expenses
    
    def get_project_hierarchy(self) -> Dict:
        """Build a hierarchical structure of projects"""
        projects = self.get_projects()
        hierarchy = {}
        
        # First pass: create project lookup
        project_lookup = {}
        for project in projects:
            project_id = project.get('Id')
            if project_id:
                project_lookup[project_id] = {
                    'id': project_id,
                    'name': project.get('Name', ''),
                    'description': project.get('Description', ''),
                    'parent_ref': project.get('ParentRef', {}).get('value') if project.get('ParentRef') else None,
                    'children': [],
                    'expenses': []
                }
        
        # Second pass: build hierarchy
        root_projects = []
        for project_id, project_data in project_lookup.items():
            parent_id = project_data['parent_ref']
            
            if parent_id and parent_id in project_lookup:
                # This is a child project
                project_lookup[parent_id]['children'].append(project_data)
            else:
                # This is a root project
                root_projects.append(project_data)
        
        hierarchy['root_projects'] = root_projects
        hierarchy['all_projects'] = project_lookup
        
        return hierarchy
    
    def get_project_expenses_summary(self, project_id: str = None, project_ids: List[str] = None) -> Dict:
        """
        Get expenses summary for projects
        
        Args:
            project_id: Specific project ID to get summary for
            project_ids: List of project IDs to get summary for (including subprojects)
        
        Returns:
            Dictionary with project expenses summary
        """
        if project_ids:
            # Get expenses for specific project IDs
            all_expenses = []
            for pid in project_ids:
                expenses = self.get_expenses(project_id=pid)
                all_expenses.extend(expenses)
            
            # Group expenses by project
            project_expenses = {}
            for expense in all_expenses:
                project_ref = expense.get('ProjectRef', {})
                project_id = project_ref.get('value')
                project_name = project_ref.get('name', 'Unknown Project')
                
                if project_id not in project_expenses:
                    project_expenses[project_id] = {
                        'project_name': project_name,
                        'expense_count': 0,
                        'total_amount': 0.0,
                        'expenses': []
                    }
                
                amount = float(expense.get('TotalAmt', 0))
                project_expenses[project_id]['expense_count'] += 1
                project_expenses[project_id]['total_amount'] += amount
                project_expenses[project_id]['expenses'].append(expense)
            
            return project_expenses
        
        elif project_id:
            # Get expenses for specific project
            expenses = self.get_expenses(project_id=project_id)
            
            if not expenses:
                return {}
            
            total_amount = sum(float(expense.get('TotalAmt', 0)) for expense in expenses)
            
            return {
                project_id: {
                    'project_name': expenses[0].get('ProjectRef', {}).get('name', 'Unknown Project'),
                    'expense_count': len(expenses),
                    'total_amount': total_amount,
                    'expenses': expenses
                }
            }
        else:
            # Get expenses for all projects (original behavior)
            expenses = self.get_expenses()
            
            if not expenses:
                return {}
            
            # Group expenses by project
            project_expenses = {}
            for expense in expenses:
                project_ref = expense.get('ProjectRef', {})
                project_id = project_ref.get('value')
                project_name = project_ref.get('name', 'Unknown Project')
                
                if project_id not in project_expenses:
                    project_expenses[project_id] = {
                        'project_name': project_name,
                        'expense_count': 0,
                        'total_amount': 0.0,
                        'expenses': []
                    }
                
                amount = float(expense.get('TotalAmt', 0))
                project_expenses[project_id]['expense_count'] += 1
                project_expenses[project_id]['total_amount'] += amount
                project_expenses[project_id]['expenses'].append(expense)
            
            return project_expenses
    
 