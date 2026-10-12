from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from . import models, schemas, security
from .database import Base, engine, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine) # crée les tables au démarrage
    yield

app = FastAPI(title="NotifyLab", lifespan=lifespan)

@app.post("/register", status_code=201)
def register(data: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(username=data.username).first():
        raise HTTPException(409, "Nom d'utilisateur déjà pris")
    user = models.User(username=data.username,
                       hashed_password=security.hash_password(data.password))
    db.add(user)
    db.commit()
    return {"username": user.username}

@app.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(username=form.username).first()
    if not user or not security.verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Identifiants incorrects")
    return {"access_token": security.create_token(user.username, user.role)}

@app.post("/notifications", response_model=schemas.NotificationOut, status_code=201)
def create_notification(data: schemas.NotificationCreate,
                        db: Session = Depends(get_db),
                        user: models.User = Depends(security.get_current_user)):
    notif = models.Notification(recipient=data.recipient,
                                message=data.message, owner_id=user.id)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

@app.get("/notifications/{notif_id}", response_model=schemas.NotificationOut)
def get_notification(notif_id: int, db: Session = Depends(get_db),
                     user: models.User = Depends(security.get_current_user)):
    notif = db.get(models.Notification, notif_id)
    if not notif:
        raise HTTPException(404, "Notification introuvable")
    if notif.owner_id != user.id and user.role != "admin":
        raise HTTPException(403, "Accès interdit")
    return notif