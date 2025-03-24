from utils.models import SessionLocal,Student,StudentPredctions
from fastapi import APIRouter
import json
from sqlalchemy import func,select,case
analytics_router=APIRouter()

def get_top_5_high_risk_sections(db):
    # Get all students with their risk status
    results = (
        db.query(
            Student.grade,
            Student.section,
            StudentPredctions.risk
        )
        .join(StudentPredctions, Student.id == StudentPredctions.student_id)
        .all()
    )
    
    # Process results in Python
    section_stats = {}
    for grade, section, is_at_risk in results:
        key = (grade, section)
        if key not in section_stats:
            section_stats[key] = {"total": 0, "at_risk": 0}
        
        section_stats[key]["total"] += 1
        if is_at_risk:
            section_stats[key]["at_risk"] += 1
    
    # Calculate percentages and format
    formatted_results = []
    for (grade, section), stats in section_stats.items():
        if stats["total"] > 0:
            risk_percentage = (stats["at_risk"] / stats["total"]) * 100
            formatted_results.append({
                "grade": grade,
                "section": section,
                "total": stats["total"],
                "at_risk": stats["at_risk"],
                "risk_percentage": round(risk_percentage, 1)
            })
    
    # Sort and limit
    formatted_results.sort(key=lambda x: x["risk_percentage"], reverse=True)
    return formatted_results[:5]

@analytics_router.get('/overall')
def overall_analytics():
    
    clusters='Balanced but inconsistent',   'Academically focused', 'Disciplined but inactive','Hard Worker and Active','Talented but unruly','Needs Intervention','Active but struggling','Diligent but underperforming',
    session=SessionLocal()
    sections=get_top_5_high_risk_sections(session)
    count_true_false = (
    session.query(
        func.count(case((StudentPredctions.risk == True, 1))).label("true_count"),
        func.count(case((StudentPredctions.risk == False, 1))).label("false_count"),
    )
).one()
    at_risk,not_at_risk=count_true_false
    cluster_dict={}
    for i in clusters:
        nums=session.scalar(select(func.count()).where(StudentPredctions.cluster==i))
        cluster_dict[i]=nums
    return {'total':at_risk+not_at_risk,'at_risk':at_risk,'not_risk':not_at_risk,'cluster_dict':cluster_dict,"sections":json.dumps(sections)}
     
    
    
    

