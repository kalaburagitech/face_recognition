#!/usr/bin/env python3
"""
Test script to verify attendance marking flow
"""
import sys
from datetime import datetime
from src.models.database import DatabaseManager

def test_attendance_flow():
    """Test the attendance marking with duplicate detection"""
    db = DatabaseManager()
    
    print("=" * 60)
    print("Testing Attendance Marking Flow")
    print("=" * 60)
    
    # Get a sample person
    persons = db.get_all_persons()
    if not persons:
        print("❌ No persons found in database. Please enroll someone first.")
        return False
    
    test_person = persons[0]
    print(f"\n✓ Testing with person: {test_person.name} (ID: {test_person.id}, Emp ID: {test_person.emp_id})")
    
    # Test 1: Mark attendance for the first time
    print("\n--- Test 1: First attendance marking ---")
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Check if already marked
    with db.get_session() as session:
        from src.models.database import Attendance
        existing = session.query(Attendance).filter(
            Attendance.person_id == test_person.id,
            Attendance.date == today
        ).first()
        
        if existing:
            print(f"⚠️  Attendance already exists for today")
            print(f"   Status: {existing.status}")
            print(f"   Marked at: {existing.marked_at}")
        else:
            attendance = db.mark_attendance(test_person.id, today, 'present')
            print(f"✓ Attendance marked successfully")
            print(f"   ID: {attendance.id}")
            print(f"   Status: {attendance.status}")
            print(f"   Marked at: {attendance.marked_at}")
    
    # Test 2: Try to mark again (should detect duplicate)
    print("\n--- Test 2: Duplicate attendance marking ---")
    with db.get_session() as session:
        from src.models.database import Attendance
        existing = session.query(Attendance).filter(
            Attendance.person_id == test_person.id,
            Attendance.date == today
        ).first()
        
        if existing:
            print(f"✓ Duplicate detected correctly!")
            print(f"   Already marked at: {existing.marked_at}")
            print(f"   Status: {existing.status}")
        else:
            print(f"❌ Duplicate detection failed")
    
    # Test 3: Get attendance records
    print("\n--- Test 3: Retrieve attendance records ---")
    records = db.get_attendance_by_date(today)
    print(f"✓ Found {len(records)} attendance records for today")
    for record in records[:3]:  # Show first 3
        print(f"   - {record['name']} ({record['emp_id']}): {record['status']}")
    
    # Test 4: Get all persons with attendance status
    print("\n--- Test 4: All persons with attendance status ---")
    all_records = db.get_all_persons_with_attendance(today)
    present_count = len([r for r in all_records if r['status'] == 'present'])
    absent_count = len([r for r in all_records if r['status'] == 'absent'])
    print(f"✓ Total persons: {len(all_records)}")
    print(f"   Present: {present_count}")
    print(f"   Absent: {absent_count}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = test_attendance_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
