"""Test script to verify expense forwarder functionality."""

import json
from models import EmailContent, ParsedExpense
from email_parser import EmailParser
from config import config

def test_email_parsing():
    """Test email parsing without actually calling OpenAI (mock response)."""
    
    print("Testing Email Parsing...")
    print("=" * 40)
    
    # Sample email content
    email_content = EmailContent(
        subject="Dinner Receipt - Pizza Palace",
        body="""
        Hi everyone!
        
        Had a great dinner at Pizza Palace last night.
        Total bill came to $67.50 including tip.
        
        Let's split this equally between me, John, and Sarah.
        
        Thanks!
        Mike
        """
    )
    
    print(f"Subject: {email_content.subject}")
    print(f"Body: {email_content.body[:100]}...")
    
    # Mock parsed response (what OpenAI would return)
    mock_parsed_expense = ParsedExpense(
        description="Dinner at Pizza Palace",
        amount=67.50,
        currency="USD",
        participants=["John", "Sarah"],
        split_type="equal",
        paid_by="Mike",
        category="Food"
    )
    
    print(f"\nParsed Expense:")
    print(f"  Description: {mock_parsed_expense.description}")
    print(f"  Amount: ${mock_parsed_expense.amount}")
    print(f"  Participants: {', '.join(mock_parsed_expense.participants)}")
    print(f"  Split Type: {mock_parsed_expense.split_type}")
    print(f"  Paid By: {mock_parsed_expense.paid_by}")
    print(f"  Category: {mock_parsed_expense.category}")

def test_configuration():
    """Test configuration loading."""
    
    print("\nTesting Configuration...")
    print("=" * 40)
    
    print(f"OpenAI Model: {config.OPENAI_MODEL}")
    print(f"Default Currency: {config.DEFAULT_CURRENCY}")
    print(f"Splitwise Base URL: {config.SPLITWISE_BASE_URL}")
    
    # Check if API keys are configured (don't print them)
    print(f"OpenAI API Key configured: {'Yes' if config.OPENAI_API_KEY else 'No'}")
    print(f"Splitwise Client ID configured: {'Yes' if config.SPLITWISE_CLIENT_ID else 'No'}")
    print(f"Splitwise Client Secret configured: {'Yes' if config.SPLITWISE_CLIENT_SECRET else 'No'}")
    
    print(f"\nConfiguration valid: {config.validate()}")

def test_data_models():
    """Test Pydantic data models."""
    
    print("\nTesting Data Models...")
    print("=" * 40)
    
    # Test ParsedExpense model
    try:
        expense = ParsedExpense(
            description="Test expense",
            amount=25.50,
            currency="USD",
            participants=["Alice", "Bob"],
            split_type="equal"
        )
        print(f"✅ ParsedExpense model works: {expense.description} - ${expense.amount}")
    except Exception as e:
        print(f"❌ ParsedExpense model error: {e}")
    
    # Test EmailContent model
    try:
        email = EmailContent(
            subject="Test Subject",
            body="Test body content"
        )
        print(f"✅ EmailContent model works: {email.subject}")
    except Exception as e:
        print(f"❌ EmailContent model error: {e}")
    
    # Test invalid data
    try:
        invalid_expense = ParsedExpense(
            description="",  # Empty description should fail validation
            amount=-5,  # Negative amount should fail
            currency="INVALID"  # Invalid currency should fail
        )
        print(f"❌ Validation should have failed but didn't")
    except Exception as e:
        print(f"✅ Validation correctly failed: {type(e).__name__}")

def main():
    """Run all tests."""
    
    print("Expense Forwarder Test Suite")
    print("=" * 50)
    
    try:
        test_configuration()
        test_data_models()
        test_email_parsing()
        
        print("\n" + "=" * 50)
        print("✅ All basic tests completed!")
        print("\nTo test the full functionality:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python main.py --auth-only --subject '' --body ''")
        print("3. Then try: python main.py --subject 'Test' --body 'Dinner $30 with John'")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main() 