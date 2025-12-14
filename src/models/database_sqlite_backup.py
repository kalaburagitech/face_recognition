"""
Optimized database model
useRepositorySchema and database connection pool optimization
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, LargeBinary, Float, Index, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship, scoped_session
from sqlalchemy.pool import StaticPool
from datetime import datetime
import pickle
import numpy as np
from typing import List, Optional, Dict, Any, Tuple
from contextlib import contextmanager
import logging
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

Base = declarative_base()


# ==================== Database model ====================

class TimestampMixin:
    """Timestamp mix-in class"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Person(Base, TimestampMixin):
    """
    Optimized personnel information table
    - Added index optimization query performance
    - Added data validation
    """
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)  # Add index
    description = Column(String(500))
    
    # Add indexes to optimize queries
    __table_args__ = (
        Index('idx_person_name_created', 'name', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name='{self.name}')>"


class FaceEncoding(Base, TimestampMixin):
    """
    Optimized face feature vector table
    - Improved data storage
    - More indexes added
    """
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, nullable=False, index=True)  # foreign key index
    encoding = Column(LargeBinary, nullable=False)  # Serialized feature vector
    image_path = Column(String(500))
    image_data = Column(LargeBinary)  # Image binary data
    face_bbox = Column(String(200))  # face bounding box [x1,y1,x2,y2]
    confidence = Column(Float, default=1.0, nullable=False)
    quality_score = Column(Float, default=1.0, nullable=False)
    
    # Add compound index to optimize query
    __table_args__ = (
        Index('idx_face_person_quality', 'person_id', 'quality_score'),
        Index('idx_face_created', 'created_at'),
    )
    
    def set_encoding(self, encoding_array: np.ndarray) -> None:
        """Set face feature vector"""
        if not isinstance(encoding_array, np.ndarray):
            raise ValueError("encoding_array must be a numpy array")
        self.encoding = pickle.dumps(encoding_array.astype(np.float32))
    
    def get_encoding(self) -> np.ndarray:
        """Get face feature vector"""
        try:
            return pickle.loads(self.encoding)
        except Exception as e:
            logger.error(f"Failed to parse face feature vector: {e}")
            raise ValueError(f"Invalid encoding data: {e}")
    
    def set_image_data(self, image_binary: bytes) -> None:
        """Set image binary data"""
        if not isinstance(image_binary, bytes):
            raise ValueError("image_binary must be bytes")
        self.image_data = image_binary
    
    def get_image_data(self) -> Optional[bytes]:
        """Get image binary data"""
        return self.image_data
    
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
            'has_image_data': self.image_data is not None,
            'encoding_size': len(self.encoding) if self.encoding else 0
        }
    
    def __repr__(self) -> str:
        return f"<FaceEncoding(id={self.id}, person_id={self.person_id}, quality={self.quality_score:.2f})>"

# ==================== Repository interface ====================

