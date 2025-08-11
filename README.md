# QuickBooks Project Expenses Extractor

A Python application to extract project expenses from QuickBooks with a focus on specific projects and their subprojects. This tool is designed for targeted data extraction rather than bulk downloads, making it ideal for test setups and focused analysis.

## Features

- **Focused Data Extraction**: Specify a project code to retrieve expenses for that project and all its subprojects
- **Hierarchical Project Support**: Handles QuickBooks' hierarchical project structure (company root → projects → subprojects)
- **Multiple Export Formats**: Export data in CSV, Excel (XLSX), or JSON formats
- **Date Range Filtering**: Filter expenses by specific date ranges
- **Comprehensive Reporting**: Generate focused reports with project hierarchy and expense summaries
- **OAuth 2.0 Authentication**: Secure authentication with QuickBooks API
- **Command-Line Interface**: Easy-to-use CLI with flexible options

## Prerequisites

- Python 3.7 or higher
- QuickBooks Developer Account
- QuickBooks App with OAuth 2.0 credentials
- Projects enabled in your QuickBooks account

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy the environment template and configure your QuickBooks credentials:
   ```bash
   copy env_example.txt .env
   ```
4. Edit `.env` with your QuickBooks API credentials

## QuickBooks Setup

1. Go to [QuickBooks Developer Portal](https://developer.intuit.com/)
2. Create a new app or use an existing one
3. Enable OAuth 2.0 and get your Client ID and Client Secret
4. Add `http://localhost:8080/callback` to your app's redirect URIs
5. Update your `.env` file with the credentials

## Authentication

Before using the application, you need to authenticate with QuickBooks:

```bash
python auth_helper.py --authenticate
```

This will:
1. Open your browser to QuickBooks authorization page
2. Start a local server to capture the callback
3. Exchange the authorization code for access tokens
4. Save tokens locally for future use

To test your connection:
```bash
python auth_helper.py --test
```

## Usage

### Basic Usage

The application now requires you to specify a project code to focus on:

```bash
# Get expenses for a specific project and its subprojects
python main.py --project-code "PROJ001"

# Get expenses with date range filtering
python main.py --project-code "PROJ001" --start-date "2024-01-01" --end-date "2024-12-31"

# Export in specific format
python main.py --project-code "PROJ001" --format csv

# Get only project hierarchy (no expenses)
python main.py --project-code "PROJ001" --projects-only
```

### Command Line Options

- `--project-code`: **Required** - Project code to retrieve expenses for
- `--format`: Export format - `csv`, `excel`, or `json` (default: `excel`)
- `--projects-only`: Only export project hierarchy, skip expenses
- `--start-date`: Start date for expenses (YYYY-MM-DD format)
- `--end-date`: End date for expenses (YYYY-MM-DD format)
- `--output-dir`: Output directory for exported files (default: `exports`)
- `--verbose`: Enable verbose output for debugging

### Examples

```bash
# Focus on a specific project and get all its subproject expenses
python main.py --project-code "CONSTRUCTION" --verbose

# Get expenses for a project within a specific quarter
python main.py --project-code "Q1_2024" --start-date "2024-01-01" --end-date "2024-03-31"

# Export project hierarchy only in JSON format
python main.py --project-code "MAIN_PROJECT" --projects-only --format json

# Use custom output directory
python main.py --project-code "TEST_PROJECT" --output-dir "my_exports"
```

## Output Files

The application creates focused exports in your specified output directory:

- **Project Hierarchy**: Filtered hierarchy showing only the target project and its subprojects
- **Expenses**: All expenses for the target project and subprojects
- **Comprehensive Report**: Multi-sheet Excel or structured JSON with project hierarchy and expense summaries

## Data Structure

### Project Hierarchy
- Root company project
- Main projects (level 1)
- Subprojects (level 2+)
- Project metadata (ID, Name, Code, Status, etc.)

### Expenses
- Transaction details (ID, Date, Amount, Description)
- Project references
- Vendor information
- Account details
- Line item breakdowns

## Configuration

Key configuration options in `config.py`:

- API endpoints (sandbox vs production)
- OAuth scopes
- Export settings
- Token management

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Run `python auth_helper.py --authenticate` to refresh tokens
2. **Project Not Found**: Use `--verbose` to see available project codes
3. **No Expenses**: Check date ranges and project assignments in QuickBooks
4. **API Limits**: QuickBooks has rate limits; the app handles basic throttling

### Debug Mode

Use `--verbose` flag for detailed output:
```bash
python main.py --project-code "PROJ001" --verbose
```

## Development

### Project Structure

```
├── main.py                 # Main application entry point
├── quickbooks_client.py    # QuickBooks API client
├── data_exporter.py        # Data export functionality
├── config.py              # Configuration settings
├── auth_helper.py         # OAuth authentication helper
├── test_setup.py          # Setup verification script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Testing Setup

Verify your environment:
```bash
python test_setup.py
```

### Adding New Export Formats

Extend the `DataExporter` class in `data_exporter.py` to add new export formats.

## API Limits and Considerations

- QuickBooks API has rate limits (100 requests per minute for most endpoints)
- Large datasets may require pagination handling
- Token refresh is handled automatically
- Sandbox environment has different limits than production

## Security Notes

- Never commit your `.env` file with real credentials
- Access tokens expire and are automatically refreshed
- Use environment variables for sensitive configuration
- Local token storage is for development convenience

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with QuickBooks API terms of service and your organization's data policies. 