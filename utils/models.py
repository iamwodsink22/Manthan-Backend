from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime,UUID, Index,select
import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base,relationship
from sqlalchemy.ext.hybrid import hybrid_property
import datetime

Base = declarative_base()
class StudentGrades(Base):
    __tablename__='StudentGrades'
    id=Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    student_id=Column(ForeignKey("Students.id"),unique=True,nullable=False)
    first_exam = Column(Float, nullable=True)
    second_exam = Column(Float, nullable=True)
    third_exam = Column(Float, nullable=True)
    fourth_exam = Column(Float, nullable=True)
    student = relationship("Student", back_populates="student_grades")
class Student(Base):
    __tablename__ = "Students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    img=Column(String,nullable=True)
    grade = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    roll_no = Column(Integer, nullable=False)
    address = Column(String, nullable=False,default=0.0)
    avg_grades=Column(Float,nullable=True)
    behavioral = Column(Float, nullable=False)
    attendance = Column(Float, nullable=False)
    extracurricular = Column(Float, nullable=False)
    parent_name = Column(String, nullable=False)
    parent_phone = Column(String, nullable=False)
    parent_email = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    search_vector = Column(TSVECTOR, nullable=True)
    student_grades = relationship("StudentGrades", back_populates="student",uselist=False)
    __table_args__ = (
        Index("search_idx", "search_vector", postgresql_using="gin"),  # Ensure index exists
    )
    
    
class StudentPredctions(Base):
    __tablename__='StudentPredictions'
    id=Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    student_id=Column(ForeignKey(Student.id),unique=True,nullable=False)
    cluster=Column(String(50),nullable=True)
    risk=Column(Boolean,nullable=True)
    summary=Column(String(200),nullable=True)
    risk_explanation=Column(String(500),nullable=True)
    created_at=Column(DateTime,server_default=func.now(),nullable=True)
    

    
    
    
    
    
DATABASE_URL = "postgresql://postgres:Puri%40222@localhost:5433/manthan"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


