from sqlalchemy import Column, Integer, and_,String, case,Float, ForeignKey, Boolean, DateTime,select,func,desc,asc
from sqlalchemy.orm import relationship
from utils.models import Base, SessionLocal, SubjectAverage,SectionAverage
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session,lazyload,joinedload
from utils.models import Student,StudentPredctions,ExamScore,Subject,SubjectAnalysis
from collections import defaultdict
import json
import uuid
from sqlalchemy.orm import joinedload
from sqlalchemy import func
student_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def calculate_exam_avg(session,student):
    student = session.query(Student).where(Student.id==student).options(lazyload(Student.exam_scores)
    ).one()
    exam_averages = {1: [], 2: [], 3: [], 4: []}
    for score in student.exam_scores:
        exam_averages[score.exam_number].append(score.score)
        
       
        exam_means = []
        for exam_num in [1, 2, 3, 4]:
            if exam_averages[exam_num]:  
                exam_mean = sum(exam_averages[exam_num]) / len(exam_averages[exam_num])
                exam_means.append(round(exam_mean,2))
    return exam_means
    
    
def get_subjectwise_data(session, student_id):
    # Fetch subject analysis data for the student along with the student details (grade and section)
    results = (
        session.query(SubjectAnalysis, Student.grade, Student.section)
        .join(Student, Student.id == SubjectAnalysis.student_id)  # Join Student to get grade and section
        .filter(SubjectAnalysis.student_id == student_id)
        .all()
    )

    subjectwise_data = {}

    for result in results:
        subject_analysis = result.SubjectAnalysis  # SubjectAnalysis object
        grade = result.grade  # Student's grade from the join
        section = result.section  # Student's section from the join

        subject_name = subject_analysis.subject.name

        # Fetch the section-wide average marks for the current subject
        # section_avg_marks is assumed to be of type ARRAY in the SubjectAverage table
        section_avg_marks = (
            session.query(SubjectAverage.avg_marks)
            .join(SectionAverage, SectionAverage.id == SubjectAverage.section_average_id)
            .filter(
                SubjectAverage.subject_id == subject_analysis.subject_id,
                SectionAverage.grade == grade,  # Use the grade from the joined Student
                SectionAverage.section == section  # Use the section from the joined Student
            )
            .first()  # Assuming we get one record with avg_marks for the subject, grade, and section
        )

        # If no section average marks are found, set it to a default list
        if section_avg_marks:
            section_avg_marks_list = section_avg_marks.avg_marks  # Directly get the ARRAY of values
        else:
            section_avg_marks_list = [None, None, None, None]  # If no data is found, return None for all exams

        # Create the final subjectwise data for this student
        subjectwise_data[subject_name] = {
            'avg_marks': subject_analysis.marks,  # Marks for this subject for the student
            'analysis': subject_analysis.analysis,  # Analysis for the subject
            'section_avg_marks': section_avg_marks_list  # Array of section-wide average marks for the subject (for 4 exams)
        }

    return subjectwise_data



        
        
    

def to_dict(student_obj):
        student_obj,_=student_obj
        student_dict = {'id':str(student_obj.id),'img':student_obj.img,'avg_grades':student_obj.avg_grades,
                        'behavioral':student_obj.behavioral,'extracurricular':student_obj.extracurricular,'attendance':student_obj.attendance,
                        'avg_score':_,'name':student_obj.name}
        
        return student_dict
    



