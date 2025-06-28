"""Expense converter for transforming parsed email data to Splitwise expenses."""

import logging
from models import ParsedExpense, SplitwiseExpense, SplitwiseUser
from splitwise_client import SplitwiseClient

logger = logging.getLogger(__name__)

class ExpenseConverter:
    """Converts parsed expense data to Splitwise expense format."""
    
    def __init__(self, splitwise_client: SplitwiseClient):
        """Initialize the expense converter."""
        self.splitwise_client = splitwise_client
        self.current_user = self._get_current_user()
    
    def _get_current_user(self):
        """Get current user information."""
        try:
            user_response = self.splitwise_client.get_current_user()
            current_user = user_response.get('user')
            logger.info(f"Loaded current user: {current_user.get('first_name')} {current_user.get('last_name')}")
            return current_user
        except Exception as e:
            logger.error(f"Failed to load current user: {e}")
            raise
    
    def convert_to_splitwise_expense(self, parsed_expense: ParsedExpense, group_id: int, email_summary: str = None) -> SplitwiseExpense:
        """Convert parsed expense to Splitwise expense object."""
        
        # Format date if available
        date_str = None
        if parsed_expense.date:
            date_str = parsed_expense.date.strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(parsed_expense.date, 'strftime') else str(parsed_expense.date)
        
        # For equal splits, don't include users - authenticated user is assumed to be payer
        # and expense is split equally among all group members
        splitwise_expense = SplitwiseExpense(
            cost=f"{parsed_expense.amount:.2f}",
            description=parsed_expense.description,
            currency_code=parsed_expense.currency,
            date=date_str,
            details=email_summary,  # Add email summary as details/notes
            group_id=group_id,
            users=None,  # Don't include users for equal split
            split_equally=True
        )
        
        logger.info(f"Created expense: {splitwise_expense.description} - ${splitwise_expense.cost} for group {group_id}")
        if date_str:
            logger.info(f"Expense date: {date_str}")
        if email_summary:
            logger.info(f"Details: {email_summary}")
        
        return splitwise_expense

# Factory function for creating converter instance
def create_expense_converter(splitwise_client: SplitwiseClient) -> ExpenseConverter:
    """Create and return an ExpenseConverter instance."""
    return ExpenseConverter(splitwise_client) 