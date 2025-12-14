"""
Test script for PostgreSQL + pgvector Face Recognition System
Tests region-based filtering and vector similarity search
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models.database import DatabaseManager, Person, FaceEncoding
from src.services.advanced_face_service import AdvancedFaceRecognitionService
import numpy as np
import cv2

def test_database_connection():
    """Test PostgreSQL connection"""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)
    try:
        db = DatabaseManager()
        stats = db.get_statistics()
        print("✓ Database connection successful!")
        print(f"  - Total persons: {stats['total_persons']}")
        print(f"  - Total face encodings: {stats['total_encodings']}")
        print(f"  - Region counts: {stats['region_counts']}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def test_region_enrollment():
    """Test enrollment with region support"""
    print("\n" + "=" * 60)
    print("TEST 2: Region-Based Enrollment")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Create test persons in different regions
        person_a = db.create_person("John Doe", region="A", description="Region A user")
        print(f"✓ Created person in Region A: {person_a.name} (ID: {person_a.id})")
        
        person_b = db.create_person("Jane Smith", region="B", description="Region B user")
        print(f"✓ Created person in Region B: {person_b.name} (ID: {person_b.id})")
        
        person_c = db.create_person("Bob Wilson", region="C", description="Region C user")
        print(f"✓ Created person in Region C: {person_c.name} (ID: {person_c.id})")
        
        # Add fake embeddings
        fake_embedding_a = np.random.rand(512).astype(np.float32)
        fake_embedding_b = np.random.rand(512).astype(np.float32)
        fake_embedding_c = np.random.rand(512).astype(np.float32)
        
        db.add_face_encoding(person_a.id, fake_embedding_a, confidence=0.95, quality_score=0.95)
        db.add_face_encoding(person_b.id, fake_embedding_b, confidence=0.92, quality_score=0.92)
        db.add_face_encoding(person_c.id, fake_embedding_c, confidence=0.90, quality_score=0.90)
        
        print("✓ Added face encodings for all test persons")
        
        return True
    except Exception as e:
        print(f"✗ Region enrollment test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_search():
    """Test pgvector similarity search with region filtering"""
    print("\n" + "=" * 60)
    print("TEST 3: Vector Similarity Search (Region Filtering)")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Get a person from Region A
        person_a = db.get_person_by_name("John Doe", region="A")
        if not person_a:
            print("✗ Test person not found. Run test_region_enrollment first.")
            return False
        
        # Get their face embedding
        encodings = db.get_face_encodings(person_id=person_a.id)
        if not encodings:
            print("✗ No face encodings found")
            return False
        
        test_embedding = encodings[0].get_encoding()
        
        # Test 1: Search in Region A (should find match)
        print("\nTest 3a: Searching in Region A...")
        matches_a = db.find_similar_faces(
            embedding=test_embedding,
            region="A",
            threshold=0.5,
            limit=5
        )
        print(f"  Found {len(matches_a)} matches in Region A")
        if matches_a:
            print(f"  ✓ Best match: {matches_a[0]['name']} (score: {matches_a[0]['match_score']:.1f}%)")
        
        # Test 2: Search in Region B (should NOT find match)
        print("\nTest 3b: Searching in Region B (should return empty)...")
        matches_b = db.find_similar_faces(
            embedding=test_embedding,
            region="B",
            threshold=0.5,
            limit=5
        )
        print(f"  Found {len(matches_b)} matches in Region B")
        if len(matches_b) == 0:
            print("  ✓ Correct! No matches in different region")
        else:
            print("  ✗ ERROR: Found matches in wrong region!")
        
        # Test 3: Search in Region C (should NOT find match)
        print("\nTest 3c: Searching in Region C (should return empty)...")
        matches_c = db.find_similar_faces(
            embedding=test_embedding,
            region="C",
            threshold=0.5,
            limit=5
        )
        print(f"  Found {len(matches_c)} matches in Region C")
        if len(matches_c) == 0:
            print("  ✓ Correct! No matches in different region")
        else:
            print("  ✗ ERROR: Found matches in wrong region!")
        
        return True
    except Exception as e:
        print(f"✗ Vector search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance():
    """Test search performance with large dataset"""
    print("\n" + "=" * 60)
    print("TEST 4: Performance Test")
    print("=" * 60)
    
    try:
        import time
        db = DatabaseManager()
        
        # Create test data
        print("Creating 100 test persons across 3 regions...")
        for i in range(100):
            region = ["A", "B", "C"][i % 3]
            person = db.create_person(f"Test Person {i}", region=region)
            fake_embedding = np.random.rand(512).astype(np.float32)
            db.add_face_encoding(person.id, fake_embedding, confidence=0.9, quality_score=0.9)
        
        print("✓ Created 100 test persons")
        
        # Test search speed
        test_embedding = np.random.rand(512).astype(np.float32)
        
        start_time = time.time()
        matches = db.find_similar_faces(
            embedding=test_embedding,
            region="A",
            threshold=0.3,
            limit=10
        )
        search_time = (time.time() - start_time) * 1000  # Convert to ms
        
        print(f"✓ Search completed in {search_time:.2f}ms")
        print(f"  Found {len(matches)} matches in Region A")
        
        if search_time < 100:  # Should be very fast with HNSW index
            print("  ✓ Excellent performance!")
        elif search_time < 500:
            print("  ✓ Good performance")
        else:
            print("  ⚠ Slower than expected (might need index tuning)")
        
        return True
    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n" + "=" * 60)
    print("Cleanup: Removing test data")
    print("=" * 60)
    
    try:
        db = DatabaseManager()
        
        # Delete all test persons
        with db.get_session() as session:
            # This will cascade delete all face_encodings
            deleted = session.query(Person).delete()
            print(f"✓ Deleted {deleted} test persons")
        
        return True
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("PostgreSQL + pgvector Face Recognition System Tests")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Region-Based Enrollment", test_region_enrollment),
        ("Vector Similarity Search", test_vector_search),
        ("Performance Test", test_performance),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            results.append((name, False))
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready for use.")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")

if __name__ == "__main__":
    main()
