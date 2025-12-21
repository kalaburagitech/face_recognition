#!/usr/bin/env python3
"""
System Diagnostic Script
Checks all components of the face recognition system
"""
import sys
sys.path.insert(0, '.')

def test_database():
    """Test database connection and schema"""
    print("\n" + "="*60)
    print("1. DATABASE TEST")
    print("="*60)
    
    try:
        from src.models.database import DatabaseManager
        from sqlalchemy import text
        
        db = DatabaseManager()
        print("✓ DatabaseManager initialized")
        
        with db.get_session() as session:
            # Test connection
            result = session.execute(text('SELECT 1'))
            print("✓ Database connection OK")
            
            # Check persons table schema
            result = session.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'persons'
                ORDER BY ordinal_position
            """))
            
            print("\n  Persons table schema:")
            required_fields = ['id', 'name', 'region', 'emp_id', 'emp_rank']
            found_fields = []
            
            for row in result:
                col_name = row[0]
                found_fields.append(col_name)
                status = "✓" if col_name in required_fields else " "
                print(f"    {status} {col_name:20} {row[1]:20} NULL={row[2]}")
            
            # Check for missing required fields
            missing = set(required_fields) - set(found_fields)
            if missing:
                print(f"\n  ❌ Missing required fields: {missing}")
                return False
            else:
                print(f"\n  ✓ All required fields present")
            
            # Count persons
            from src.models.database import Person
            count = session.query(Person).count()
            print(f"\n  Total persons in database: {count}")
            
            if count > 0:
                person = session.query(Person).first()
                print(f"  Sample person:")
                print(f"    - Name: {person.name}")
                print(f"    - Emp ID: {person.emp_id}")
                print(f"    - Region: {person.region}")
                print(f"    - Rank: {person.emp_rank}")
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service():
    """Test face recognition service"""
    print("\n" + "="*60)
    print("2. SERVICE TEST")
    print("="*60)
    
    try:
        from src.services.advanced_face_service import AdvancedFaceRecognitionService
        
        print("Initializing service (this may take a moment)...")
        service = AdvancedFaceRecognitionService()
        print(f"✓ Service initialized with model: {service.model_name}")
        print(f"✓ Database manager: {type(service.db_manager).__name__}")
        print(f"✓ Visualizer: {type(service.visualizer).__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api():
    """Test API endpoints"""
    print("\n" + "="*60)
    print("3. API TEST")
    print("="*60)
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        print("\nTesting /api/health...")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test persons endpoint
        print("\nTesting /api/persons...")
        response = requests.get(f"{base_url}/api/persons", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Persons API working")
            print(f"  Total persons: {data.get('total', 0)}")
            
            if data.get('persons'):
                person = data['persons'][0]
                print(f"  Sample person fields:")
                for key in ['name', 'emp_id', 'emp_rank', 'region']:
                    value = person.get(key, 'MISSING')
                    status = "✓" if value != 'MISSING' else "❌"
                    print(f"    {status} {key}: {value}")
        else:
            print(f"❌ Persons API failed: {response.status_code}")
            return False
        
        # Test statistics endpoint
        print("\nTesting /api/statistics...")
        response = requests.get(f"{base_url}/api/statistics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Statistics API working")
            print(f"  Total persons: {data.get('total_persons', 0)}")
            print(f"  Total encodings: {data.get('total_encodings', 0)}")
        else:
            print(f"❌ Statistics API failed: {response.status_code}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("   Make sure the server is running: python3 main.py")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all diagnostic tests"""
    print("\n" + "="*60)
    print("FACE RECOGNITION SYSTEM DIAGNOSTICS")
    print("="*60)
    
    results = {
        'database': test_database(),
        'service': test_service(),
        'api': test_api()
    }
    
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{test_name.upper():20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL TESTS PASSED - System is working correctly!")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
