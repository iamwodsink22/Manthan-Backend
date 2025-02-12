from utils.models import SessionLocal,Student,StudentPredctions
from fastapi import APIRouter
from sqlalchemy import func,select,case
analytics_router=APIRouter()

@analytics_router.get('/overall')
def overall_analytics():
    
    clusters='Balanced but inconsistent',   'Academically focused', 'Disciplined but inactive','Hard Worker and Active','Talented but unruly','Needs Intervention','Active but struggling','Diligent but underperforming',
    session=SessionLocal()
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
    return {'total':at_risk+not_at_risk,'at_risk':at_risk,'not_risk':not_at_risk,'cluster_dict':cluster_dict}
     
    
    
    

