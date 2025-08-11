import os
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from config import QuickBooksConfig

class DataExporter:
    """Class for exporting QuickBooks project and expense data in various formats"""
    
    def __init__(self):
        self.config = QuickBooksConfig()
        self.output_dir = self.config.OUTPUT_DIR
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_projects(self, projects: List[Dict], format: str = None) -> str:
        """Export projects data to specified format"""
        if not format:
            format = self.config.DEFAULT_EXPORT_FORMAT
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"projects_{timestamp}"
        
        if format.lower() == 'csv':
            return self._export_projects_csv(projects, filename)
        elif format.lower() == 'excel':
            return self._export_projects_excel(projects, filename)
        elif format.lower() == 'json':
            return self._export_projects_json(projects, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_expenses(self, expenses: List[Dict], format: str = None) -> str:
        """Export expenses data to specified format"""
        if not format:
            format = self.config.DEFAULT_EXPORT_FORMAT
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"expenses_{timestamp}"
        
        if format.lower() == 'csv':
            return self._export_expenses_csv(expenses, filename)
        elif format.lower() == 'excel':
            return self._export_expenses_excel(expenses, filename)
        elif format.lower() == 'json':
            return self._export_expenses_json(expenses, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_project_hierarchy(self, hierarchy: Dict, format: str = None) -> str:
        """Export project hierarchy data to specified format"""
        if not format:
            format = self.config.DEFAULT_EXPORT_FORMAT
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_hierarchy_{timestamp}"
        
        if format.lower() == 'csv':
            return self._export_hierarchy_csv(hierarchy, filename)
        elif format.lower() == 'excel':
            return self._export_hierarchy_excel(hierarchy, filename)
        elif format.lower() == 'json':
            return self._export_hierarchy_json(hierarchy, filename)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def export_comprehensive_report(self, hierarchy: Dict, expenses_summary: Dict, format: str = None) -> str:
        """Export a comprehensive report with projects and expenses"""
        if not format:
            format = self.config.DEFAULT_EXPORT_FORMAT
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_report_{timestamp}"
        
        if format.lower() == 'excel':
            return self._export_comprehensive_excel(hierarchy, expenses_summary, filename)
        elif format.lower() == 'json':
            return self._export_comprehensive_json(hierarchy, expenses_summary, filename)
        else:
            raise ValueError(f"Comprehensive report only supports Excel and JSON formats")
    
    def _export_projects_csv(self, projects: List[Dict], filename: str) -> str:
        """Export projects to CSV format"""
        # Flatten project data for CSV
        flattened_data = []
        for project in projects:
            flattened_data.append({
                'ID': project.get('Id', ''),
                'Name': project.get('Name', ''),
                'Description': project.get('Description', ''),
                'Parent_Project_ID': project.get('ParentRef', {}).get('value', ''),
                'Parent_Project_Name': project.get('ParentRef', {}).get('name', ''),
                'Active': project.get('Active', ''),
                'Created_Date': project.get('MetaData', {}).get('CreateTime', ''),
                'Last_Modified': project.get('MetaData', {}).get('LastUpdatedTime', '')
            })
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False)
        return filepath
    
    def _export_projects_excel(self, projects: List[Dict], filename: str) -> str:
        """Export projects to Excel format"""
        # Flatten project data for Excel
        flattened_data = []
        for project in projects:
            flattened_data.append({
                'ID': project.get('Id', ''),
                'Name': project.get('Name', ''),
                'Description': project.get('Description', ''),
                'Parent_Project_ID': project.get('ParentRef', {}).get('value', ''),
                'Parent_Project_Name': project.get('ParentRef', {}).get('name', ''),
                'Active': project.get('Active', ''),
                'Created_Date': project.get('MetaData', {}).get('CreateTime', ''),
                'Last_Modified': project.get('MetaData', {}).get('LastUpdatedTime', '')
            })
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Projects', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Projects']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def _export_projects_json(self, projects: List[Dict], filename: str) -> str:
        """Export projects to JSON format"""
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        with open(filepath, 'w') as f:
            json.dump(projects, f, indent=2, default=str)
        return filepath
    
    def _export_expenses_csv(self, expenses: List[Dict], filename: str) -> str:
        """Export expenses to CSV format"""
        # Flatten expense data for CSV
        flattened_data = []
        for expense in expenses:
            # Handle multiple line items
            lines = expense.get('Line', [{}])
            for line in lines:
                flattened_data.append({
                    'Expense_ID': expense.get('Id', ''),
                    'Date': expense.get('TxnDate', ''),
                    'Vendor_ID': expense.get('VendorRef', {}).get('value', ''),
                    'Vendor_Name': expense.get('VendorRef', {}).get('name', ''),
                    'Description': line.get('Description', ''),
                    'Amount': line.get('Amount', 0),
                    'Account_ID': line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get('value', ''),
                    'Account_Name': line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get('name', ''),
                    'Project_ID': expense.get('ProjectRef', {}).get('value', ''),
                    'Project_Name': expense.get('ProjectRef', {}).get('name', ''),
                    'Total_Amount': expense.get('TotalAmt', 0),
                    'Created_Date': expense.get('MetaData', {}).get('CreateTime', ''),
                    'Last_Modified': expense.get('MetaData', {}).get('LastUpdatedTime', '')
                })
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False)
        return filepath
    
    def _export_expenses_excel(self, expenses: List[Dict], filename: str) -> str:
        """Export expenses to Excel format"""
        # Flatten expense data for Excel
        flattened_data = []
        for expense in expenses:
            # Handle multiple line items
            lines = expense.get('Line', [{}])
            for line in lines:
                flattened_data.append({
                    'Expense_ID': expense.get('Id', ''),
                    'Date': expense.get('TxnDate', ''),
                    'Vendor_ID': expense.get('VendorRef', {}).get('value', ''),
                    'Vendor_Name': expense.get('VendorRef', {}).get('name', ''),
                    'Description': line.get('Description', ''),
                    'Amount': line.get('Amount', 0),
                    'Account_ID': line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get('value', ''),
                    'Account_Name': line.get('AccountBasedExpenseLineDetail', {}).get('AccountRef', {}).get('name', ''),
                    'Project_ID': expense.get('ProjectRef', {}).get('value', ''),
                    'Project_Name': expense.get('ProjectRef', {}).get('name', ''),
                    'Total_Amount': expense.get('TotalAmt', 0),
                    'Created_Date': expense.get('MetaData', {}).get('CreateTime', ''),
                    'Last_Modified': expense.get('MetaData', {}).get('LastUpdatedTime', '')
                })
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Expenses', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Expenses']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def _export_expenses_json(self, expenses: List[Dict], filename: str) -> str:
        """Export expenses to JSON format"""
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        with open(filepath, 'w') as f:
            json.dump(expenses, f, indent=2, default=str)
        return filepath
    
    def _export_hierarchy_csv(self, hierarchy: Dict, filename: str) -> str:
        """Export project hierarchy to CSV format"""
        # Flatten hierarchy for CSV
        flattened_data = []
        
        def flatten_project(project, level=0, parent_path=""):
            current_path = f"{parent_path}/{project['name']}" if parent_path else project['name']
            
            flattened_data.append({
                'Level': level,
                'Project_ID': project['id'],
                'Project_Name': project['name'],
                'Description': project['description'],
                'Parent_Project_ID': project['parent_ref'],
                'Full_Path': current_path,
                'Child_Count': len(project['children'])
            })
            
            # Process children
            for child in project['children']:
                flatten_project(child, level + 1, current_path)
        
        # Process root projects
        for root_project in hierarchy['root_projects']:
            flatten_project(root_project)
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.csv")
        df.to_csv(filepath, index=False)
        return filepath
    
    def _export_hierarchy_excel(self, hierarchy: Dict, filename: str) -> str:
        """Export project hierarchy to Excel format"""
        # Flatten hierarchy for Excel
        flattened_data = []
        
        def flatten_project(project, level=0, parent_path=""):
            current_path = f"{parent_path}/{project['name']}" if parent_path else project['name']
            
            flattened_data.append({
                'Level': level,
                'Project_ID': project['id'],
                'Project_Name': project['name'],
                'Description': project['description'],
                'Parent_Project_ID': project['parent_ref'],
                'Full_Path': current_path,
                'Child_Count': len(project['children'])
            })
            
            # Process children
            for child in project['children']:
                flatten_project(child, level + 1, current_path)
        
        # Process root projects
        for root_project in hierarchy['root_projects']:
            flatten_project(root_project)
        
        df = pd.DataFrame(flattened_data)
        filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Project_Hierarchy', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Project_Hierarchy']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def _export_hierarchy_json(self, hierarchy: Dict, filename: str) -> str:
        """Export project hierarchy to JSON format"""
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        with open(filepath, 'w') as f:
            json.dump(hierarchy, f, indent=2, default=str)
        return filepath
    
    def _export_comprehensive_excel(self, hierarchy: Dict, expenses_summary: Dict, filename: str) -> str:
        """Export comprehensive report to Excel with multiple sheets"""
        filepath = os.path.join(self.output_dir, f"{filename}.xlsx")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Project Hierarchy
            hierarchy_data = []
            def flatten_project(project, level=0, parent_path=""):
                current_path = f"{parent_path}/{project['name']}" if parent_path else project['name']
                
                hierarchy_data.append({
                    'Level': level,
                    'Project_ID': project['id'],
                    'Project_Name': project['name'],
                    'Description': project['description'],
                    'Parent_Project_ID': project['parent_ref'],
                    'Full_Path': current_path,
                    'Child_Count': len(project['children'])
                })
                
                for child in project['children']:
                    flatten_project(child, level + 1, current_path)
            
            for root_project in hierarchy['root_projects']:
                flatten_project(root_project)
            
            df_hierarchy = pd.DataFrame(hierarchy_data)
            df_hierarchy.to_excel(writer, sheet_name='Project_Hierarchy', index=False)
            
            # Sheet 2: Expenses Summary
            summary_data = []
            for project_id, summary in expenses_summary.items():
                summary_data.append({
                    'Project_ID': project_id,
                    'Total_Amount': summary['total_amount'],
                    'Expense_Count': summary['expense_count']
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Expenses_Summary', index=False)
            
            # Sheet 3: Detailed Expenses
            all_expenses = []
            for project_id, summary in expenses_summary.items():
                for expense in summary['expenses']:
                    expense['Project_ID'] = project_id
                    all_expenses.append(expense)
            
            df_expenses = pd.DataFrame(all_expenses)
            df_expenses.to_excel(writer, sheet_name='Detailed_Expenses', index=False)
            
            # Auto-adjust column widths for all sheets
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        
        return filepath
    
    def _export_comprehensive_json(self, hierarchy: Dict, expenses_summary: Dict, filename: str) -> str:
        """Export comprehensive report to JSON format"""
        comprehensive_data = {
            'export_timestamp': datetime.now().isoformat(),
            'project_hierarchy': hierarchy,
            'expenses_summary': expenses_summary
        }
        
        filepath = os.path.join(self.output_dir, f"{filename}.json")
        with open(filepath, 'w') as f:
            json.dump(comprehensive_data, f, indent=2, default=str)
        return filepath 