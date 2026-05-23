#!/usr/bin/env python3
"""
Test script for Groq AI integration.
Run this to verify Groq API connectivity.
"""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def test_groq_connection():
    api_key = os.getenv('GROQ_API_KEY', '')
    if not api_key or api_key == 'your_groq_api_key_here':
        print("❌ No valid Groq API key found in .env file")
        print("Please add your API key to the .env file:")
        print("GROQ_API_KEY=your_actual_api_key_here")
        return False

    try:
        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, test message"}],
            temperature=0.7,
            max_tokens=50
        )
        response = completion.choices[0].message.content
        print("✅ Groq API connection successful!")
        print(f"Response: {response}")
        return True
    except Exception as e:
        print(f"❌ Groq API connection failed: {e}")
        return False

if __name__ == "__main__":
    test_groq_connection()