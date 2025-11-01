#!/usr/bin/env python3
"""
Simple API test script for vocabulary app
Run this after restarting the application with the fixed routes
"""
import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("=" * 60)
    print("Testing Vocabulary App API Endpoints")
    print("=" * 60)
    print()
    
    # Test 1: Create VocabularyItem
    print("1️⃣  Creating VocabularyItem...")
    vocab_data = {
        "front": "Hello",
        "back": "Hola", 
        "comment": "Basic greeting",
        "lesson": "Lesson 1"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/vocabulary-items",
        json=vocab_data
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    vocab_id: Optional[str] = None
    if response.status_code == 201:
        vocab_id = response.json().get("id")
        print(f"✅ Created VocabularyItem ID: {vocab_id}")
    print()
    
    # Test 2: Get VocabularyItem by ID
    if vocab_id:
        print(f"2️⃣  Getting VocabularyItem by ID: {vocab_id}")
        response = requests.get(f"{BASE_URL}/api/vocabulary-items/{vocab_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    
    # Test 3: List all VocabularyItems
    print("3️⃣  Listing all VocabularyItems...")
    response = requests.get(f"{BASE_URL}/api/vocabulary-items")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total items: {result.get('total', 0)}")
    print(f"Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 4: Create another VocabularyItem
    print("4️⃣  Creating another VocabularyItem...")
    vocab2_data = {
        "front": "Goodbye",
        "back": "Adiós",
        "comment": "Farewell",
        "lesson": "Lesson 1"
    }
    response = requests.post(f"{BASE_URL}/api/vocabulary-items", json=vocab2_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()
    
    # Test 5: Update VocabularyItem
    if vocab_id:
        print(f"5️⃣  Updating VocabularyItem: {vocab_id}")
        update_data = {
            "front": "Hello",
            "back": "Hola",
            "comment": "Updated - Basic greeting in Spanish",
            "lesson": "Lesson 1 - Greetings"
        }
        response = requests.put(
            f"{BASE_URL}/api/vocabulary-items/{vocab_id}",
            json=update_data
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    
    # Test 6: Create ShareLink
    print("6️⃣  Creating ShareLink...")
    share_data = {
        "token": "abc123xyz456",
        "label": "Spanish Vocabulary - Week 1"
    }
    response = requests.post(f"{BASE_URL}/api/share-links", json=share_data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    share_id: Optional[str] = None
    if response.status_code == 201:
        share_id = response.json().get("id")
        print(f"✅ Created ShareLink ID: {share_id}")
    print()
    
    # Test 7: Get ShareLink by ID
    if share_id:
        print(f"7️⃣  Getting ShareLink by ID: {share_id}")
        response = requests.get(f"{BASE_URL}/api/share-links/{share_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    
    # Test 8: List all ShareLinks
    print("8️⃣  Listing all ShareLinks...")
    response = requests.get(f"{BASE_URL}/api/share-links")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total links: {result.get('total', 0)}")
    print(f"Response: {json.dumps(result, indent=2)}")
    print()
    
    # Test 9: Revoke ShareLink
    if share_id:
        print(f"9️⃣  Revoking ShareLink: {share_id}")
        response = requests.delete(f"{BASE_URL}/api/share-links/{share_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    
    # Test 10: Delete VocabularyItem
    if vocab_id:
        print(f"🔟 Deleting VocabularyItem: {vocab_id}")
        response = requests.delete(f"{BASE_URL}/api/vocabulary-items/{vocab_id}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()
    
    # Test 11: Final list
    print("1️⃣1️⃣  Final list of VocabularyItems...")
    response = requests.get(f"{BASE_URL}/api/vocabulary-items")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Total items: {result.get('total', 0)}")
    print()
    
    print("=" * 60)
    print("✅ All API tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the API server")
        print(f"   Make sure the app is running on {BASE_URL}")
    except Exception as e:
        print(f"❌ Error: {e}")
