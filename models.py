"""Data models for expense forwarder."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from decimal import Decimal

class ParsedExpense(BaseModel):
    """Parsed expense data from email content."""
    
    description: str = Field(..., description="Description of the expense")
    amount: float = Field(..., gt=0, description="Amount of the expense")
    currency: str = Field(default="USD", description="Currency code")
    date: Optional[datetime] = Field(default=None, description="Date of the expense")
    category: Optional[str] = Field(default=None, description="Category of the expense")
    participants: List[str] = Field(default_factory=list, description="List of participant names or emails")
    split_type: str = Field(default="equal", description="How to split the expense (equal, exact, percentage)")
    paid_by: Optional[str] = Field(default=None, description="Who paid for the expense")
    
    @validator('currency')
    def validate_currency(cls, v):
        """Validate currency code."""
        if len(v) != 3:
            raise ValueError('Currency code must be 3 characters')
        return v.upper()
    
    @validator('split_type')
    def validate_split_type(cls, v):
        """Validate split type."""
        valid_types = ['equal', 'exact', 'percentage']
        if v not in valid_types:
            raise ValueError(f'Split type must be one of {valid_types}')
        return v

class SplitwiseUser(BaseModel):
    """Splitwise user data for expense creation."""
    
    user_id: int = Field(..., description="Splitwise user ID")
    paid_share: str = Field(default="0.00", description="Amount this user paid")
    owed_share: str = Field(default="0.00", description="Amount this user owes")
    net_balance: str = Field(default="0.00", description="Net balance for this user")

class SplitwiseExpense(BaseModel):
    """Splitwise expense request model."""
    
    cost: str = Field(..., description="Total cost of the expense")
    description: str = Field(..., description="Description of the expense")
    details: Optional[str] = Field(default=None, description="Additional details/notes about the expense")
    currency_code: str = Field(default="USD", description="Currency code")
    date: Optional[str] = Field(default=None, description="Date in ISO format (YYYY-MM-DDTHH:MM:SSZ)")
    category_id: Optional[int] = Field(default=None, description="Category ID")
    group_id: Optional[int] = Field(default=None, description="Group ID (required for group expenses)")
    users: Optional[List[SplitwiseUser]] = Field(default=None, description="List of users involved in the expense")
    split_equally: bool = Field(default=True, description="Whether to split equally")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            Decimal: str
        }
        exclude_none = True  # Exclude None values from JSON

class SplitwiseExpenseResponse(BaseModel):
    """Splitwise API response for expense creation."""
    
    expenses: List[Dict[str, Any]] = Field(..., description="Created expenses data")
    errors: Dict[str, Any] = Field(default_factory=dict, description="API errors")

class EmailContent(BaseModel):
    """Email content model."""
    
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body")
    sender: Optional[str] = Field(default=None, description="Email sender")
    
    @validator('subject', 'body')
    def validate_not_empty(cls, v):
        """Validate that subject and body are not empty."""
        if not v or not v.strip():
            raise ValueError('Subject and body cannot be empty')
        return v.strip()

class OpenAIResponse(BaseModel):
    """OpenAI API response model."""
    
    parsed_expense: ParsedExpense = Field(..., description="Parsed expense data")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score of the parsing")
    notes: Optional[str] = Field(default=None, description="Additional notes about the parsing")
    email_summary: Optional[str] = Field(default=None, description="Brief summary of the email content") 