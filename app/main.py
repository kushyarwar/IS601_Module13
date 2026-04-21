from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List

from app.database import engine, get_db
from app import models, schemas
from app.auth import hash_password, verify_password
from app.calculator import CalculationFactory, OperationType
from app.jwt_utils import create_token

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Calculator API - Module 13", version="5.0.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Auth Routes (/register and /login as required by spec) ────────────────

@app.post("/register", response_model=schemas.RegisterResponse, status_code=201)
@app.post("/users/register", response_model=schemas.RegisterResponse, status_code=201)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    effective_username = user.username or user.email.split("@")[0]
    existing = db.query(models.User).filter(
        (models.User.username == effective_username) | (models.User.email == user.email)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    db_user = models.User(
        username=effective_username,
        email=user.email,
        password_hash=hash_password(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = create_token(db_user.id, db_user.email)
    return schemas.RegisterResponse(
        token=token,
        message="Registration successful",
        user=schemas.UserRead.model_validate(db_user),
    )


@app.post("/login", response_model=schemas.LoginResponse)
@app.post("/users/login", response_model=schemas.LoginResponse)
def login_user(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_token(user.id, user.email)
    return schemas.LoginResponse(
        token=token,
        message="Login successful",
        user=schemas.UserRead.model_validate(user),
    )


@app.get("/users/", response_model=List[schemas.UserRead])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@app.get("/users/{user_id}", response_model=schemas.UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()


# ── Calculation Routes (BREAD) ─────────────────────────────────────────────

@app.get("/calculations/", response_model=List[schemas.CalculationRead])
def browse_calculations(db: Session = Depends(get_db)):
    return db.query(models.Calculation).all()


@app.get("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def read_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return calc


@app.put("/calculations/{calc_id}", response_model=schemas.CalculationRead)
def edit_calculation(calc_id: int, update: schemas.CalculationUpdate, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")

    new_a = update.a if update.a is not None else calc.a
    new_b = update.b if update.b is not None else calc.b
    new_type_str = update.type.value if update.type is not None else calc.type
    new_type = OperationType(new_type_str)

    if new_type == OperationType.Divide and new_b == 0:
        raise HTTPException(status_code=422, detail="Division by zero is not allowed")

    calc.a = new_a
    calc.b = new_b
    calc.type = new_type_str
    calc.result = CalculationFactory.compute(new_type, new_a, new_b)

    db.commit()
    db.refresh(calc)
    return calc


@app.post("/calculations/", response_model=schemas.CalculationRead, status_code=201)
def add_calculation(calc: schemas.CalculationCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == calc.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    result = CalculationFactory.compute(calc.type, calc.a, calc.b)
    db_calc = models.Calculation(
        a=calc.a,
        b=calc.b,
        type=calc.type.value,
        result=result,
        user_id=calc.user_id,
    )
    db.add(db_calc)
    db.commit()
    db.refresh(db_calc)
    return db_calc


@app.delete("/calculations/{calc_id}", status_code=204)
def delete_calculation(calc_id: int, db: Session = Depends(get_db)):
    calc = db.query(models.Calculation).filter(models.Calculation.id == calc_id).first()
    if not calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(calc)
    db.commit()


# ── Join Query ─────────────────────────────────────────────────────────────

@app.get("/calculations/join/all", response_model=List[schemas.CalculationWithUser])
def calculations_with_users(db: Session = Depends(get_db)):
    rows = (
        db.query(models.Calculation, models.User.username)
        .join(models.User, models.Calculation.user_id == models.User.id)
        .all()
    )
    return [schemas.CalculationWithUser(
        username=username,
        a=calc.a,
        b=calc.b,
        type=calc.type,
        result=calc.result,
    ) for calc, username in rows]


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}
