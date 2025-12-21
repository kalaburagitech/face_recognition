#!/usr/bin/env python3
"""Fix the add_person_faces endpoint to validate faces belong to the person"""

with open('src/api/advanced_fastapi_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section to replace
old_section_start = "# Check similarity - Only check against OTHER people's faces"
old_section_end = ").all()"

# Find start position
start_pos = content.find(old_section_start)
if start_pos == -1:
    print("ERROR: Could not find start marker")
    exit(1)

# Find end position (first occurrence after start)
search_from = start_pos + len(old_section_start)
end_marker = "FaceEncodingModel.person_id != person_id\n                                ).all()"
end_pos = content.find(end_marker, search_from)
if end_pos == -1:
    print("ERROR: Could not find end marker")
    exit(1)
end_pos += len(end_marker)

# New code to insert
new_code = """# Check similarity - Verify the face belongs to THIS person
                        try:
                            with service.db_manager.get_session() as check_session:
                                from ..models import FaceEncoding as FaceEncodingModel
                                
                                # Get recognition threshold (lower = stricter matching)
                                recognition_threshold = config.get('face_recognition.recognition_threshold', 0.6)
                                duplicate_threshold = config.get('face_recognition.duplicate_threshold', 0.85)
                                
                                # STEP 1: Verify the new face matches existing faces of THIS person
                                existing_faces = check_session.query(FaceEncodingModel).filter(
                                    FaceEncodingModel.person_id == person_id
                                ).all()
                                
                                if existing_faces:  # Only validate if person already has faces
                                    max_similarity_to_self = 0.0
                                    
                                    for existing_face in existing_faces:
                                        if existing_face.embedding is not None:
                                            # Handle encoded data in different formats
                                            existing_encoding = None
                                            if isinstance(existing_face.embedding, bytes):
                                                try:
                                                    existing_encoding = pickle.loads(existing_face.embedding)
                                                except Exception as e:
                                                    logger.warning(f"Trait deserialization failed: {e}")
                                                    continue
                                            elif isinstance(existing_face.embedding, np.ndarray):
                                                existing_encoding = existing_face.embedding
                                            elif isinstance(existing_face.embedding, (list, tuple)):
                                                existing_encoding = np.array(existing_face.embedding, dtype=np.float32)
                                            elif isinstance(existing_face.embedding, str):
                                                try:
                                                    existing_encoding = np.frombuffer(
                                                        base64.b64decode(existing_face.embedding), 
                                                        dtype=np.float32
                                                    )
                                                except Exception as e:
                                                    logger.warning(f"Base64Decoding failed: {e}")
                                                    continue
                                            else:
                                                logger.warning(f"Unknown encoding format: {type(existing_face.embedding)}")
                                                continue
                                            
                                            if existing_encoding is None or len(existing_encoding) == 0:
                                                continue
                                            
                                            # Calculate cosine similarity
                                            try:
                                                similarity = float(np.dot(encoding, existing_encoding) / 
                                                                 (np.linalg.norm(encoding) * np.linalg.norm(existing_encoding)))
                                                max_similarity_to_self = max(max_similarity_to_self, similarity)
                                            except Exception as e:
                                                logger.warning(f"Similarity calculation failed: {e}")
                                                continue
                                    
                                    # If the face doesn't match this person's existing faces, reject it
                                    if max_similarity_to_self < recognition_threshold:
                                        results.append({
                                            'file_name': face_file.filename,
                                            'success': False,
                                            'error': f'Face does not match existing faces of {person_name} (Similarity: {max_similarity_to_self*100:.1f}%, required: {recognition_threshold*100:.1f}%)'
                                        })
                                        error_count += 1
                                        raise Exception("Face mismatch")
                                
                                # STEP 2: Check similarities to other people's faces
                                other_faces = check_session.query(FaceEncodingModel, Person).join(
                                    Person, FaceEncodingModel.person_id == Person.id
                                ).filter(
                                    FaceEncodingModel.person_id != person_id
                                ).all()"""

# Replace the section
new_content = content[:start_pos] + new_code + content[end_pos:]

# Write back
with open('src/api/advanced_fastapi_app.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ Successfully updated add_person_faces endpoint")
print("Now the endpoint will:")
print("  1. Verify new face matches existing faces of the SAME person")
print("  2. Reject if face doesn't match (wrong person)")
print("  3. Also check against OTHER people's faces")
  
  