"""
PostgreSQL + pgvector Database Models for Face Recognition
Optimized for multi-client API deployment with region-based filtering
"""
import os
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Date, LargeBinary, ForeignKey, Index, Text, text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.pool import QueuePool
from pgvector.sqlalchemy import Vector
import numpy as np
import pickle

from ..utils.config import config

logger = logging.getLogger(__name__)

Base = declarative_base()


# ==================== Database Models ====================

class TimestampMixin:
    """Timestamp mix-in class"""
    @staticmethod
    def _get_ist_now():
        """Get current time in IST"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist)
    
    created_at = Column(DateTime(timezone=True), default=lambda: TimestampMixin._get_ist_now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: TimestampMixin._get_ist_now(), onupdate=lambda: TimestampMixin._get_ist_now(), nullable=False)


class Person(Base, TimestampMixin):
    """Person table with region and client support for multi-tenant API"""
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    region = Column(String(50), nullable=False, index=True)  # Region: ka, ap, tn
    emp_id = Column(String(100), nullable=False, unique=True, index=True)  # Employee ID
    emp_rank = Column(String(100), nullable=False, index=True)  # Employee Rank
    client_id = Column(String(100), nullable=True, index=True)  # For multi-tenant support
    description = Column(Text, nullable=True)  # Optional, for backward compatibility
    
    # Relationship to face encodings
    face_encodings = relationship('FaceEncoding', back_populates='person', cascade='all, delete-orphan')
    
    # Composite indexes for fast region + client filtering
    __table_args__ = (
        Index('idx_person_region_client', 'region', 'client_id'),
        Index('idx_person_name_region', 'name', 'region'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'emp_id': self.emp_id,
            'emp_rank': self.emp_rank,
            'client_id': self.client_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<Person(id={self.id}, name='{self.name}', region='{self.region}')>"


class Attendance(Base, TimestampMixin):
    """Attendance records table"""
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('persons.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default='present', nullable=False)  # present/absent
    marked_at = Column(DateTime(timezone=True), default=lambda: TimestampMixin._get_ist_now(), nullable=False)
    check_in_time = Column(DateTime(timezone=True), nullable=True)  # Check-in timestamp
    check_out_time = Column(DateTime(timezone=True), nullable=True)  # Check-out timestamp
    
    # Location tracking
    check_in_latitude = Column(Float, nullable=True)  # Check-in latitude
    check_in_longitude = Column(Float, nullable=True)  # Check-in longitude
    check_in_location_accuracy = Column(Float, nullable=True)  # Check-in location accuracy in meters
    check_out_latitude = Column(Float, nullable=True)  # Check-out latitude
    check_out_longitude = Column(Float, nullable=True)  # Check-out longitude
    check_out_location_accuracy = Column(Float, nullable=True)  # Check-out location accuracy in meters
    
    # Relationship - passive_deletes tells SQLAlchemy to let the database handle CASCADE
    person = relationship('Person', backref='attendance_records', passive_deletes=True)
    
    # Composite index for fast date + person queries
    __table_args__ = (
        Index('idx_attendance_date_person', 'date', 'person_id'),
        Index('idx_attendance_date', 'date'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'marked_at': self.marked_at.isoformat() if self.marked_at else None,
            'check_in_time': self.check_in_time.isoformat() if self.check_in_time else None,
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'check_in_location': {
                'latitude': self.check_in_latitude,
                'longitude': self.check_in_longitude,
                'accuracy': self.check_in_location_accuracy
            } if self.check_in_latitude and self.check_in_longitude else None,
            'check_out_location': {
                'latitude': self.check_out_latitude,
                'longitude': self.check_out_longitude,
                'accuracy': self.check_out_location_accuracy
            } if self.check_out_latitude and self.check_out_longitude else None
        }


class AnalyticsLog(Base, TimestampMixin):
    """Analytics log table for tracking system events"""
    __tablename__ = 'analytics_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False, index=True)  # 'registration', 'check_in', 'check_out'
    person_id = Column(Integer, ForeignKey('persons.id', ondelete='CASCADE'), nullable=True, index=True)
    emp_id = Column(String(100), nullable=True, index=True)
    name = Column(String(255), nullable=True)
    region = Column(String(50), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: TimestampMixin._get_ist_now(), index=True)
    date = Column(Date, nullable=False, index=True)
    event_metadata = Column(JSON, nullable=True)  # Additional data as JSON (renamed from 'metadata' to avoid SQLAlchemy conflict)
    
    # Relationship
    person = relationship('Person', backref='analytics_logs', passive_deletes=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_analytics_log_date_event', 'date', 'event_type'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'person_id': self.person_id,
            'emp_id': self.emp_id,
            'name': self.name,
            'region': self.region,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'date': self.date.isoformat() if self.date else None,
            'metadata': self.event_metadata  # Return as 'metadata' in dict for API compatibility
        }


class FaceEncoding(Base, TimestampMixin):
    """Face encoding table using pgvector for similarity search"""
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, ForeignKey('persons.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # Vector embedding (512 dimensions for InsightFace)
    embedding = Column(Vector(512), nullable=False)
    
    # Metadata
    image_path = Column(String(500), nullable=True)
    image_data = Column(LargeBinary, nullable=True)  # Store actual image
    face_bbox = Column(String(100), nullable=True)  # [x1, y1, x2, y2]
    confidence = Column(Float, default=0.0)
    quality_score = Column(Float, default=0.0)
    
    # Relationship
    person = relationship('Person', back_populates='face_encodings')
    
    # HNSW index for ultra-fast vector similarity search
    __table_args__ = (
        Index('idx_embedding_hnsw', 'embedding', 
              postgresql_using='hnsw', 
              postgresql_with={'m': 16, 'ef_construction': 64}, 
              postgresql_ops={'embedding': 'vector_cosine_ops'}),
    )
    
    def __repr__(self):
        return f"<FaceEncoding(id={self.id}, person_id={self.person_id})>"
    
    def get_encoding(self) -> np.ndarray:
        """Get embedding as numpy array"""
        if isinstance(self.embedding, np.ndarray):
            return self.embedding
        # pgvector returns list, convert to numpy
        return np.array(self.embedding, dtype=np.float32)
    
    def set_encoding(self, encoding_array: np.ndarray) -> None:
        """Set face feature vector (for compatibility)"""
        if not isinstance(encoding_array, np.ndarray):
            raise ValueError("encoding_array must be a numpy array")
        # Convert to list for pgvector
        self.embedding = encoding_array.tolist()
    
    def get_image_data(self) -> Optional[bytes]:
        """Get stored image data"""
        return self.image_data
    
    def set_image_data(self, image_data: bytes) -> None:
        """Set image data"""
        self.image_data = image_data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'person_id': self.person_id,
            'image_path': self.image_path,
            'face_bbox': self.face_bbox,
            'confidence': self.confidence,
            'quality_score': self.quality_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_image_data': self.image_data is not None
        }


# ==================== Database Manager ====================

class DatabaseManager:
    """Database manager for PostgreSQL + pgvector"""
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_url: PostgreSQL connection URL. If None, reads from config.
        """
        if db_url is None:
            db_url = config.get('database.url', 'postgresql://postgres:postgres@localhost:5432/face_recognition')
        
        self.db_url = db_url
        
        # Create engine with connection pooling
        pool_size = config.get('database.pool_size', 20)
        max_overflow = config.get('database.max_overflow', 40)
        pool_timeout = config.get('database.pool_timeout', 30)
        pool_recycle = config.get('database.pool_recycle', 3600)
        
        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=False  # Set to True for SQL debugging
        )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"PostgreSQL connection established: {db_url.split('@')[1] if '@' in db_url else 'localhost'}")
        
        # Create tables and enable pgvector
        self._initialize_database()
    
    def _initialize_database(self):
        """Create tables and enable pgvector extension"""
        try:
            # Enable pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                logger.info("✓ pgvector extension enabled")
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("✓ Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== Person Methods ====================
    
    def create_person(self, name: str, region: str, emp_id: str, emp_rank: str,
                     description: Optional[str] = None, client_id: Optional[str] = None) -> Person:
        """
        Create a new person
        
        Args:
            name: Person's name
            region: Region identifier (ka, ap, tn)
            emp_id: Employee ID (unique)
            emp_rank: Employee rank/position
            description: Optional description
            client_id: Optional client identifier for multi-tenant
        
        Returns:
            Person object
        """
        with self.get_session() as session:
            person = Person(
                name=name,
                region=region,
                emp_id=emp_id,
                emp_rank=emp_rank,
                description=description,
                client_id=client_id
            )
            session.add(person)
            session.flush()
            session.refresh(person)
            
            # Capture values before session closes
            person_id = person.id
            person_name = person.name
            person_region = person.region
            person_emp_id = person.emp_id
            person_emp_rank = person.emp_rank
            person_description = person.description
            person_client_id = person.client_id
            person_created_at = person.created_at
            person_updated_at = person.updated_at
            
            logger.info(f"Created person: {name} (Emp ID: {emp_id}) in region {region} (DB ID: {person_id})")
        
        # Return a detached copy with all attributes set
        detached_person = Person(
            id=person_id,
            name=person_name,
            region=person_region,
            emp_id=person_emp_id,
            emp_rank=person_emp_rank,
            description=person_description,
            client_id=person_client_id
        )
        detached_person.created_at = person_created_at
        detached_person.updated_at = person_updated_at
        return detached_person
    
    def get_person_by_name(self, name: str, region: Optional[str] = None, 
                          client_id: Optional[str] = None) -> Optional[Person]:
        """Get person by name, optionally filtered by region and client"""
        with self.get_session() as session:
            query = session.query(Person).filter(Person.name == name)
            
            if region:
                query = query.filter(Person.region == region)
            if client_id:
                query = query.filter(Person.client_id == client_id)
            
            person = query.first()
            if person:
                session.expunge(person)  # Detach from session
            return person
    
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """Get person by ID"""
        with self.get_session() as session:
            person = session.query(Person).filter(Person.id == person_id).first()
            if person:
                session.expunge(person)
            return person
    
    def get_all_persons(self, region: Optional[str] = None, client_id: Optional[str] = None) -> List[Person]:
        """Get all persons, optionally filtered by region and client"""
        with self.get_session() as session:
            query = session.query(Person)
            
            if region:
                query = query.filter(Person.region == region)
            if client_id:
                query = query.filter(Person.client_id == client_id)
            
            persons = query.order_by(Person.created_at.desc()).all()
            for person in persons:
                session.expunge(person)
            return persons
    
    
    def delete_person(self, person_id: int) -> bool:
        """Delete person and all their face encodings and attendance records"""
        with self.get_session() as session:
            # Use raw SQL to avoid ORM relationship issues
            # Delete attendance records first
            session.execute(text("DELETE FROM attendance WHERE person_id = :pid"), {"pid": person_id})
            # Delete face encodings
            session.execute(text("DELETE FROM face_encodings WHERE person_id = :pid"), {"pid": person_id})
            # Delete person
            result = session.execute(text("DELETE FROM persons WHERE id = :pid"), {"pid": person_id})
            
            if result.rowcount > 0:
                logger.info(f"Deleted person ID {person_id} and all related records")
                return True
            return False
    
    # ==================== Face Encoding Methods ====================
    
    def add_face_encoding(self, person_id: int, encoding: np.ndarray, 
                         image_path: Optional[str] = None,
                         image_data: Optional[bytes] = None,
                         face_bbox: Optional[str] = None,
                         confidence: float = 0.0,
                         quality_score: float = 0.0) -> FaceEncoding:
        """
        Add face encoding with vector embedding
        
        Args:
            person_id: Person ID
            encoding: Face embedding vector (numpy array)
            image_path: Optional image path
            image_data: Optional raw image data
            face_bbox: Optional bounding box string
            confidence: Detection confidence
            quality_score: Quality score
        
        Returns:
            FaceEncoding object
        """
        with self.get_session() as session:
            # Convert numpy array to list for pgvector
            embedding_list = encoding.tolist() if isinstance(encoding, np.ndarray) else encoding
            
            face_encoding = FaceEncoding(
                person_id=person_id,
                embedding=embedding_list,
                image_path=image_path,
                image_data=image_data,
                face_bbox=face_bbox,
                confidence=confidence,
                quality_score=quality_score
            )
            session.add(face_encoding)
            session.flush()
            session.refresh(face_encoding)
            logger.info(f"Added face encoding for person_id={person_id}")
            session.expunge(face_encoding)
            return face_encoding
    
    # ==================== Vector Search Method (MAIN FEATURE) ====================
    
    def find_similar_faces(self, embedding: np.ndarray, region: str, 
                          emp_id: Optional[str] = None,
                          client_id: Optional[str] = None,
                          threshold: float = 0.3,
                          limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find similar faces using pgvector cosine similarity
        **This is the key method that replaces Python loop matching**
        
        Args:
            embedding: Query face embedding
            region: Region to search in (A, B, C, etc.)
            emp_id: Optional employee ID for targeted search (only search this person)
            client_id: Optional client filter
            threshold: Similarity threshold (0-1)
            limit: Maximum results to return
        
        Returns:
            List of matches with person info and similarity scores
        """
        with self.get_session() as session:
            # Convert embedding to list for pgvector
            embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
            
            # Build query with region filtering + vector similarity
            query = session.query(
                FaceEncoding,
                Person,
                FaceEncoding.embedding.cosine_distance(embedding_list).label('distance')
            ).join(Person, FaceEncoding.person_id == Person.id)
            
            # Filter by region (always required)
            query = query.filter(Person.region == region)
            
            # Optional emp_id filter (targeted search)
            if emp_id:
                query = query.filter(Person.emp_id == emp_id)
            
            # Optional client filter
            if client_id:
                query = query.filter(Person.client_id == client_id)
            
            # Calculate similarity (1 - cosine_distance) and filter
            # pgvector cosine_distance returns 0-2, where 0 = identical
            # We want similarity > threshold, so distance < (1 - threshold)
            max_distance = 1.0 - threshold
            query = query.filter(FaceEncoding.embedding.cosine_distance(embedding_list) < max_distance)
            
            # Order by similarity (smallest distance = highest similarity)
            query = query.order_by('distance').limit(limit)
            
            results = []
            for face_encoding, person, distance in query.all():
                similarity = 1.0 - distance  # Convert distance back to similarity
                results.append({
                    'emp_id': person.emp_id,
                    'name': person.name,
                    'region': person.region,
                    'match_score': similarity * 100,  # Percentage
                    'distance': float(distance),
                    'face_encoding_id': face_encoding.id,
                    'quality': face_encoding.quality_score,
                    'confidence': face_encoding.confidence
                })
            
            search_scope = f"emp_id '{emp_id}'" if emp_id else f"region '{region}'"
            logger.info(f"Found {len(results)} matches in {search_scope} above threshold {threshold}")
            return results
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_session() as session:
            total_persons = session.query(Person).count()
            total_encodings = session.query(FaceEncoding).count()
            
            # Count by region
            region_counts = {}
            regions = session.query(Person.region).distinct().all()
            for (region,) in regions:
                count = session.query(Person).filter(Person.region == region).count()
                region_counts[region] = count
            
            return {
                'total_persons': total_persons,
                'total_encodings': total_encodings,
                'avg_photos_per_person': round(total_encodings / total_persons, 1) if total_persons > 0 else 0,
                'region_counts': region_counts
            }
    
    # ==================== Backward Compatibility Methods ====================
    
    def get_face_encodings(self, person_id: Optional[int] = None) -> List[FaceEncoding]:
        """Get face encodings (backward compatible)"""
        with self.get_session() as session:
            if person_id is not None:
                encodings = session.query(FaceEncoding).filter(FaceEncoding.person_id == person_id).all()
            else:
                encodings = session.query(FaceEncoding).all()
            
            for encoding in encodings:
                session.expunge(encoding)
            return encodings
    
    def get_face_encodings_by_person(self, person_id: int) -> List[FaceEncoding]:
        """Get face encodings by person ID"""
        return self.get_face_encodings(person_id=person_id)
    
    def get_face_encoding_by_id(self, encoding_id: int) -> Optional[FaceEncoding]:
        """Get face encoding by ID"""
        with self.get_session() as session:
            encoding = session.query(FaceEncoding).filter(FaceEncoding.id == encoding_id).first()
            if encoding:
                session.expunge(encoding)
            return encoding
    
    def get_face_encoding_repository(self, session):
        """Get face encoding repository (for backward compatibility)"""
        # This is a simple wrapper that returns self since we have the methods directly
        return self
    
    def delete_face_encoding(self, encoding_id: int) -> bool:
        """Delete a face encoding by ID"""
        with self.get_session() as session:
            encoding = session.query(FaceEncoding).filter(FaceEncoding.id == encoding_id).first()
            if encoding:
                session.delete(encoding)
                logger.info(f"Deleted face encoding ID {encoding_id}")
                return True
            return False
    
    def get_all_encodings_with_persons(self) -> List[Tuple[Person, FaceEncoding]]:
        """Get all encodings with person info (backward compatible)"""
        with self.get_session() as session:
            results = session.query(Person, FaceEncoding).join(
                FaceEncoding, Person.id == FaceEncoding.person_id
            ).all()
            
            detached_results = []
            for person, encoding in results:
                session.expunge(person)
                session.expunge(encoding)
                detached_results.append((person, encoding))
            
            return detached_results
    
    # ==================== Attendance Methods ====================
    
    def mark_attendance(self, person_id: int, date: Optional[datetime] = None, status: str = 'present') -> 'Attendance':
        """Mark attendance for a person"""
        import pytz
        ist = pytz.timezone('Asia/Kolkata')
        
        if date is None:
            date = datetime.now(ist).replace(hour=0, minute=0, second=0, microsecond=0)
        
        with self.get_session() as session:
            # Check if attendance already exists for this person on this date
            existing = session.query(Attendance).filter(
                Attendance.person_id == person_id,
                Attendance.date == date
            ).first()
            
            if existing:
                # Update existing attendance
                existing.status = status
                existing.marked_at = datetime.now(ist)
                session.flush()
                session.refresh(existing)
                session.expunge(existing)
                logger.info(f"Updated attendance for person_id={person_id} on {date.date()}")
                return existing
            else:
                # Create new attendance record
                attendance = Attendance(
                    person_id=person_id,
                    date=date,
                    status=status,
                    marked_at=datetime.now(ist)
                )
                session.add(attendance)
                session.flush()
                session.refresh(attendance)
                session.expunge(attendance)
                logger.info(f"Marked attendance for person_id={person_id} on {date.date()}")
                return attendance
    
    def get_attendance_by_date(self, date: datetime, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get attendance records for a specific date with person details"""
        with self.get_session() as session:
            query = session.query(Attendance, Person).join(
                Person, Attendance.person_id == Person.id
            ).filter(Attendance.date == date)
            
            if region:
                query = query.filter(Person.region == region)
            
            results = []
            for attendance, person in query.all():
                results.append({
                    'attendance_id': attendance.id,
                    'person_id': person.id,
                    'name': person.name,
                    'emp_id': person.emp_id,
                    'emp_rank': person.emp_rank,
                    'region': person.region,
                    'status': attendance.status,
                    'marked_at': attendance.marked_at.isoformat() if attendance.marked_at else None,
                    'date': attendance.date.isoformat() if attendance.date else None
                })
            
            return results
    
    def get_all_persons_with_attendance(self, date: datetime, region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all persons with their attendance status for a specific date"""
        with self.get_session() as session:
            # Get all persons in the region
            query = session.query(Person)
            if region:
                query = query.filter(Person.region == region)
            
            persons = query.all()
            
            results = []
            for person in persons:
                # Check if attendance exists for this person on this date
                attendance = session.query(Attendance).filter(
                    Attendance.person_id == person.id,
                    Attendance.date == date
                ).first()
                
                results.append({
                    'person_id': person.id,
                    'name': person.name,
                    'emp_id': person.emp_id,
                    'emp_rank': person.emp_rank,
                    'region': person.region,
                    'status': attendance.status if attendance else 'absent',
                    'marked_at': attendance.marked_at.isoformat() if attendance and attendance.marked_at else None,
                    'check_in_time': attendance.check_in_time.isoformat() if attendance and attendance.check_in_time else None,
                    'check_out_time': attendance.check_out_time.isoformat() if attendance and attendance.check_out_time else None,
                    'attendance_id': attendance.id if attendance else None,
                    'date': date.isoformat()
                })
            
            return results
    
    # ==================== Analytics Logging ====================
    
    def log_event(self, event_type: str, person_id: Optional[int] = None, emp_id: Optional[str] = None, 
                  name: Optional[str] = None, region: Optional[str] = None, metadata: Optional[dict] = None) -> Dict[str, Any]:
        """
        Log an analytics event
        
        Args:
            event_type: Type of event ('registration', 'check_in', 'check_out', etc.)
            person_id: Person ID (optional)
            emp_id: Employee ID (optional)
            name: Person name (optional)
            region: Region (optional)
            metadata: Additional data as dictionary (optional)
        """
        try:
            import pytz
            ist = pytz.timezone('Asia/Kolkata')
            now_ist = datetime.now(ist)
            
            with self.get_session() as session:
                log_entry = AnalyticsLog(
                    event_type=event_type,
                    person_id=person_id,
                    emp_id=emp_id,
                    name=name,
                    region=region,
                    timestamp=now_ist,
                    date=now_ist.date(),
                    event_metadata=metadata  # Use event_metadata instead of metadata
                )
                session.add(log_entry)
                session.flush()
                log_id = log_entry.id
                session.commit()
                
            logger.info(f"✅ Analytics event logged: {event_type} for {name} (ID: {log_id})")
            # Return a simple dict instead of the object
            return {'id': log_id, 'event_type': event_type}
        except Exception as e:
            logger.error(f"❌ Failed to log analytics event: {e}")
            raise
    
    def get_analytics_summary(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, 
                             region: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics summary for a date range
        
        Returns counts of registrations, check-ins, and check-outs
        """
        with self.get_session() as session:
            query = session.query(AnalyticsLog)
            
            if start_date:
                query = query.filter(AnalyticsLog.date >= start_date.date())
            if end_date:
                query = query.filter(AnalyticsLog.date <= end_date.date())
            if region:
                query = query.filter(AnalyticsLog.region == region)
            
            all_logs = query.all()
            
            # Count by event type
            registrations = len([log for log in all_logs if log.event_type == 'registration'])
            check_ins = len([log for log in all_logs if log.event_type == 'check_in'])
            check_outs = len([log for log in all_logs if log.event_type == 'check_out'])
            
            # Get daily breakdown
            daily_stats = {}
            for log in all_logs:
                date_str = log.date.isoformat()
                if date_str not in daily_stats:
                    daily_stats[date_str] = {'registrations': 0, 'check_ins': 0, 'check_outs': 0}
                
                if log.event_type == 'registration':
                    daily_stats[date_str]['registrations'] += 1
                elif log.event_type == 'check_in':
                    daily_stats[date_str]['check_ins'] += 1
                elif log.event_type == 'check_out':
                    daily_stats[date_str]['check_outs'] += 1
            
            return {
                'total_registrations': registrations,
                'total_check_ins': check_ins,
                'total_check_outs': check_outs,
                'daily_stats': daily_stats,
                'date_range': {
                    'start': start_date.isoformat() if start_date else None,
                    'end': end_date.isoformat() if end_date else None
                },
                'region': region
            }
    
    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None, 
                         region: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent analytics events"""
        with self.get_session() as session:
            query = session.query(AnalyticsLog).order_by(AnalyticsLog.timestamp.desc())
            
            if event_type:
                query = query.filter(AnalyticsLog.event_type == event_type)
            if region:
                query = query.filter(AnalyticsLog.region == region)
            
            logs = query.limit(limit).all()
            return [log.to_dict() for log in logs]


# ==================== Global Singleton ====================

# Global database manager instance
_database_manager = None

# Backward compatibility alias
OptimizedDatabaseManager = DatabaseManager

def get_database_manager() -> DatabaseManager:
    """Get singleton database manager instance"""
    global _database_manager
    if _database_manager is None:
        _database_manager = DatabaseManager()
    return _database_manager
