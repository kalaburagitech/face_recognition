#!/usr/bin/env python3
"""
Test the attendance API endpoint directly
"""
import requests
from datetime import datetime

# Test with an existing person
person_id = 109  # shashank from the test

print("=" * 60)
print("Testing Attendance API Endpoint")
print("=" * 60)

# Test 1: Mark attendance first time (or check if already marked)
print("\n--- Test 1: First attendance marking ---")
response = requests.post(
    'http://localhost:8000/api/attendance/mark',
    data={
        'person_id': person_id,
        'status': 'present'
    }
)

print(f"Status Code: {response.status_code}")
result = response.json()
print(f"Response: {result}")
print(f"already_marked: {result.get('already_marked')}")
print(f"success: {result.get('success')}")

# Test 2: Try to mark again (should show already marked)
print("\n--- Test 2: Second attendance marking (should be duplicate) ---")
response2 = requests.post(
    'http://localhost:8000/api/attendance/mark',
    data={
        'person_id': person_id,
        'status': 'present'
    }
)

print(f"Status Code: {response2.status_code}")
result2 = response2.json()
print(f"Response: {result2}")
print(f"already_marked: {result2.get('already_marked')}")
print(f"success: {result2.get('success')}")

if result2.get('already_marked') == True:
    print("\n✓ SUCCESS: Duplicate detection working correctly!")
else:
    print("\n❌ FAIL: Duplicate not detected!")

print("\n" + "=" * 60)
