from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime,select,func,desc,asc
from sqlalchemy.orm import relationship
from utils.models import Base, SessionLocal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from utils.models import Student,StudentPredctions,StudentGrades
import json
import uuid
student_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def to_dict(student_obj):
        student_obj,_=student_obj
        student_dict = {'id':str(student_obj.id),'img':student_obj.img,'avg_grades':student_obj.avg_grades,
                        'behavioral':student_obj.behavioral,'extracurricular':student_obj.extracurricular,'attendance':student_obj.attendance,
                        'avg_score':_,'name':student_obj.name}
        
        return student_dict
@student_router.get("/")
def get_student(id:str,db:Session=Depends(get_db)):
    student=db.query(Student).filter(Student.id==id).one()
    predictions=db.query(StudentPredctions).filter(StudentPredctions.student_id==id).one()
    avg_section=db.query(func.avg(Student.avg_grades).label('section_avg_grades'),
                         func.avg(Student.extracurricular).label('section_avg_extracurricular'),
                         func.avg(Student.attendance).label('section_avg_attendance'),
                         func.avg(Student.behavioral).label('section_avg_behavioral'),
                                  ).where(Student.section==student.section).one()
    return_dict={
        'name':student.name,
        'grade':student.grade,
        'section':student.section,
        'attendance':student.attendance,
        'behavioral':student.behavioral,
        'extracurricular':student.extracurricular,
        'avg_grades':student.avg_grades,
        'parent_name':student.parent_name,
        'address':student.address,
        'cluster':predictions.cluster,
        'at_risk':predictions.risk,
        'explanation':predictions.risk_explanation,
        'section_avg_data':[avg_section.section_avg_grades,avg_section.section_avg_attendance,avg_section.section_avg_behavioral,avg_section.section_avg_extracurricular]
        
    }
    return return_dict
        

@student_router.get("/search")
def search_students(q: str, db: Session = Depends(get_db)):
    stmt = select(Student).where(
        Student.search_vector.op('@@')(func.plainto_tsquery(q))
    )
    results = db.execute(stmt).scalars().all()
    return results

@student_router.get("/overall/top{n}")
def get_overall_top_n(n:int,db:Session=Depends(get_db)):
    ascending= db.query(Student,((Student.avg_grades+Student.attendance+Student.behavioral+Student.extracurricular)/4).label('average_score')).order_by(asc('average_score')).limit(n).all()
    descending= db.query(Student,((Student.avg_grades+Student.attendance+Student.behavioral+Student.extracurricular)/4).label('average_score')).order_by(desc('average_score')).limit(n).all()
    return {
        "ascending": [to_dict(row) for row in ascending],
        "descending": [to_dict(row) for row in descending]
    }
    
@student_router.get("/overall/charts")
def get_overall_charts(db:Session=Depends(get_db)):
    results = db.query(
    Student, 
    StudentPredctions.cluster,
    StudentPredctions.risk,
    StudentGrades.first_exam, 
    StudentGrades.second_exam, 
    StudentGrades.third_exam, 
    StudentGrades.fourth_exam
).join(
    StudentGrades, StudentGrades.student_id == Student.id
).join(
    StudentPredctions, StudentPredctions.student_id == Student.id
).all()

    
    # Initialize an empty list to hold the data
    whole_data = []
    
    # Process the results from the JOIN
    for student,cluster,risk, first_exam, second_exam, third_exam, fourth_exam in results:
        my_dict = {
            'name': student.name,
            'grade': student.grade,
            'section': student.section,
            'address': student.address,
            'cluster':cluster,
            'risk':risk,
            'avg_grades': student.avg_grades,
            'behavioral': student.behavioral,
            'attendance': student.attendance,
            'extracurricular': student.extracurricular,
            'first_exam': first_exam,
            'second_exam': second_exam,
            'third_exam': third_exam,
            'fourth_exam': fourth_exam,
        }
        whole_data.append(my_dict)
    
    return {'data': whole_data}

@student_router.get("/students/section/{section}")
def get_students_by_section(section: str, db: Session = Depends(get_db)):
    return db.query(Student).filter(Student.section == section).all()

@student_router.get("/students/top/{n}")
def get_top_students(n: int, db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.avg_grades.desc()).limit(n).all()

@student_router.get("/students/bottom/{n}/behavioral")
def get_bottom_behavioral_students(n: int, db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.behavioral.asc()).limit(n).all()

@student_router.get("/students/bottom/{n}/attendance")
def get_bottom_attendance_students(n: int, db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.attendance.asc()).limit(n).all()
