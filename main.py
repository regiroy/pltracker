#!/usr/bin/env python3
"""
QuickBooks Project Expenses Extractor
A Python application to pull down all expenses of projects from QuickBooks.
"""

import argparse
import sys
import os
from quickbooks_client import QuickBooksClient
from data_exporter import DataExporter

def main():
    parser = argparse.ArgumentParser(
        description='Extract project expenses from QuickBooks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get expenses for a specific project and its subprojects
  python main.py --project-code "PROJ001"
  
  # Get expenses for a specific project with date range
  python main.py --project-code "PROJ001" --start-date "2024-01-01" --end-date "2024-12-31"
  
  # Export in specific format
  python main.py --project-code "PROJ001" --format csv
  
  # Get only project hierarchy (no expenses)
  python main.py --project-code "PROJ001" --projects-only
        """
    )
    
    parser.add_argument(
        '--project-code', 
        required=True,
        help='Project code to retrieve expenses for (required)'
    )
    parser.add_argument(
        '--format', 
        choices=['csv', 'excel', 'json'], 
        default='excel',
        help='Export format (default: excel)'
    )
    parser.add_argument(
        '--projects-only', 
        action='store_true',
        help='Only export project hierarchy, skip expenses'
    )
    parser.add_argument(
        '--start-date', 
        help='Start date for expenses (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--end-date', 
        help='End date for expenses (YYYY-MM-DD format)'
    )
    parser.add_argument(
        '--output-dir', 
        default='exports',
        help='Output directory for exported files (default: exports)'
    )
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate date format if provided
    if args.start_date and not _is_valid_date(args.start_date):
        print(f"Error: Invalid start date format '{args.start_date}'. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    if args.end_date and not _is_valid_date(args.end_date):
        print(f"Error: Invalid end date format '{args.end_date}'. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    if args.verbose:
        print(f"Starting QuickBooks data extraction for project: {args.project_code}")
        if args.start_date:
            print(f"Date range: {args.start_date} to {args.end_date or 'present'}")
        print(f"Export format: {args.format}")
        print(f"Output directory: {args.output_dir}")
    
    # Initialize QuickBooks client
    client = QuickBooksClient()
    if not client.access_token or not client.realm_id:
        print("Error: Not authenticated with QuickBooks.")
        print("Please run 'python auth_helper.py --authenticate' first.")
        sys.exit(1)
    
    # Initialize exporter
    exporter = DataExporter(output_dir=args.output_dir)
    
    try:
        # First, get the project hierarchy to find the target project and its subprojects
        if args.verbose:
            print("Fetching project hierarchy...")
        
        hierarchy = client.get_project_hierarchy()
        
        # Find the target project and its subprojects
        target_project = _find_project_by_code(hierarchy, args.project_code)
        if not target_project:
            print(f"Error: Project with code '{args.project_code}' not found.")
            print("Available project codes:")
            _print_available_project_codes(hierarchy)
            sys.exit(1)
        
        if args.verbose:
            print(f"Found project: {target_project['Name']} (ID: {target_project['Id']})")
        
        # Get all subproject IDs (including the target project itself)
        project_ids = _get_project_and_subproject_ids(hierarchy, target_project['Id'])
        
        if args.verbose:
            print(f"Retrieving data for {len(project_ids)} projects (including subprojects)")
        
        # Export project hierarchy for the target project and its subprojects
        if not args.projects_only:
            if args.verbose:
                print("Exporting project hierarchy...")
            
            # Filter hierarchy to only include target project and subprojects
            filtered_hierarchy = _filter_hierarchy_for_projects(hierarchy, project_ids)
            exporter.export_project_hierarchy(filtered_hierarchy, args.format)
        
        # Get and export expenses for the target project and its subprojects
        if not args.projects_only:
            if args.verbose:
                print("Fetching expenses for target project and subprojects...")
            
            all_expenses = []
            for project_id in project_ids:
                expenses = client.get_expenses(
                    project_id=project_id,
                    start_date=args.start_date,
                    end_date=args.end_date
                )
                all_expenses.extend(expenses)
                
                if args.verbose:
                    print(f"  Found {len(expenses)} expenses for project ID {project_id}")
            
            if all_expenses:
                if args.verbose:
                    print(f"Exporting {len(all_expenses)} total expenses...")
                exporter.export_expenses(all_expenses, args.format)
            else:
                print("No expenses found for the specified project and subprojects.")
        
        # Create a focused summary report
        if not args.projects_only and all_expenses:
            if args.verbose:
                print("Creating focused summary report...")
            
            # Get expenses summary for the specific projects
            expenses_summary = client.get_project_expenses_summary(project_ids=project_ids)
            exporter.export_comprehensive_report(filtered_hierarchy, expenses_summary, args.format)
        
        print(f"\n✅ Data extraction completed successfully!")
        print(f"📁 Files exported to: {args.output_dir}/")
        print(f"🎯 Focused on project: {target_project['Name']} ({args.project_code})")
        if not args.projects_only:
            print(f"💰 Total expenses found: {len(all_expenses)}")
        
    except Exception as e:
        print(f"Error during data extraction: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def _is_valid_date(date_string):
    """Validate date format YYYY-MM-DD"""
    import re
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_string):
        return False
    
    try:
        from datetime import datetime
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def _find_project_by_code(hierarchy, project_code):
    """Find a project by its code in the hierarchy"""
    def search_recursive(node):
        if node.get('ProjectCode') == project_code:
            return node
        for child in node.get('children', []):
            result = search_recursive(child)
            if result:
                return result
        return None
    
    return search_recursive(hierarchy)

def _get_project_and_subproject_ids(hierarchy, project_id):
    """Get all project IDs including the target project and all its subprojects"""
    def find_project_node(node, target_id):
        if node.get('Id') == target_id:
            return node
        for child in node.get('children', []):
            result = find_project_node(child, target_id)
            if result:
                return result
        return None
    
    def collect_project_ids(node, project_ids):
        project_ids.append(node.get('Id'))
        for child in node.get('children', []):
            collect_project_ids(child, project_ids)
    
    target_node = find_project_node(hierarchy, project_id)
    if not target_node:
        return [project_id]  # Fallback to just the target ID
    
    project_ids = []
    collect_project_ids(target_node, project_ids)
    return project_ids

def _filter_hierarchy_for_projects(hierarchy, project_ids):
    """Filter hierarchy to only include specified project IDs and their relationships"""
    def filter_recursive(node):
        if node.get('Id') in project_ids:
            filtered_node = node.copy()
            filtered_node['children'] = [
                filter_recursive(child) for child in node.get('children', [])
                if child.get('Id') in project_ids
            ]
            return filtered_node
        
        # If this node is not in project_ids, check if any of its children are
        # This handles the case where we're filtering from a root hierarchy
        filtered_children = []
        for child in node.get('children', []):
            filtered_child = filter_recursive(child)
            if filtered_child is not None:
                filtered_children.append(filtered_child)
        
        if filtered_children:
            # Return a copy of the node with only the filtered children
            filtered_node = node.copy()
            filtered_node['children'] = filtered_children
            return filtered_node
        
        return None
    
    return filter_recursive(hierarchy)

def _print_available_project_codes(hierarchy):
    """Print available project codes for user reference"""
    def print_codes_recursive(node, indent=""):
        if node.get('ProjectCode'):
            print(f"{indent}{node['ProjectCode']}: {node['Name']}")
        for child in node.get('children', []):
            print_codes_recursive(child, indent + "  ")
    
    print_codes_recursive(hierarchy)

if __name__ == '__main__':
    main() 