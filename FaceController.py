from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict
import uuid
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import cv2
import numpy as np
from deepface import DeepFace
from deepface.modules.exceptions import FaceNotDetected

load_dotenv()

min_face_confidence = os.getenv("MIN_FACE_CONFIDENCE")
min_face_confidence = float(min_face_confidence) if min_face_confidence is not None else 0
app = FastAPI()

def get_face_embedding(image_path):
    """Extract face embedding from an image"""
    img_size  = os.path.getsize(image_path)
    print(f'DEBUG -- IMG LEN {img_size} ----------------------------')
    try:
        embedding_objs = DeepFace.represent(image_path)
        face_confidence = embedding_objs[0]['face_confidence']

        if face_confidence < min_face_confidence:
            raise FaceNotDetected

        embedding = embedding_objs[0]['embedding']
        return embedding
    
    except FaceNotDetected:
        print('ERROR: FACE NOT DETECTED')
        return None

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

API_USER = os.getenv("API_USER")
API_PASSWORD = os.getenv("API_PASSWORD")

images: Dict[str, dict] = {}

security = HTTPBearer()


def create_token(subject: str):
    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/get_token")
def get_token(username: str, password: str):
    if username == API_USER and password == API_PASSWORD:
        return {"access_token": create_token(username)}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/register")
async def register_image(
    image: UploadFile = File(...),
    subject: str = Depends(verify_token)
):
    image_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{image_id}_{image.filename}"
    with open(file_path, "wb") as f:
        f.write(await image.read())
    print(f'DEBUG -- FILE PATH {file_path} ----------------------------')
    embedding = get_face_embedding(file_path)
    return {"image_id": image_id, "file_path": file_path, "embedding": embedding}


@app.get("/identify")
def identify(subject: str = Depends(verify_token)):
    return {"authenticated_as": subject}