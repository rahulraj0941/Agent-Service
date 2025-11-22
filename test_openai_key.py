#!/usr/bin/env python3
"""
Simple script to test if your OpenAI API key has available credits.
This will make a minimal API call to verify your key works.
"""

import os
from openai import OpenAI

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ ERROR: OPENAI_API_KEY environment variable not set")
    print("Please set it in Replit Secrets")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")
print("\nTesting API with gpt-3.5-turbo (free tier model)...")
print("Making a minimal test request...\n")

try:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'API key works!'"}
        ],
        max_tokens=10
    )
    
    result = response.choices[0].message.content
    
    print("✅ SUCCESS! Your API key is working!")
    print(f"Response: {result}")
    print("\n📊 Usage Information:")
    print(f"   - Model: {response.model}")
    print(f"   - Tokens used: {response.usage.total_tokens}")
    print(f"   - Prompt tokens: {response.usage.prompt_tokens}")
    print(f"   - Completion tokens: {response.usage.completion_tokens}")
    print("\n✓ Your API key has available credits and the application should work!")
    
except Exception as e:
    error_str = str(e)
    print("❌ ERROR: API call failed")
    print(f"\nError details: {error_str}\n")
    
    if "insufficient_quota" in error_str or "429" in error_str:
        print("🔍 DIAGNOSIS: Your API key has NO available credits\n")
        print("SOLUTION:")
        print("1. Visit: https://platform.openai.com/settings/organization/billing/overview")
        print("2. Check your credit balance (it's probably $0.00)")
        print("3. Add a payment method and buy credits (minimum $5)")
        print("4. OR: If you're expecting free trial credits, check:")
        print("   - Trial credits may have expired (they expire after 3 months)")
        print("   - Free tier has very strict limits (3 requests/minute)")
        print("   - You may need to add a payment method even for free tier access")
        print("\n📖 More info: https://platform.openai.com/docs/guides/rate-limits")
    elif "invalid" in error_str.lower():
        print("🔍 DIAGNOSIS: Your API key appears to be invalid")
        print("\nSOLUTION:")
        print("1. Go to: https://platform.openai.com/api-keys")
        print("2. Create a new API key")
        print("3. Update it in Replit Secrets")
    else:
        print("🔍 DIAGNOSIS: Unknown error")
        print("Please check the error message above for details")
