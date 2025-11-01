#!/bin/bash
# Test script for vocabulary app endpoints

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
HEADER="Content-Type: application/json"

echo "========================================="
echo "Testing Vocabulary App Endpoints"
echo "Base URL: $BASE_URL"
echo "========================================="
echo ""

# Test 1: Create VocabularyItem
echo "1️⃣  Creating VocabularyItem..."
VOCAB_RESPONSE=$(curl -s -X POST "$BASE_URL/api/vocabulary-items" \
  -H "$HEADER" \
  -d '{
    "front": "Hello",
    "back": "Hola",
    "comment": "Basic greeting",
    "lesson": "Lesson 1"
  }')

echo "Response: $VOCAB_RESPONSE"
VOCAB_ID=$(echo $VOCAB_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Created VocabularyItem ID: $VOCAB_ID"
echo ""

# Test 2: Get VocabularyItem by ID
if [ ! -z "$VOCAB_ID" ]; then
  echo "2️⃣  Getting VocabularyItem by ID: $VOCAB_ID"
  curl -s -X GET "$BASE_URL/api/vocabulary-items/$VOCAB_ID" | jq '.' || echo "$VOCAB_RESPONSE"
  echo ""
fi

# Test 3: List all VocabularyItems
echo "3️⃣  Listing all VocabularyItems..."
curl -s -X GET "$BASE_URL/api/vocabulary-items" | jq '.' || curl -s -X GET "$BASE_URL/api/vocabulary-items"
echo ""

# Test 4: Create another VocabularyItem
echo "4️⃣  Creating another VocabularyItem..."
VOCAB2_RESPONSE=$(curl -s -X POST "$BASE_URL/api/vocabulary-items" \
  -H "$HEADER" \
  -d '{
    "front": "Goodbye",
    "back": "Adiós",
    "comment": "Farewell",
    "lesson": "Lesson 1"
  }')
echo "Response: $VOCAB2_RESPONSE"
echo ""

# Test 5: Update VocabularyItem
if [ ! -z "$VOCAB_ID" ]; then
  echo "5️⃣  Updating VocabularyItem: $VOCAB_ID"
  curl -s -X PUT "$BASE_URL/api/vocabulary-items/$VOCAB_ID" \
    -H "$HEADER" \
    -d '{
      "front": "Hello",
      "back": "Hola",
      "comment": "Updated comment - Basic greeting in Spanish",
      "lesson": "Lesson 1 - Greetings"
    }' | jq '.' || echo "Update response"
  echo ""
fi

# Test 6: Create ShareLink
echo "6️⃣  Creating ShareLink..."
SHARE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/share-links" \
  -H "$HEADER" \
  -d '{
    "token": "abc123xyz456",
    "label": "Spanish Vocabulary - Week 1"
  }')
echo "Response: $SHARE_RESPONSE"
SHARE_ID=$(echo $SHARE_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
echo "Created ShareLink ID: $SHARE_ID"
echo ""

# Test 7: Get ShareLink by ID
if [ ! -z "$SHARE_ID" ]; then
  echo "7️⃣  Getting ShareLink by ID: $SHARE_ID"
  curl -s -X GET "$BASE_URL/api/share-links/$SHARE_ID" | jq '.' || echo "ShareLink response"
  echo ""
fi

# Test 8: List all ShareLinks
echo "8️⃣  Listing all ShareLinks..."
curl -s -X GET "$BASE_URL/api/share-links" | jq '.' || curl -s -X GET "$BASE_URL/api/share-links"
echo ""

# Test 9: Revoke ShareLink
if [ ! -z "$SHARE_ID" ]; then
  echo "9️⃣  Revoking ShareLink: $SHARE_ID"
  curl -s -X DELETE "$BASE_URL/api/share-links/$SHARE_ID" | jq '.' || echo "Revoke response"
  echo ""
fi

# Test 10: Delete VocabularyItem
if [ ! -z "$VOCAB_ID" ]; then
  echo "🔟 Deleting VocabularyItem: $VOCAB_ID"
  curl -s -X DELETE "$BASE_URL/api/vocabulary-items/$VOCAB_ID" | jq '.' || echo "Delete response"
  echo ""
fi

# Test 11: Final list to verify deletion
echo "1️⃣1️⃣  Final list of VocabularyItems..."
curl -s -X GET "$BASE_URL/api/vocabulary-items" | jq '.' || curl -s -X GET "$BASE_URL/api/vocabulary-items"
echo ""

echo "========================================="
echo "✅ All endpoint tests completed!"
echo "========================================="
