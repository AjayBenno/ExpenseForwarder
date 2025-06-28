"""Email parser module using OpenAI API."""

import json
import logging
from typing import Dict, Any
from openai import OpenAI

from config import config
from models import EmailContent, ParsedExpense, OpenAIResponse

logger = logging.getLogger(__name__)

class EmailParser:
    """Parser for extracting expense information from emails using OpenAI."""
    
    def __init__(self):
        """Initialize the email parser with OpenAI client."""
        if not config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
    
    def _create_expense_extraction_prompt(self, email_content: EmailContent) -> str:
        """Create a prompt for extracting expense information from email."""
        
        prompt = f"""
You are an expert at parsing email content to extract expense information for financial tracking.

Parse the following email and extract expense information in JSON format:

EMAIL SUBJECT: {email_content.subject}
EMAIL BODY: {email_content.body}

Extract the following information and return it as a JSON object:
{{
    "parsed_expense": {{
        "description": "Brief description of the expense",
        "amount": float (the total amount),
        "currency": "3-letter currency code (default: USD)",
        "date": "YYYY-MM-DD format if mentioned, null otherwise",
        "category": "expense category if apparent (e.g., 'Food', 'Transportation', 'Entertainment')",
        "participants": ["list", "of", "participant", "names", "or", "emails"],
        "split_type": "equal|exact|percentage (default: equal)",
        "paid_by": "name or email of who paid (if mentioned)"
    }},
    "confidence": float (0.0 to 1.0 - how confident you are in the parsing),
    "notes": "Any additional notes about the parsing or ambiguities"
}}

Guidelines:
1. Extract the main expense amount (ignore taxes, tips unless they're part of the total)
2. If multiple people are mentioned, add them to participants
3. Look for keywords like "split", "share", "owe", "paid" to identify participants
4. Default to "equal" split unless specific amounts or percentages are mentioned
5. If the email is clearly not about an expense, set confidence to 0.0
6. Be conservative with confidence - only use high confidence (>0.8) if information is very clear

Return ONLY the JSON object, no additional text.
"""
        return prompt
    
    async def parse_email_async(self, email_content: EmailContent) -> OpenAIResponse:
        """Parse email content asynchronously using OpenAI API."""
        try:
            prompt = self._create_expense_extraction_prompt(email_content)
            
            response = await self.client.chat.completions.acreate(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial expense parser. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {content}")
            
            # Parse the JSON response
            parsed_data = json.loads(content)
            
            # Validate and create the response model
            return OpenAIResponse(**parsed_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            logger.error(f"Raw response: {content}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing email with OpenAI: {e}")
            raise
    
    def parse_email(self, email_content: EmailContent) -> OpenAIResponse:
        """Parse email content synchronously using OpenAI API."""
        try:
            prompt = self._create_expense_extraction_prompt(email_content)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a financial expense parser. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {content}")
            
            # Parse the JSON response
            parsed_data = json.loads(content)
            
            # Validate and create the response model
            return OpenAIResponse(**parsed_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI JSON response: {e}")
            logger.error(f"Raw response: {content}")
            raise ValueError(f"Invalid JSON response from OpenAI: {e}")
        
        except Exception as e:
            logger.error(f"Error parsing email with OpenAI: {e}")
            raise
    
    def validate_parsing_confidence(self, response: OpenAIResponse, 
                                  min_confidence: float = 0.5) -> bool:
        """Validate that the parsing confidence meets minimum threshold."""
        return response.confidence >= min_confidence

# Factory function for creating parser instance
def create_email_parser() -> EmailParser:
    """Create and return an EmailParser instance."""
    return EmailParser() 