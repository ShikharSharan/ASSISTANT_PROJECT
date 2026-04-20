#!/usr/bin/env python3
"""
Test script to verify AI functionality within the app.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from app.ai import get_chat_response
from app.backend import TaskManager, MoneyManager
from app.sqlite_storage import SQLiteStorage

def test_ai_response():
    """Test AI response functionality."""
    # Initialize managers (they use global storage)
    task_manager = TaskManager()
    money_manager = MoneyManager()

    # Test with existing data (don't add test data to avoid conflicts)
    # task_manager.add_task("Complete project report", "", "High")
    # task_manager.add_task("Buy groceries", "", "Medium")
    # money_manager.add_entry("Income", 50000, "Salary")
    # money_manager.add_entry("Expense", -15000, "Rent")

    # Test different types of queries
    test_queries = [
        "Hello",  # Simple greeting
        "How can I improve my productivity?",  # Complex question (should use Groq)
        "What are my priorities?",  # Task-related
        "How is my budget looking?",  # Money-related
        "Help me survive this month",  # Survival mode
    ]

    print("🧪 Testing AI Response Functionality")
    print("=" * 50)

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            response = get_chat_response(query, task_manager, money_manager)
            if response:
                print(f"✅ Response: {response[:100]}{'...' if len(response) > 100 else ''}")
            else:
                print("❌ No response generated")
        except Exception as e:
            print(f"❌ Error: {e}")

    print("\n" + "=" * 50)
    print("🎯 AI Testing Complete!")

if __name__ == "__main__":
    test_ai_response()