"""
优化后的数据库模型
采用Repository模式和数据库连接池优化
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


# ==================== 数据库模型 ====================

class TimestampMixin:
    """时间戳混入类"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class Person(Base, TimestampMixin):
    """
    优化后的人员信息表
    - 添加了索引优化查询性能
    - 增加了数据验证
    """
    __tablename__ = 'persons'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)  # 添加索引
    description = Column(String(500))
    
    # 添加索引以优化查询
    __table_args__ = (
        Index('idx_person_name_created', 'name', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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
    优化后的人脸特征向量表
    - 改进了数据存储方式
    - 添加了更多的索引
    """
    __tablename__ = 'face_encodings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, nullable=False, index=True)  # 外键索引
    encoding = Column(LargeBinary, nullable=False)  # 序列化的特征向量
    image_path = Column(String(500))
    image_data = Column(LargeBinary)  # 图片二进制数据
    face_bbox = Column(String(200))  # 人脸边界框 [x1,y1,x2,y2]
    confidence = Column(Float, default=1.0, nullable=False)
    quality_score = Column(Float, default=1.0, nullable=False)
    
    # 添加复合索引优化查询
    __table_args__ = (
        Index('idx_face_person_quality', 'person_id', 'quality_score'),
        Index('idx_face_created', 'created_at'),
    )
    
    def set_encoding(self, encoding_array: np.ndarray) -> None:
        """设置人脸特征向量"""
        if not isinstance(encoding_array, np.ndarray):
            raise ValueError("encoding_array must be a numpy array")
        self.encoding = pickle.dumps(encoding_array.astype(np.float32))
    
    def get_encoding(self) -> np.ndarray:
        """获取人脸特征向量"""
        try:
            return pickle.loads(self.encoding)
        except Exception as e:
            logger.error(f"解析人脸特征向量失败: {e}")
            raise ValueError(f"Invalid encoding data: {e}")
    
    def set_image_data(self, image_binary: bytes) -> None:
        """设置图片二进制数据"""
        if not isinstance(image_binary, bytes):
            raise ValueError("image_binary must be bytes")
        self.image_data = image_binary
    
    def get_image_data(self) -> Optional[bytes]:
        """获取图片二进制数据"""
        return self.image_data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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

# ==================== Repository 接口 ====================

class BaseRepository(ABC):
    """基础仓库接口"""
    
    def __init__(self, session: Session):
        self.session = session
    
    @abstractmethod
    def create(self, **kwargs):
        """创建实体"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int):
        """根据ID获取实体"""
        pass
    
    @abstractmethod
    def update(self, entity_id: int, **kwargs):
        """更新实体"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int):
        """删除实体"""
        pass


class PersonRepository(BaseRepository):
    """人员仓库"""
    
    def create(self, name: str, description: Optional[str] = None) -> Person:
        """创建人员"""
        person = Person(name=name.strip(), description=description)
        self.session.add(person)
        self.session.flush()  # 获取ID但不提交
        return person
    
    def get_by_id(self, person_id: int) -> Optional[Person]:
        """根据ID获取人员"""
        return self.session.query(Person).filter_by(id=person_id).first()
    
    def get_by_name(self, name: str) -> Optional[Person]:
        """根据姓名获取人员"""
        return self.session.query(Person).filter_by(name=name.strip()).first()
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[Person]:
        """获取所有人员"""
        query = self.session.query(Person).order_by(Person.created_at.desc())
        if limit:
            query = query.limit(limit).offset(offset)
        return query.all()
    
    def search_by_name(self, name_pattern: str, limit: int = 50) -> List[Person]:
        """按姓名模糊搜索"""
        return (self.session.query(Person)
                .filter(Person.name.like(f'%{name_pattern}%'))
                .order_by(Person.name)
                .limit(limit)
                .all())
    
    def update(self, person_id: int, name: Optional[str] = None, 
               description: Optional[str] = None) -> Optional[Person]:
        """更新人员信息"""
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
        """删除人员"""
        person = self.get_by_id(person_id)
        if person:
            self.session.delete(person)
            return True
        return False
    
    def count(self) -> int:
        """获取人员总数"""
        return self.session.query(Person).count()


class FaceEncodingRepository(BaseRepository):
    """人脸编码仓库"""
    
    def create(self, person_id: int, encoding: np.ndarray, 
               image_path: Optional[str] = None, image_data: Optional[bytes] = None,
               face_bbox: Optional[str] = None, confidence: float = 1.0,
               quality_score: float = 1.0) -> FaceEncoding:
        """创建人脸编码"""
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
        """根据ID获取人脸编码"""
        return self.session.query(FaceEncoding).filter_by(id=encoding_id).first()
    
    def get_by_person_id(self, person_id: int) -> List[FaceEncoding]:
        """获取指定人员的所有人脸编码"""
        return (self.session.query(FaceEncoding)
                .filter_by(person_id=person_id)
                .order_by(FaceEncoding.quality_score.desc())
                .all())
    
    def get_all_encodings(self) -> List[Tuple[FaceEncoding, Person]]:
        """获取所有编码及对应人员信息"""
        return (self.session.query(FaceEncoding, Person)
                .join(Person, FaceEncoding.person_id == Person.id)
                .order_by(FaceEncoding.created_at.desc())
                .all())
    
    def update(self, encoding_id: int, **kwargs) -> Optional[FaceEncoding]:
        """更新人脸编码"""
        encoding = self.get_by_id(encoding_id)
        if not encoding:
            return None
        
        for key, value in kwargs.items():
            if hasattr(encoding, key):
                setattr(encoding, key, value)
        
        return encoding
    
    def delete(self, encoding_id: int) -> bool:
        """删除人脸编码"""
        encoding = self.get_by_id(encoding_id)
        if encoding:
            self.session.delete(encoding)
            return True
        return False
    
    def delete_by_person_id(self, person_id: int) -> int:
        """删除指定人员的所有人脸编码"""
        deleted_count = (self.session.query(FaceEncoding)
                        .filter_by(person_id=person_id)
                        .delete())
        return deleted_count
    
    def count(self) -> int:
        """获取编码总数"""
        return self.session.query(FaceEncoding).count()
    
    def count_by_person_id(self, person_id: int) -> int:
        """获取指定人员的编码数量"""
        return self.session.query(FaceEncoding).filter_by(person_id=person_id).count()


# ==================== 优化的数据库管理器 ====================

class OptimizedDatabaseManager:
    """
    优化的数据库管理器
    
    特性:
    - 连接池管理
    - Repository 模式
    - 事务管理
    - 错误处理
    - 性能监控
    """
    
    def __init__(self, db_path: str = "data/database/face_recognition.db", 
                 pool_size: int = 5, max_overflow: int = 10):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
            pool_size: 连接池大小
            max_overflow: 最大溢出连接数
        """
        self.db_path = Path(db_path)
        self._ensure_db_directory()
        
        # 创建引擎（针对SQLite优化）
        self.engine = create_engine(
            f'sqlite:///{self.db_path}',
            poolclass=StaticPool,
            connect_args={
                'check_same_thread': False,
                'timeout': 30
            },
            echo=False  # 生产环境中设置为False
        )
        
        # 优化SQLite设置
        self._optimize_sqlite()
        
        # 创建表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.SessionLocal = scoped_session(
            sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        )
        
        logger.info(f"数据库初始化完成: {self.db_path}")
    
    def _ensure_db_directory(self):
        """确保数据库目录存在"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _optimize_sqlite(self):
        """优化SQLite设置"""
        with self.engine.connect() as conn:
            # 设置SQLite优化参数
            conn.execute(text("PRAGMA journal_mode=WAL"))  # 写前日志模式
            conn.execute(text("PRAGMA synchronous=NORMAL"))  # 平衡性能和安全
            conn.execute(text("PRAGMA cache_size=10000"))  # 增加缓存
            conn.execute(text("PRAGMA temp_store=MEMORY"))  # 临时存储在内存
            conn.execute(text("PRAGMA mmap_size=268435456"))  # 256MB内存映射
    
    
    @contextmanager
    def get_session(self):
        """获取数据库会话（上下文管理器）"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    def get_person_repository(self, session: Session) -> PersonRepository:
        """获取人员仓库"""
        return PersonRepository(session)
    
    def get_face_encoding_repository(self, session: Session) -> FaceEncodingRepository:
        """获取人脸编码仓库"""
        return FaceEncodingRepository(session)
    
    # ==================== 便捷方法（向后兼容） ====================
    
    def create_person(self, name: str, description: Optional[str] = None) -> Person:
        """创建人员"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.create(name, description)
            # 手动刷新以获取ID，并返回可独立使用的对象
            session.commit()
            session.refresh(person)
            # 创建一个新的独立对象以避免Session绑定问题
            return Person(
                id=person.id,
                name=person.name,
                description=person.description,
                created_at=person.created_at,
                updated_at=person.updated_at
            )
    
    def get_person_by_name(self, name: str) -> Optional[Person]:
        """根据姓名获取人员"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.get_by_name(name)
            if person:
                # 创建Session-independent对象
                from sqlalchemy.orm import make_transient
                session.expunge(person)
                make_transient(person)
                return person
            return None
    
    def get_person_by_id(self, person_id: int) -> Optional[Person]:
        """根据ID获取人员"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            person = repo.get_by_id(person_id)
            if person:
                # 创建Session-independent对象
                from sqlalchemy.orm import make_transient
                session.expunge(person)
                make_transient(person)
                return person
            return None
    
    def add_face_encoding(self, person_id: int, encoding: np.ndarray, 
                         image_path: Optional[str] = None, image_data: Optional[bytes] = None,
                         face_bbox: Optional[str] = None, confidence: float = 1.0,
                         quality_score: float = 1.0) -> FaceEncoding:
        """添加人脸编码"""
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
            # 创建一个新的独立对象以避免Session绑定问题
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
        """获取所有人员"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            return repo.get_all()
    
    def delete_person(self, person_id: int) -> bool:
        """删除人员及其所有人脸编码"""
        with self.get_session() as session:
            # 先删除人脸编码
            face_repo = self.get_face_encoding_repository(session)
            face_repo.delete_by_person_id(person_id)
            
            # 再删除人员
            person_repo = self.get_person_repository(session)
            return person_repo.delete(person_id)
    
    def get_statistics(self) -> Dict[str, int]:
        """获取数据库统计信息"""
        with self.get_session() as session:
            person_repo = self.get_person_repository(session)
            face_repo = self.get_face_encoding_repository(session)
            
            return {
                'total_persons': person_repo.count(),
                'total_encodings': face_repo.count()
            }
    
    def cleanup_orphaned_encodings(self) -> int:
        """清理孤立的人脸编码"""
        with self.get_session() as session:
            # 删除没有对应人员的人脸编码
            result = session.execute(text("""
                DELETE FROM face_encodings 
                WHERE person_id NOT IN (SELECT id FROM persons)
            """))
            deleted_count = result.rowcount
            
            if deleted_count > 0:
                logger.info(f"清理了 {deleted_count} 条孤立的人脸编码")
            
            return deleted_count
    
    def vacuum_database(self):
        """压缩数据库（释放空间）"""
        with self.engine.connect() as conn:
            conn.execute(text("VACUUM"))
        logger.info("数据库压缩完成")
    
    # ==================== 向后兼容的方法 ====================
    
    def add_person(self, name: str, description: str = None) -> Person:
        """添加人员（向后兼容）"""
        return self.create_person(name, description)
    
    def get_person(self, person_id: int) -> Optional[Person]:
        """获取人员信息（向后兼容）"""
        return self.get_person_by_id(person_id)
    
    def update_person(self, person_id: int, name: str = None, description: str = None) -> bool:
        """更新人员信息（向后兼容）"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            result = repo.update(person_id, name, description)
            return result is not None
    
    def get_face_encodings(self, person_id: int = None) -> List[FaceEncoding]:
        """获取人脸编码（向后兼容）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            if person_id is not None:
                return repo.get_by_person_id(person_id)
            else:
                # 返回所有编码
                encodings_with_persons = repo.get_all_encodings()
                return [encoding for encoding, person in encodings_with_persons]
    
    def get_face_encodings_by_person(self, person_id: int) -> List[FaceEncoding]:
        """根据人员ID获取人脸编码"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            encodings = repo.get_by_person_id(person_id)
            # 创建独立的对象列表以避免Session绑定问题
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
        """删除人脸编码（向后兼容）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            return repo.delete(encoding_id)
    
    def get_all_encodings_with_persons(self) -> List[Tuple[Person, FaceEncoding]]:
        """获取所有人脸编码及对应的人员信息（向后兼容）"""
        with self.get_session() as session:
            repo = self.get_face_encoding_repository(session)
            encodings_with_persons = repo.get_all_encodings()
            # 调整返回的元组顺序以保持向后兼容
            return [(person, encoding) for encoding, person in encodings_with_persons]
    
    def search_person_by_name(self, name: str) -> List[Person]:
        """按姓名搜索人员（向后兼容）"""
        with self.get_session() as session:
            repo = self.get_person_repository(session)
            return repo.search_by_name(name)
    
    def backup_database(self, backup_path: str) -> bool:
        """备份数据库（向后兼容）"""
        try:
            import shutil
            shutil.copy2(str(self.db_path), backup_path)
            logger.info(f"数据库备份完成: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False
    
    def restore_database(self, backup_path: str) -> bool:
        """从备份恢复数据库（向后兼容）"""
        try:
            import shutil
            shutil.copy2(backup_path, str(self.db_path))
            # 重新初始化引擎
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
            logger.info(f"数据库恢复完成: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            return False


# 向后兼容的全局变量
DatabaseManager = OptimizedDatabaseManager

# 全局数据库管理器实例
_database_manager = None

def get_database_manager() -> OptimizedDatabaseManager:
    """获取数据库管理器单例"""
    global _database_manager
    if _database_manager is None:
        from ..utils.config import config
        _database_manager = OptimizedDatabaseManager(config.DATABASE_PATH)
    return _database_manager
