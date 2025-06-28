"""Example usage of the expense forwarder."""

from main import ExpenseForwarder

def example_basic_usage():
    """Example of basic usage with authentication."""
    
    # Initialize the forwarder
    forwarder = ExpenseForwarder()
    
    # Authenticate with Splitwise (this will open a browser for OAuth)
    access_token = forwarder.authenticate_splitwise()
    print(f"Authenticated! Access token: {access_token[:20]}...")
    
    # Example email content
    subject = "Dinner Receipt - Pizza Palace"
    body = """
    Hi everyone!
    
    I paid for dinner at Pizza Palace last night.
    Total: $45.67
    
    Let's split this between me, John, and Sarah.
    
    Thanks!
    """
    
    # Process the email
    result = forwarder.process_email(
        subject=subject,
        body=body,
        min_confidence=0.6
    )
    
    if result['success']:
        print(f"✅ Created expense: {result['description']}")
        print(f"Amount: {result['currency']} {result['amount']}")
        print(f"Expense ID: {result['expense_id']}")
    else:
        print(f"❌ Failed: {result['error']}")

def example_with_existing_token():
    """Example using an existing access token."""
    
    # If you already have an access token, you can use it directly
    access_token = "your_saved_access_token_here"
    
    forwarder = ExpenseForwarder(access_token=access_token)
    
    # Example email about a shared Uber ride
    subject = "Uber Receipt"
    body = """
    Your trip with Uber
    
    From: Downtown
    To: Airport
    Total: $28.50
    
    Shared with Alex and Maria
    """
    
    result = forwarder.process_email(
        subject=subject,
        body=body,
        group_id=12345,  # Specific group ID
        min_confidence=0.7
    )
    
    print(f"Result: {result}")

def example_list_data():
    """Example of listing user data."""
    
    forwarder = ExpenseForwarder()
    forwarder.authenticate_splitwise()
    
    # Get user info
    user_info = forwarder.get_user_info()
    print(f"User: {user_info['user']['first_name']} {user_info['user']['last_name']}")
    
    # List friends
    friends = forwarder.list_friends()
    print(f"\nFriends ({len(friends)}):")
    for friend in friends[:5]:  # Show first 5
        print(f"  - {friend['first_name']} {friend['last_name']}")
    
    # List groups
    groups = forwarder.list_groups()
    print(f"\nGroups ({len(groups)}):")
    for group in groups[:5]:  # Show first 5
        print(f"  - {group['name']} (ID: {group['id']})")

if __name__ == "__main__":
    print("Expense Forwarder Examples")
    print("=" * 40)
    
    print("\n1. Basic usage example:")
    try:
        example_basic_usage()
    except Exception as e:
        print(f"Error in basic example: {e}")
    
    print("\n2. Example with existing token:")
    try:
        example_with_existing_token()
    except Exception as e:
        print(f"Error in token example: {e}")
    
    print("\n3. List data example:")
    try:
        example_list_data()
    except Exception as e:
        print(f"Error in list example: {e}") 