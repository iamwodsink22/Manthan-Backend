from fastapi import FastAPI
from utils.routers.students import student_router
from utils.routers.predictions import prediction_router
from utils.routers.analytics import analytics_router
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(debug=True)
origins = [
    "http://localhost:3000",

]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(student_router,prefix='/students')
app.include_router(prediction_router,prefix='/predictions')
app.include_router(analytics_router,prefix='/analytics')
