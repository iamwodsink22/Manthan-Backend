from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from utils.models import Base, SessionLocal
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from utils.models import Student
from utils.ai.makepredictions import RunPredictions

prediction_router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
@prediction_router.post('/runpredictions')
def run_predictions_whole():
    
        rp=RunPredictions()
        rp.run_whole_inference()
        return JSONResponse(content={'result': 'Done Successfully'}, status_code=200)
    # except:
    #     raise HTTPException(status_code=500,detail='Something went wrong')

@prediction_router.post('/runpredictions')
def run_predictions_whole(id:str):
    pass
    