class BaseRepository(ABC):
    """Basic warehouse interface"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @abstractmethod
    def create(self, **kwargs):
        """Create entity"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int):
        """according toIDGet entity"""
        pass
    
    @abstractmethod
    def update(self, entity_id: int, **kwargs):
        """Update entity"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int):
        """Delete entity"""
        pass


class PersonRepository(BaseRepository):
    """personnel warehouse"""
    
    def create(self, name: str, description: Optional[str] = None) -> Person:
        """Create people"""
        person = Person(name=name.strip(), description=description)
        self.session.add(person)
        self.session.flush()  # GetIDbut don't submit
        return person
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """according toIDGet people"""
        return self.session.query(Person).filter_by(id=person_id).first()
    
    def get_by_name(self, name: str) -> Optional[Person]:
        """Get people by name"""
        return self.session.query(Person).filter_by(name=name.strip()).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Person]:
        """Get all people"""
        query = self.session.query(Person).order_by(Person.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def search_by_name(self, name_pattern: str, limit: int = 50) -> List[Person]:
        """Fuzzy search by name"""
        return (self.session.query(Person)
                .filter(Person.name.like(f'%{name_pattern}%'))
                .order_by(Person.name)
                .limit(limit)
                .all())
    
    def update(self, person_id: int, name: Optional[str] = None, 
               description: Optional[str] = None) -> Optional[Person]:
        """Update personnel information"""
        person = self.get_by_id(person_id)
        if not person:
            return None
        
        if name is not None:
            person.name = name.strip()
        if description is not None:
            person.description = description
        
        person.updated_at = datetime.utcnow()
        return person
    
    def delete(self, person_id: int) -> bool:
        """Delete people"""
        person = self.get_by_id(person_id)
        if person:
            self.session.delete(person)
            return True
        return False
    
    def count(self) -> int:
        """Get the total number of people"""
        return self.session.query(Person).count()


class FaceEncodingRepository(BaseRepository):
    """Face coding warehouse"""
    
    def create(self, person_id: int, encoding: np.ndarray, 
               image_path: Optional[str] = None, image_data: Optional[bytes] = None,
               face_bbox: Optional[str] = None, confidence: float = 1.0,
               quality_score: float = 1.0) -> FaceEncoding:
        """Create face encoding"""
        face_encoding = FaceEncoding(
            person_id=person_id,
            image_path=image_path,
            face_bbox=face_bbox,
            confidence=confidence,
            quality_score=quality_score
        )
        
        face_encoding.set_encoding(encoding)
        if image_data:
            face_encoding.set_image_data(image_data)
        
        self.session.add(face_encoding)
        self.session.flush()
        return face_encoding
    
    def get_by_id(self, encoding_id: int) -> Optional[FaceEncoding]:
        """according toIDGet face code"""
        return self.session.query(FaceEncoding).filter_by(id=encoding_id).first()
    
    def get_by_person_id(self, person_id: int) -> List[FaceEncoding]:
        """Get all face codes of the specified person"""
        return (self.session.query(FaceEncoding)
                .filter_by(person_id=person_id)
                .order_by(FaceEncoding.quality_score.desc())
                .all())
    
    def get_all_encodings(self) -> List[Tuple[FaceEncoding, Person]]:
        """Get all codes and corresponding personnel information"""
        return (self.session.query(FaceEncoding, Person)
                .join(Person, FaceEncoding.person_id == Person.id)
                .order_by(FaceEncoding.created_at.desc())
                .all())
    
    def update(self, encoding_id: int, **kwargs) -> Optional[FaceEncoding]:
        """Update face encoding"""
        encoding = self.get_by_id(encoding_id)
        if not encoding:
            return None
        
        for key, value in kwargs.items():
            if hasattr(encoding, key):
                setattr(encoding, key, value)
        
        return encoding
    
    def delete(self, encoding_id: int) -> bool:
        """Delete face code"""
        encoding = self.get_by_id(encoding_id)
        if encoding:
            self.session.delete(encoding)
            return True
        return False
    
    def delete_by_person_id(self, person_id: int) -> int:
        """Delete all face codes of the specified person"""
        deleted_count = (self.session.query(FaceEncoding)
                        .filter_by(person_id=person_id)
                        .delete())
        return deleted_count
    
    def count(self) -> int:
        """Get the total number of codes"""
        return self.session.query(FaceEncoding).count()
    
    def count_by_person_id(self, person_id: int) -> int:
        """Get the code number of the specified person"""
        return self.session.query(FaceEncoding).filter_by(person_id=person_id).count()


# ==================== Optimized database manager ====================

class OptimizedDatabaseManager:
    """
    Optimized database manager
    
    characteristic:
    - Connection pool management
    - Repository model
    - transaction management
    - Error handling
    - Performance monitoring
    """
    
    def __init__(self, db_path: str = "data/database/face_recognition.db", 
                 pool_size: int = 5, max_overflow: int = 10):
        """
        Initialize the database manager
        
        Args:
            db_path: Database file path
            pool_size: Connection pool size
            max_overflow: Maximum number of overflow connections
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        
        # Create engine（againstSQLiteoptimization）
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            poolclass=StaticPool,
            connect_args={
                'check_same_thread': False,
                'timeout': 30
            },
            echo=False  # In production environment it is set toFalse
        )
        
        # optimizationSQLiteset up
        self._optimize_sqlite()
        
        # Create table
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
        
        logger.info(f"Database initialization completed: {self.db_path}")
    
    def _ensure_db_directory(self):
        """Make sure the database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _optimize_sqlite(self):
        """optimizationSQLiteset up"""
        with self.engine.connect() as conn:
            # set upSQLiteOptimization parameters
            conn.execute(text("PRAGMA journal_mode=WAL"))  # Log before write mode
            conn.execute(text("PRAGMA synchronous=NORMAL"))  # Balance performance and security
            conn.execute(text("PRAGMA cache_size=10000"))  # Increase cache
            conn.execute(text("PRAGMA temp_store=MEMORY"))  # temporarily stored in memory
            conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MBmemory map
    
    
    @contextmanager
    def get_session(self):
        """Get database session（context manager）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            session.close()
    
    def get_person_repository(self, session: Session) -> PersonRepository:
        """Get personnel warehouse"""
        return PersonRepository(session)
    
    def get_face_encoding_repository(self, session: Session) -> FaceEncodingRepository:
        """Get the face coding warehouse"""
        return FaceEncodingRepository(session)
    
    # ==================== Convenience method（backwards compatible） ====================
    
    def create_person(self, name: str, description: Optional[str] = None) -> Person:
        """Create people"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.create(name, description)
            # Refresh manually to getID，and returns an object that can be used independently
            session.commit()
            session.refresh(person)
            # Create a new independent object to avoidSessionBinding problem
            return Person(
                id=person.id,
                name=person.name,
                description=person.description,
                created_at=person.created_at,
                updated_at=person.updated_at
            )
    
    def get_person_by_name(self, name: str) -> Optional[Person]:
        """Get people by name"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.get_by_name(name)
            if person:
                # createSession-independentobject
                from sqlalchemy.orm import make_transient
                session.expunge(person)
                make_transient(person)
                return person
            return None
    
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """according toIDGet people"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.get_by_id(person_id)
            if person:
                # createSession-independentobject
                from sqlalchemy.orm import make_transient
                session.expunge(person)
                make_transient(person)
                return person
            return None
    
    def add_face_encoding(self, person_id: int, encoding: np.ndarray, 
                         image_path: Optional[str] = None, image_data: Optional[bytes] = None,
                         face_bbox: Optional[str] = None, confidence: float = 1.0,
                         quality_score: float = 1.0) -> FaceEncoding:
        """Add face encoding"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            face_encoding = repo.create(
                person_id=person_id,
                encoding=encoding,
                image_path=image_path,
                image_data=image_data,
                face_bbox=face_bbox,
                confidence=confidence,
                quality_score=quality_score
            )
            session.commit()
            session.refresh(face_encoding)
            # Create a new independent object to avoidSessionBinding problem
            return FaceEncoding(
                id=face_encoding.id,
                person_id=face_encoding.person_id,
                encoding=face_encoding.encoding,
                image_path=face_encoding.image_path,
                image_data=face_encoding.image_data,
                face_bbox=face_encoding.face_bbox,
                confidence=face_encoding.confidence,
                quality_score=face_encoding.quality_score,
                created_at=face_encoding.created_at,
                updated_at=face_encoding.updated_at
            )
    
    def get_all_persons(self) -> List[Person]:
        """Get all people"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            return repo.get_all()
    
    def delete_person(self, person_id: int) -> bool:
        """Delete people and all their face codes"""
        with self.get_session() as session:
            # Delete the face encoding first
            face_repo = self.get_face_encoding_repository(session)
            face_repo.delete_by_person_id(person_id)
            
            # Delete people again
            person_repo = self.get_person_repository(session)
            return person_repo.delete(person_id)
    
    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.get_session() as session:
            person_repo = self.get_person_repository(session)
            face_repo = self.get_face_encoding_repository(session)
            
            return {
                'total_persons': person_repo.count(),
                'total_encodings': face_repo.count()
            }
    
    def cleanup_orphaned_encodings(self) -> int:
        """Clean up orphaned face encodings"""
        with self.get_session() as session:
            # Delete face codes that have no corresponding person
            result = session.execute(text("""
                DELETE FROM face_encodings 
                WHERE person_id NOT IN (SELECT id FROM persons)
            """))
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} Isolated face code")
            
            return deleted_count
    
    def vacuum_database(self):
        """Compress database（free up space）"""
        with self.engine.connect() as conn:
            conn.execute(text("VACUUM"))
        logger.info("Database compression completed")
    
    # ==================== backward compatible approach ====================
    
    def add_person(self, name: str, description: str = None) -> Person:
        """Add people（backwards compatible）"""
        return self.create_person(name, description)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        """Get personnel information（backwards compatible）"""
        return self.get_person_by_id(person_id)
    
    def update_person(self, person_id: int, name: str = None, description: str = None) -> bool:
        """Update personnel information（backwards compatible）"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            result = repo.update(person_id, name, description)
            return result is not None
    
    def get_face_encodings(self, person_id: int = None) -> List[FaceEncoding]:
        """Get face code（backwards compatible）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            if person_id is not None:
                return repo.get_by_person_id(person_id)
            else:
                # Return all encodings
                encodings_with_persons = repo.get_all_encodings()
                return [encoding for encoding, person in encodings_with_persons]
    
    def get_face_encodings_by_person(self, person_id: int) -> List[FaceEncoding]:
        """According to personnelIDGet face code"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            encodings = repo.get_by_person_id(person_id)
            # Create separate object lists to avoidSessionBinding problem
            independent_encodings = []
            for encoding in encodings:
                independent_encoding = FaceEncoding(
                    id=encoding.id,
                    person_id=encoding.person_id,
                    encoding=encoding.encoding,
                    image_path=encoding.image_path,
                    image_data=encoding.image_data,
                    face_bbox=encoding.face_bbox,
                    confidence=encoding.confidence,
                    quality_score=encoding.quality_score,
                    created_at=encoding.created_at,
                    updated_at=encoding.updated_at
                )
                independent_encodings.append(independent_encoding)
            return independent_encodings
    
    def delete_face_encoding(self, encoding_id: int) -> bool:
        """Delete face code（backwards compatible）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            return repo.delete(encoding_id)
    
    def get_all_encodings_with_persons(self) -> List[Tuple[Person, FaceEncoding]]:
        """Get all face codes and corresponding person information（backwards compatible）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            encodings_with_persons = repo.get_all_encodings()
            # Adjust returned tuple order to maintain backward compatibility
            return [(person, encoding) for encoding, person in encodings_with_persons]
    
    def search_person_by_name(self, name: str) -> List[Person]:
        """Search people by name（backwards compatible）"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            return repo.search_by_name(name)
    
    def backup_database(self, backup_path: str) -> bool:
        """Back up database（backwards compatible）"""
        try:
            import shutil
            shutil.copy2(str(self.db_path), backup_path)
            logger.info(f"Database backup completed: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup（backwards compatible）"""
        try:
            import shutil
            shutil.copy2(backup_path, str(self.db_path))
            # Reinitialize the engine
            self.engine = create_engine(
                f'sqlite:///{self.db_path}',
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 30
                },
                echo=False
            )
            self.SessionLocal = scoped_session(
                sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            )
            logger.info(f"Database recovery completed: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database recovery failed: {e}")
            return False


# Backwards compatible global variables
DatabaseManager = OptimizedDatabaseManager

# Global database manager instance
_database_manager = None

def get_database_manager() -> OptimizedDatabaseManager:
    """Get the database manager singleton"""
    global _database_manager
    if _database_manager is None:
        from ..utils.config import config
        _database_manager = OptimizedDatabaseManager(config.DATABASE_PATH)
    return _database_manager
