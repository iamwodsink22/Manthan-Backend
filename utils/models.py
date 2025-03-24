from sqlalchemy import Column, Integer, String, Float, ARRAY,ForeignKey, Boolean, DateTime,UUID, Index,select, UniqueConstraint
import uuid
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, declarative_base,relationship
from sqlalchemy.ext.hybrid import hybrid_property
import datetime
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
import uuid

Base = declarative_base()
    
class Subject(Base):
    __tablename__ = 'Subjects'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade = Column(Integer, nullable=False) 
    name = Column(String, nullable=False)    
    __table_args__ = (
        UniqueConstraint('grade', 'name', name='uq_subject_grade_name'),
        
    )
    
class ExamScore(Base):
    __tablename__ = 'ExamScores'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(ForeignKey("Students.id"), nullable=False)
    subject_id = Column(ForeignKey("Subjects.id"), nullable=False)
    exam_number = Column(Integer, nullable=False)  # 1, 2, 3, or 4
    score = Column(Float, nullable=False)
    
    student = relationship("Student", back_populates="exam_scores")
    subject = relationship("Subject")
    
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', 'exam_number', name='uq_student_subject_exam'),
    )
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
    exam_scores = relationship("ExamScore", back_populates="student")
    __table_args__ = (
        Index("search_idx", "search_vector", postgresql_using="gin"),  # Ensure index exists
    )
    
    
class StudentPredctions(Base):
    __tablename__='StudentPredictions'
    id=Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    student_id=Column(ForeignKey(Student.id),unique=True,nullable=False)
    cluster=Column(String(50),nullable=True)
    risk=Column(Boolean,nullable=True)
    summary=Column(String(500),nullable=True)
    risk_explanation=Column(String(500),nullable=True)
    created_at=Column(DateTime,server_default=func.now(),nullable=True)
    
class SubjectAnalysis(Base):
    __tablename__='SubjectAnalysis'
    id=Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    student_id=Column(ForeignKey(Student.id),nullable=False)
    subject_id = Column(ForeignKey("Subjects.id"), nullable=False)
    marks=Column(String(100),nullable=True)
    analysis=Column(String(50),nullable=True)
    subject = relationship("Subject")
    __table_args__ = (
        UniqueConstraint('student_id', 'subject_id', name='uq_student_subject'),
    )
    
    
class User(Base):
    __tablename__='User'
    id=Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    name=Column(String(50),nullable=True)
    email=Column(String(50),nullable=False)
    password=Column(String(100),nullable=False)
    college=Column(String(100),nullable=False)
    super_admin=Column(Boolean,nullable=True,default=False)
    
    


class SectionAverage(Base):
    __tablename__ = 'SectionAverages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade = Column(Integer, nullable=False)
    section = Column(String, nullable=False)
    avg_grades = Column(Float, nullable=True)
    avg_attendance = Column(Float, nullable=True)
    avg_behavioral = Column(Float, nullable=True)
    avg_extracurricular = Column(Float, nullable=True)
    created_at = Column(DateTime)

    subject_averages = relationship("SubjectAverage", backref=None)

    __table_args__ = (
        UniqueConstraint('grade', 'section', name='uq_section_grade'),
    )


class SubjectAverage(Base):
    __tablename__ = 'SubjectAverages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_average_id = Column(UUID(as_uuid=True), ForeignKey('SectionAverages.id'), nullable=False) 
    subject_id = Column(ForeignKey('Subjects.id'), nullable=False)
    avg_marks = Column(ARRAY(Float), nullable=False) 
    section_average = relationship("SectionAverage",backref='subject_averages_rel') 
    subject = relationship("Subject")

    
    
    
    
DATABASE_URL = "postgresql://postgres:Puri%40222@localhost:5433/manthan"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