@student_router.get("/")
def get_student(id: str, db: Session = Depends(get_db)):
    # Fetch the student and associated prediction data
    student, cluster, risk, explanation = (
        db.query(
            Student,
            StudentPredctions.cluster,
            StudentPredctions.risk,
            StudentPredctions.risk_explanation,
        )
        .join(StudentPredctions, Student.id == StudentPredctions.student_id)
        .filter(Student.id == id)
        .first()
    )
    
    # Fetch the exam averages (this function is assumed to be defined elsewhere)
    grades = calculate_exam_avg(db, student.id)
    
    # Fetch the section averages from the SectionAverage table (modify based on relationship)
    avg_section = db.query(
        SectionAverage.avg_grades.label('section_avg_grades'),
        SectionAverage.avg_attendance.label('section_avg_attendance'),
        SectionAverage.avg_behavioral.label('section_avg_behavioral'),
        SectionAverage.avg_extracurricular.label('section_avg_extracurricular')
    ).filter(
        SectionAverage.grade == student.grade,
        SectionAverage.section == student.section
    ).one_or_none()  
    
    # If no section averages found, use a default value (for example: [None, None, None, None])
    if avg_section:
        section_avg_data = [
            avg_section.section_avg_grades,
            avg_section.section_avg_attendance,
            avg_section.section_avg_behavioral,
            avg_section.section_avg_extracurricular
        ]
    else:
        section_avg_data = [None, None, None, None]  # Default when no section data is found
    
    # Fetch subject analysis data (subject-wide details)
    subject_analysis = get_subjectwise_data(db, id)
    
    # Construct the response dictionary
    return_dict = {
        'name': student.name,
        'grade': student.grade,
        'section': student.section,
        'attendance': student.attendance,
        'behavioral': student.behavioral,
        'extracurricular': student.extracurricular,
        'avg_grades': student.avg_grades,
        'parent_name': student.parent_name,
        'address': student.address,
        'cluster': cluster,
        'at_risk': risk,
        'explanation': explanation,
        'exam_data': grades,
        'subject_analysis': json.dumps(subject_analysis),
        'section_avg_data': section_avg_data  # Array of section averages for 4 exams
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
def get_overall_charts(db: Session = Depends(get_db)):
    
    exam_averages = (
        db.query(
            ExamScore.student_id,
            ExamScore.exam_number,
            func.avg(ExamScore.score).label('exam_avg')
        )
        .group_by(ExamScore.student_id, ExamScore.exam_number)
        .subquery()
    )

    # Step 2: Pivot exam averages into columns
    pivoted_exams = (
        db.query(
            exam_averages.c.student_id,
            func.max(
                case(
                    (exam_averages.c.exam_number == 1, exam_averages.c.exam_avg),
                    else_=None
                )
            ).label('first_exam'),
            func.max(
                case(
                    (exam_averages.c.exam_number == 2, exam_averages.c.exam_avg),
                    else_=None
                )
            ).label('second_exam'),
            func.max(
                case(
                    (exam_averages.c.exam_number == 3, exam_averages.c.exam_avg),
                    else_=None
                )
            ).label('third_exam'),
            func.max(
                case(
                    (exam_averages.c.exam_number == 4, exam_averages.c.exam_avg),
                    else_=None
                )
            ).label('fourth_exam')
        )
        .group_by(exam_averages.c.student_id)
        .subquery()
    )

 
    results = (
        db.query(
            Student,
            StudentPredctions.cluster,
            StudentPredctions.risk,
            pivoted_exams.c.first_exam,
            pivoted_exams.c.second_exam,
            pivoted_exams.c.third_exam,
            pivoted_exams.c.fourth_exam
        )
        .outerjoin(StudentPredctions, Student.id == StudentPredctions.student_id)
        .outerjoin(pivoted_exams, Student.id == pivoted_exams.c.student_id)
        .all()
    )

    whole_data = []
    for student, cluster, risk, first, second, third, fourth in results:
        whole_data.append({
            'name': student.name,
            'grade': student.grade,
            'section': student.section,
            'address': student.address,
            'cluster': cluster,
            'risk': risk,
            'avg_grades': student.avg_grades,
            'behavioral': student.behavioral,
            'attendance': student.attendance,
            'extracurricular': student.extracurricular,
            'first_exam': round(float(first or 0.0), 2),
            'second_exam': round(float(second or 0.0), 2),
            'third_exam': round(float(third or 0.0), 2),
            'fourth_exam': round(float(fourth or 0.0), 2)
        })
    
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
