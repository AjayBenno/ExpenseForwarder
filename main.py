"""Main module for expense forwarder application."""

import logging
import sys
import argparse
from typing import Optional

from config import config
from models import EmailContent
from email_parser import create_email_parser
from splitwise_client import create_splitwise_client
from expense_converter import create_expense_converter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('expense_forwarder.log')
    ]
)

logger = logging.getLogger(__name__)

class ExpenseForwarder:
    """Main application class for forwarding email expenses to Splitwise."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize the expense forwarder."""
        
        # Validate configuration
        if not config.validate():
            raise ValueError("Configuration validation failed. Please check your environment variables.")
        
        # Initialize components
        self.email_parser = create_email_parser()
        self.splitwise_client = create_splitwise_client(access_token)
        
        # Initialize converter if access token is provided
        if access_token:
            try:
                self.expense_converter = create_expense_converter(self.splitwise_client)
                logger.info("Initialized expense converter with provided access token")
            except Exception as e:
                logger.warning(f"Failed to initialize expense converter with provided token: {e}")
                self.expense_converter = None
        else:
            self.expense_converter = None
    
    def authenticate_splitwise(self) -> str:
        """Authenticate with Splitwise and return access token."""
        logger.info("Starting Splitwise OAuth authentication...")
        
        try:
            access_token = self.splitwise_client.authorize_interactive()
            logger.info("Successfully authenticated with Splitwise")
            
            # Initialize the expense converter now that we have authentication
            self.expense_converter = create_expense_converter(self.splitwise_client)
            
            return access_token
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def process_email(self, subject: str, body: str, group_id: int) -> dict:
        """Process email content and create Splitwise expense."""
        
        if not self.expense_converter:
            raise ValueError("Not authenticated with Splitwise. Please authenticate first.")
        
        logger.info(f"Processing email: {subject[:50]}...")
        
        try:
            # Create email content model
            email_content = EmailContent(subject=subject, body=body)
            
            # Parse email using OpenAI
            logger.info("Parsing email with OpenAI...")
            openai_response = self.email_parser.parse_email(email_content)
            
            logger.info(f"OpenAI parsing confidence: {openai_response.confidence:.2f}")
            
            # Convert to Splitwise expense
            logger.info("Converting to Splitwise expense...")
            splitwise_expense = self.expense_converter.convert_to_splitwise_expense(
                openai_response.parsed_expense,
                group_id
            )
            
            # Create expense in Splitwise
            logger.info("Creating expense in Splitwise...")
            response = self.splitwise_client.create_expense(splitwise_expense)
            
            logger.info(f"Successfully created expense: {response.expense.get('id')}")
            
            return {
                'success': True,
                'expense_id': response.expense.get('id'),
                'description': splitwise_expense.description,
                'amount': splitwise_expense.cost,
                'currency': splitwise_expense.currency_code,
                'confidence': openai_response.confidence,
                'notes': openai_response.notes
            }
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return {
                'success': False,
                'error': str(e),
                'description': subject[:100] if subject else 'Unknown'
            }
    
    def get_user_info(self) -> dict:
        """Get current user information."""
        if not self.splitwise_client.access_token:
            raise ValueError("Not authenticated with Splitwise")
        
        try:
            return self.splitwise_client.get_current_user()
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            raise
    
    def list_friends(self) -> list:
        """List user's friends."""
        if not self.splitwise_client.access_token:
            raise ValueError("Not authenticated with Splitwise")
        
        try:
            return self.splitwise_client.get_friends()
        except Exception as e:
            logger.error(f"Error listing friends: {e}")
            raise
    
    def list_groups(self) -> list:
        """List user's groups."""
        if not self.splitwise_client.access_token:
            raise ValueError("Not authenticated with Splitwise")
        
        try:
            return self.splitwise_client.get_groups()
        except Exception as e:
            logger.error(f"Error listing groups: {e}")
            raise

def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(description='Forward email expenses to Splitwise')
    parser.add_argument('--subject', help='Email subject')
    parser.add_argument('--body', help='Email body')
    parser.add_argument('--group-id', type=int, help='Splitwise group ID (required for expense creation)')
    parser.add_argument('--access-token', help='Splitwise access token (optional)')
    parser.add_argument('--auth-only', action='store_true', 
                       help='Only perform authentication and exit')
    parser.add_argument('--user-info', action='store_true',
                       help='Display user information and exit')
    parser.add_argument('--list-friends', action='store_true',
                       help='List friends and exit')
    parser.add_argument('--list-groups', action='store_true',
                       help='List groups and exit')
    
    args = parser.parse_args()
    
    # Check if subject, body, and group_id are required (not for info commands)
    info_commands = [args.auth_only, args.user_info, args.list_friends, args.list_groups]
    if not any(info_commands):
        if not args.subject or not args.body:
            parser.error("--subject and --body are required unless using info commands (--auth-only, --user-info, --list-friends, --list-groups)")
        if not args.group_id:
            parser.error("--group-id is required for expense creation")
    
    try:
        # Initialize forwarder
        forwarder = ExpenseForwarder(access_token=args.access_token)
        
        # Authenticate if no token provided
        if not args.access_token:
            access_token = forwarder.authenticate_splitwise()
            print(f"\nAccess token: {access_token}")
            
            if args.auth_only:
                print("Authentication completed successfully!")
                return
        
        # Handle info commands
        if args.user_info:
            user_info = forwarder.get_user_info()
            print(f"\nUser: {user_info['user']['first_name']} {user_info['user']['last_name']}")
            print(f"Email: {user_info['user']['email']}")
            return
        
        if args.list_friends:
            friends = forwarder.list_friends()
            print(f"\nFriends ({len(friends)}):")
            for friend in friends:
                print(f"  - {friend['first_name']} {friend['last_name']} ({friend['email']})")
            return
        
        if args.list_groups:
            groups = forwarder.list_groups()
            print(f"\nGroups ({len(groups)}):")
            for group in groups:
                print(f"  - {group['name']} (ID: {group['id']})")
            return
        
        # Process email
        result = forwarder.process_email(
            subject=args.subject,
            body=args.body,
            group_id=args.group_id
        )
        
        if result['success']:
            print(f"\n✅ Successfully created expense!")
            print(f"Description: {result['description']}")
            print(f"Amount: {result['currency']} {result['amount']}")
            print(f"Expense ID: {result['expense_id']}")
            print(f"Confidence: {result['confidence']:.2f}")
            if result['notes']:
                print(f"Notes: {result['notes']}")
        else:
            print(f"\n❌ Failed to create expense:")
            print(f"Error: {result['error']}")
            print(f"Description: {result['description']}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 