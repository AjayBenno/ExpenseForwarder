"""Expense converter module for transforming parsed email data to Splitwise expenses."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from config import config
from models import ParsedExpense, SplitwiseExpense, SplitwiseUser
from splitwise_client import SplitwiseClient

logger = logging.getLogger(__name__)

class ExpenseConverter:
    """Converts parsed expense data to Splitwise expense objects."""
    
    def __init__(self, splitwise_client: SplitwiseClient):
        """Initialize the expense converter with Splitwise client."""
        self.splitwise_client = splitwise_client
        self.current_user = None
        self._load_current_user()
    
    def _load_current_user(self):
        """Load current user information."""
        try:
            user_response = self.splitwise_client.get_current_user()
            self.current_user = user_response.get('user')
            logger.info(f"Loaded current user: {self.current_user.get('first_name')} {self.current_user.get('last_name')}")
        except Exception as e:
            logger.error(f"Failed to load current user: {e}")
            raise
    
    def _resolve_participants(self, participants: List[str]) -> List[Dict[str, Any]]:
        """Resolve participant names/emails to Splitwise user objects."""
        resolved_users = []
        
        # Always include current user
        if self.current_user:
            resolved_users.append(self.current_user)
        
        # Resolve other participants
        for participant in participants:
            if participant.strip():
                user = self.splitwise_client.find_user_by_name_or_email(participant.strip())
                if user:
                    # Check if user is not already in the list
                    if not any(u['id'] == user['id'] for u in resolved_users):
                        resolved_users.append(user)
                        logger.info(f"Resolved participant '{participant}' to user {user['first_name']} {user['last_name']}")
                else:
                    logger.warning(f"Could not resolve participant: {participant}")
        
        return resolved_users
    
    def _calculate_equal_split(self, total_amount: float, num_users: int) -> str:
        """Calculate equal split amount per user."""
        if num_users == 0:
            return "0.00"
        
        amount_per_user = total_amount / num_users
        return f"{amount_per_user:.2f}"
    
    def _determine_payer(self, parsed_expense: ParsedExpense, 
                        resolved_users: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Determine who paid for the expense."""
        
        # If paid_by is specified, try to find that user
        if parsed_expense.paid_by:
            for user in resolved_users:
                # Check by name or email
                first_name = user.get('first_name', '').lower()
                last_name = user.get('last_name', '').lower()
                full_name = f"{first_name} {last_name}".strip()
                email = user.get('email', '').lower()
                
                paid_by_lower = parsed_expense.paid_by.lower()
                
                if (paid_by_lower in [first_name, last_name, full_name, email]):
                    return user
        
        # Default to current user if not specified or not found
        return self.current_user
    
    def _create_splitwise_users(self, parsed_expense: ParsedExpense, 
                               resolved_users: List[Dict[str, Any]]) -> List[SplitwiseUser]:
        """Create Splitwise user objects with payment information."""
        
        if not resolved_users:
            raise ValueError("No valid users found for expense")
        
        total_amount = parsed_expense.amount
        num_users = len(resolved_users)
        
        # Determine who paid
        payer = self._determine_payer(parsed_expense, resolved_users)
        
        splitwise_users = []
        
        if parsed_expense.split_type == "equal":
            # Equal split calculation
            amount_per_user = self._calculate_equal_split(total_amount, num_users)
            
            for user in resolved_users:
                user_id = user['id']
                
                # The payer has paid_share = total_amount, others have 0
                paid_share = f"{total_amount:.2f}" if user_id == payer['id'] else "0.00"
                owed_share = amount_per_user
                
                splitwise_user = SplitwiseUser(
                    user_id=user_id,
                    paid_share=paid_share,
                    owed_share=owed_share
                )
                splitwise_users.append(splitwise_user)
        
        else:
            # For non-equal splits, default to equal for now
            # This could be extended to handle exact amounts or percentages
            logger.warning(f"Split type '{parsed_expense.split_type}' not fully implemented, using equal split")
            return self._create_splitwise_users(
                ParsedExpense(**{**parsed_expense.dict(), 'split_type': 'equal'}),
                resolved_users
            )
        
        return splitwise_users
    
    def _format_date(self, date: Optional[datetime]) -> Optional[str]:
        """Format date for Splitwise API."""
        if date:
            return date.strftime("%Y-%m-%d")
        return None
    
    def _resolve_category(self, category_name: Optional[str]) -> Optional[int]:
        """Resolve category name to Splitwise category ID."""
        if not category_name:
            return None
        
        try:
            category_id = self.splitwise_client.find_category_by_name(category_name)
            if category_id:
                logger.info(f"Resolved category '{category_name}' to ID {category_id}")
            else:
                logger.warning(f"Could not resolve category: {category_name}")
            return category_id
        except Exception as e:
            logger.error(f"Error resolving category '{category_name}': {e}")
            return None
    
    def convert_to_splitwise_expense(self, parsed_expense: ParsedExpense,
                                   group_id: Optional[int] = None) -> SplitwiseExpense:
        """Convert parsed expense to Splitwise expense object."""
        
        # Resolve participants to Splitwise users
        resolved_users = self._resolve_participants(parsed_expense.participants)
        
        if not resolved_users:
            raise ValueError("No valid participants found for expense")
        
        # Create Splitwise user objects
        splitwise_users = self._create_splitwise_users(parsed_expense, resolved_users)
        
        # Resolve category
        category_id = self._resolve_category(parsed_expense.category)
        
        # Use provided group_id or default from config
        final_group_id = group_id or config.DEFAULT_GROUP_ID
        
        # Create Splitwise expense
        splitwise_expense = SplitwiseExpense(
            cost=f"{parsed_expense.amount:.2f}",
            description=parsed_expense.description,
            currency_code=parsed_expense.currency,
            date=self._format_date(parsed_expense.date),
            category_id=category_id,
            group_id=final_group_id,
            users=splitwise_users,
            split_equally=parsed_expense.split_type == "equal"
        )
        
        logger.info(f"Converted expense: {splitwise_expense.description} - ${splitwise_expense.cost}")
        logger.info(f"Participants: {len(splitwise_users)} users")
        
        return splitwise_expense
    
    def validate_expense(self, expense: SplitwiseExpense) -> bool:
        """Validate that the expense is ready for creation."""
        
        # Check required fields
        if not expense.cost or float(expense.cost) <= 0:
            logger.error("Expense cost must be greater than 0")
            return False
        
        if not expense.description or not expense.description.strip():
            logger.error("Expense description is required")
            return False
        
        if not expense.users or len(expense.users) == 0:
            logger.error("At least one user is required")
            return False
        
        # Validate user data
        total_paid = sum(float(user.paid_share) for user in expense.users)
        total_owed = sum(float(user.owed_share) for user in expense.users)
        expense_cost = float(expense.cost)
        
        # Check that total paid equals expense cost
        if abs(total_paid - expense_cost) > 0.01:  # Allow for small rounding errors
            logger.error(f"Total paid ({total_paid}) does not match expense cost ({expense_cost})")
            return False
        
        # Check that total owed equals expense cost
        if abs(total_owed - expense_cost) > 0.01:  # Allow for small rounding errors
            logger.error(f"Total owed ({total_owed}) does not match expense cost ({expense_cost})")
            return False
        
        logger.info("Expense validation passed")
        return True

# Factory function for creating converter instance
def create_expense_converter(splitwise_client: SplitwiseClient) -> ExpenseConverter:
    """Create and return an ExpenseConverter instance."""
    return ExpenseConverter(splitwise_client) 