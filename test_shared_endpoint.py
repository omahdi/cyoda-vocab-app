#!/usr/bin/env python3
"""
Test the shared vocabulary endpoint
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "finnish-basics-2025"

print("=" * 70)
print("Testing Shared Vocabulary Endpoint")
print("=" * 70)
print(f"Token: {TOKEN}")
print(f"URL: {BASE_URL}/api/shared/{TOKEN}")
print()

# Test the shared endpoint
print("📖 Fetching shared vocabulary...")
response = requests.get(f"{BASE_URL}/api/shared/{TOKEN}")

print(f"Status Code: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    
    print("✅ Success!")
    print()
    print("Share Information:")
    print(f"  Token:        {data.get('token')}")
    print(f"  Label:        {data.get('label')}")
    print(f"  Total Items:  {data.get('total')}")
    print()
    
    share_info = data.get('share_info', {})
    print("Share Statistics:")
    print(f"  Created:      {share_info.get('created_at')}")
    print(f"  Visit Count:  {share_info.get('visit_count')}")
    print(f"  Last Access:  {share_info.get('last_accessed') or 'Never'}")
    print()
    
    items = data.get('items', [])
    print(f"Vocabulary Items ({len(items)} total):")
    print("-" * 70)
    
    for i, item in enumerate(items[:5], 1):  # Show first 5
        print(f"{i}. {item.get('front')} → {item.get('back')}")
        if item.get('comment'):
            print(f"   💬 {item.get('comment')}")
        if item.get('lesson'):
            print(f"   📚 Lesson: {item.get('lesson')}")
        print()
    
    if len(items) > 5:
        print(f"... and {len(items) - 5} more items")
    
    print("=" * 70)
    print("Full Response (JSON):")
    print(json.dumps(data, indent=2))

else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)

print()
print("=" * 70)
print("Testing with invalid token...")
response = requests.get(f"{BASE_URL}/api/shared/invalid-token-xyz")
print(f"Status Code: {response.status_code}")
if response.status_code == 404:
    print("✅ Correctly returns 404 for invalid token")
    print(f"Response: {response.json()}")
