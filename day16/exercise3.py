from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status
import jwt
from datetime import datetime, timedelta
from exercise2 import app, shipments_db

SECRET_KEY = "training-only-secret-change-in-production"
ALGORITHM = "HS256"
DEMO_USER = {"username": "ops_admin", "password": "demo-password"}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if (
        form_data.username != DEMO_USER["username"]
        or form_data.password != DEMO_USER["password"]
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    token = jwt.encode(
        {"sub": form_data.username, "exp": datetime.utcnow() + timedelta(minutes=30)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username
