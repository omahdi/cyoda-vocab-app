#!/usr/bin/env python3
"""
Import vocabulary items from CSV file to Cyoda via API endpoints.

Usage:
    python import_vocabulary_csv.py <csv_file> [--url BASE_URL] [--lesson LESSON_NAME]
"""

import argparse
import csv
import sys
from typing import Dict, List, Optional

import requests


def parse_csv_file(filepath: str) -> List[Dict[str, str]]:
    """Parse CSV file and return list of vocabulary items."""
    items = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        # Use csv.reader to handle quoted fields properly
        reader = csv.reader(f)
        headers = next(reader)  # Skip header row
        
        print(f"CSV Headers: {headers}")
        print(f"Expected: id, front, back, comment")
        print()
        
        for row_num, row in enumerate(reader, start=2):
            if not row or len(row) < 2:
                print(f"⚠️  Skipping empty or invalid row {row_num}")
                continue
            
            # Handle different CSV formats
            # Expected: id, front, back, comment
            item = {}
            
            if len(row) >= 4:
                # Standard format with all columns
                item = {
                    'id': row[0].strip() if row[0] else '',
                    'front': row[1].strip() if len(row) > 1 else '',
                    'back': row[2].strip() if len(row) > 2 else '',
                    'comment': row[3].strip() if len(row) > 3 else ''
                }
            elif len(row) == 3:
                # Missing comment
                item = {
                    'id': row[0].strip() if row[0] else '',
                    'front': row[1].strip(),
                    'back': row[2].strip(),
                    'comment': ''
                }
            elif len(row) == 2:
                # Only front and back
                item = {
                    'id': '',
                    'front': row[0].strip(),
                    'back': row[1].strip(),
                    'comment': ''
                }
            
            # Validate required fields
            if not item.get('front') or not item.get('back'):
                print(f"⚠️  Row {row_num}: Skipping - missing front or back: {row}")
                continue
            
            # If there are extra columns, append them to comment
            if len(row) > 4:
                extra = ', '.join(row[4:])
                if item['comment']:
                    item['comment'] += ' ' + extra
                else:
                    item['comment'] = extra
            
            items.append(item)
            print(f"✓ Row {row_num}: {item['front']} → {item['back']}")
    
    return items


def create_vocabulary_item(
    base_url: str,
    front: str,
    back: str,
    comment: Optional[str] = None,
    lesson: Optional[str] = None
) -> Dict:
    """Create a vocabulary item via API."""
    url = f"{base_url}/api/vocabulary-items"
    
    data = {
        "front": front,
        "back": back,
    }
    
    if comment:
        data["comment"] = comment
    
    if lesson:
        data["lesson"] = lesson
    
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }


def import_vocabulary(
    csv_file: str,
    base_url: str = "http://127.0.0.1:8000",
    lesson: Optional[str] = None,
    dry_run: bool = False
) -> Dict:
    """Import all vocabulary items from CSV file."""
    print("=" * 70)
    print("Vocabulary CSV Import Tool")
    print("=" * 70)
    print(f"CSV File: {csv_file}")
    print(f"API URL: {base_url}")
    print(f"Lesson: {lesson or '(not set)'}")
    print(f"Dry Run: {dry_run}")
    print("=" * 70)
    print()
    
    # Parse CSV
    print("📖 Parsing CSV file...")
    try:
        items = parse_csv_file(csv_file)
    except FileNotFoundError:
        print(f"❌ Error: File not found: {csv_file}")
        return {"success": False, "error": "File not found"}
    except Exception as e:
        print(f"❌ Error parsing CSV: {e}")
        return {"success": False, "error": str(e)}
    
    print(f"\n✓ Found {len(items)} vocabulary items to import")
    print()
    
    if dry_run:
        print("🔍 DRY RUN - No items will be created")
        print()
        for i, item in enumerate(items, 1):
            print(f"{i}. {item['front']} → {item['back']}")
            if item.get('comment'):
                print(f"   Comment: {item['comment']}")
        return {"success": True, "dry_run": True, "items_found": len(items)}
    
    # Import each item
    print("📤 Importing items to Cyoda...")
    print()
    
    results = {
        "total": len(items),
        "successful": 0,
        "failed": 0,
        "errors": []
    }
    
    for i, item in enumerate(items, 1):
        print(f"[{i}/{len(items)}] Importing: {item['front']} → {item['back']}")
        
        result = create_vocabulary_item(
            base_url=base_url,
            front=item['front'],
            back=item['back'],
            comment=item.get('comment'),
            lesson=lesson
        )
        
        if result["success"]:
            results["successful"] += 1
            entity_id = result["data"].get("entity_id", "unknown")
            print(f"   ✅ Created (ID: {entity_id})")
        else:
            results["failed"] += 1
            results["errors"].append({
                "item": item,
                "error": result.get("error", "Unknown error")
            })
            print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
        print()
    
    # Summary
    print("=" * 70)
    print("Import Summary")
    print("=" * 70)
    print(f"Total items:      {results['total']}")
    print(f"✅ Successful:     {results['successful']}")
    print(f"❌ Failed:         {results['failed']}")
    print("=" * 70)
    
    if results["errors"]:
        print("\nErrors:")
        for err in results["errors"]:
            print(f"  • {err['item']['front']}: {err['error']}")
    
    results["success"] = results["failed"] == 0
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Import vocabulary items from CSV file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import from CSV with default settings
  python import_vocabulary_csv.py finnish-vocab-example.csv
  
  # Import with lesson name
  python import_vocabulary_csv.py vocab.csv --lesson "Finnish 101"
  
  # Dry run to preview without importing
  python import_vocabulary_csv.py vocab.csv --dry-run
  
  # Use custom API URL
  python import_vocabulary_csv.py vocab.csv --url http://localhost:5000

CSV Format:
  The CSV should have columns: id, front, back, comment
  - id: (optional) entity ID
  - front: Front side of flashcard (required)
  - back: Back side of flashcard (required)
  - comment: Additional notes (optional)
        """
    )
    
    parser.add_argument(
        "csv_file",
        help="Path to CSV file containing vocabulary items"
    )
    
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000",
        help="Base URL of the API (default: http://127.0.0.1:8000)"
    )
    
    parser.add_argument(
        "--lesson",
        help="Lesson name to assign to all imported items"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse CSV and show what would be imported without actually importing"
    )
    
    args = parser.parse_args()
    
    # Run import
    result = import_vocabulary(
        csv_file=args.csv_file,
        base_url=args.url,
        lesson=args.lesson,
        dry_run=args.dry_run
    )
    
    # Exit with appropriate code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
