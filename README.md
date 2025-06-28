# Expense Forwarder

A Python application that automatically parses email content to extract expense information and creates expenses in Splitwise using OpenAI and the Splitwise API.

## Features

- **Email Parsing**: Uses OpenAI GPT-4 to intelligently extract expense information from email content
- **Splitwise Integration**: Automatically creates expenses in Splitwise with proper participant assignment
- **OAuth Authentication**: Secure OAuth2 flow for Splitwise API access
- **Participant Resolution**: Automatically matches participant names/emails to Splitwise friends
- **Category Detection**: Intelligent expense category assignment
- **Validation**: Comprehensive validation of parsed data and expense creation
- **Command Line Interface**: Easy-to-use CLI for processing individual emails
- **Programmatic API**: Clean Python API for integration into other applications

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd expenseforwarder
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
cp config.example.env .env
# Edit .env with your API keys and configuration
```

## Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4

# Splitwise Configuration
SPLITWISE_CLIENT_ID=your_splitwise_client_id_here
SPLITWISE_CLIENT_SECRET=your_splitwise_client_secret_here
SPLITWISE_REDIRECT_URI=http://localhost:8080/callback

# Default Settings
DEFAULT_CURRENCY=USD
DEFAULT_GROUP_ID=your_default_group_id_here
```

### Getting API Keys

#### OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section and create a new key

#### Splitwise API Credentials

1. Visit [Splitwise Developers](https://secure.splitwise.com/apps)
2. Register a new application
3. Use `http://localhost:8080/callback` as the redirect URI
4. Copy the Client ID and Client Secret

## Usage

### Command Line Interface

#### Basic Usage

```bash
python main.py --subject "Dinner Receipt" --body "Pizza dinner $45.67 split between John and Sarah"
```

#### With Group ID

```bash
python main.py --subject "Uber Receipt" --body "Uber ride $28.50" --group-id 12345
```

#### Authentication Only

```bash
python main.py --auth-only --subject "" --body ""
```

#### List Information

```bash
# List friends
python main.py --list-friends --subject "" --body ""

# List groups
python main.py --list-groups --subject "" --body ""

# Get user info
python main.py --user-info --subject "" --body ""
```

### Programmatic Usage

```python
from main import ExpenseForwarder

# Initialize and authenticate
forwarder = ExpenseForwarder()
access_token = forwarder.authenticate_splitwise()

# Process an email
result = forwarder.process_email(
    subject="Dinner Receipt - Pizza Palace",
    body="Total: $45.67. Split between me, John, and Sarah.",
    group_id=12345,
    min_confidence=0.6
)

if result['success']:
    print(f"Created expense: {result['expense_id']}")
else:
    print(f"Error: {result['error']}")
```

## Architecture

The application is built with a modular architecture:

### Core Modules

- **`config.py`**: Configuration management and environment variables
- **`models.py`**: Pydantic data models for type safety and validation
- **`email_parser.py`**: OpenAI integration for parsing email content
- **`splitwise_client.py`**: Splitwise API client with OAuth authentication
- **`expense_converter.py`**: Converts parsed data to Splitwise expense format
- **`main.py`**: Main application orchestration and CLI

### Data Flow

1. **Email Input**: Email subject and body provided via CLI or API
2. **OpenAI Parsing**: Email content sent to OpenAI for expense extraction
3. **Data Validation**: Parsed data validated for completeness and confidence
4. **Participant Resolution**: Names/emails matched to Splitwise friends
5. **Expense Creation**: Splitwise expense object created and validated
6. **API Submission**: Expense submitted to Splitwise via authenticated API

## Examples

### Email Formats Supported

The application can parse various email formats:

#### Restaurant Receipt

```
Subject: Dinner at Italian Bistro
Body: Had dinner with the team. Total came to $125.40.
      Split between me, Alice, Bob, and Carol.
```

#### Uber/Transportation

```
Subject: Uber Receipt
Body: Uber ride from downtown to airport. $34.50 total.
      Shared with Sarah and Mike.
```

#### General Expenses

```
Subject: Office Supplies
Body: Bought supplies for the office: $67.89
      Please split with team members.
```

### Output Example

```json
{
  "success": true,
  "expense_id": 123456789,
  "description": "Dinner at Italian Bistro",
  "amount": "125.40",
  "currency": "USD",
  "confidence": 0.95,
  "notes": "Successfully identified 4 participants",
  "splitwise_response": {
    "id": 123456789,
    "cost": "125.40",
    "description": "Dinner at Italian Bistro",
    "date": "2024-01-15T00:00:00Z",
    "users": [...]
  }
}
```

## Error Handling

The application includes comprehensive error handling:

- **Configuration Validation**: Ensures all required environment variables are set
- **Authentication Errors**: Clear messages for OAuth flow issues
- **Parsing Confidence**: Configurable minimum confidence threshold
- **API Errors**: Detailed logging of Splitwise API responses
- **Validation Errors**: Expense validation before submission

## Logging

Logs are written to both console and `expense_forwarder.log`:

```
2024-01-15 10:30:00 - main - INFO - Processing email: Dinner Receipt...
2024-01-15 10:30:01 - email_parser - INFO - OpenAI parsing confidence: 0.95
2024-01-15 10:30:02 - expense_converter - INFO - Resolved participant 'John' to user John Doe
2024-01-15 10:30:03 - splitwise_client - INFO - Successfully created expense: 123456789
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security Considerations

- API keys are stored in environment variables only
- OAuth tokens can be reused to avoid repeated authentication
- All HTTP requests use HTTPS
- Input validation prevents injection attacks
- Minimal required OAuth scopes

## Limitations

- Requires OpenAI API access (paid service)
- Splitwise API rate limits apply
- Participants must be existing Splitwise friends
- Currently supports equal splits primarily
- Email parsing accuracy depends on content clarity

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:

1. Check the logs in `expense_forwarder.log`
2. Verify your environment configuration
3. Test authentication separately using `--auth-only`
4. Review the OpenAI parsing confidence scores

## Roadmap

- [ ] Support for exact amount splits
- [ ] Email integration (IMAP/webhook)
- [ ] Web interface
- [ ] Batch processing
- [ ] Receipt image processing
- [ ] Custom parsing rules
- [ ] Multiple currency support
