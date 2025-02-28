from fastapi import APIRouter, Depends
from pydantic import BaseModel
from utils.models import SessionLocal, User
from sqlalchemy import func,exc
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi import HTTPException
from datetime import datetime,timedelta
import jwt

SECRET_KEY = "Araksha@222"
ALGORITHM = "HS256"
auth_router=APIRouter()
pwd_context=CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pwd):
    return pwd_context.hash(pwd)


def verify_password(pwd,hashed):
    return pwd_context.verify(pwd,hashed)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode=data.copy()
    expires=datetime.now()+expires_delta
    to_encode.update({'exp':expires})
    return jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)


class Credentials(BaseModel):
    email:str
    password:str
    
class UserRegister(BaseModel):
    name:str
    email: str
    password: str
    college: str
    
    
def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()
    
@auth_router.post('/login')
def login(credentials:Credentials,db:Session=Depends(get_db)):
    email,password=credentials.email,credentials.password
    try:
        user=db.query(User).where(User.email==email).one()
        verified=verify_password(password,user.password)
        if not verified:
            return HTTPException(status_code=401, detail="Invalid credentials")
        else:
            print('verified')
            user_dict={'id':str(user.id),'email':user.email,'college':user.college}
            access_token_expires = timedelta(hours=2)
            access_token=create_access_token(user_dict,access_token_expires)
            print(access_token)
            return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
            return HTTPException(status_code=401, detail="Invalid credentials")
        
        
    
@auth_router.post('/register')
def register(user: UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)

    new_user = User(name=user.name,email=user.email, password=hashed_password, college=user.college,super_admin=False)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  

        return {"message": "User created successfully", "user": {"email": new_user.email, "college": new_user.college}}

    except exc.SQLAlchemyError as e:
        db.rollback()  
        raise HTTPException(status_code=500, detail="Error registering user")
        
        
    