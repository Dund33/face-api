from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Annotated
import uuid
import jwt
from datetime import datetime, timedelta
import os
import cv2
import numpy as np
from deepface import DeepFace
from deepface.modules.exceptions import FaceNotDetected
from VectorStore import RedisVectorStore
from User import UserModel
from mathops import medoid
from SettingsStore import config_store, init_config_store

init_config_store()
vector_store = RedisVectorStore(dim=4096)
vector_store.create_index()
app = FastAPI()
security = HTTPBearer()


def get_face_embedding(image_path: str, config: dict):
    """Extract face embedding from an image"""
    min_face_confidence = config["min_face_confidence"]
    try:
        embedding_objs = DeepFace.represent(image_path)
        face_confidence = embedding_objs[0]["face_confidence"]

        if face_confidence < min_face_confidence:
            raise FaceNotDetected

        embedding = embedding_objs[0]["embedding"]
        embedding = np.array(embedding)
        return embedding

    except FaceNotDetected:
        print("ERROR: FACE NOT DETECTED")
        return None


def create_token(subject: str, config: dict):
    secret_key = config["secret_key"]
    algorithm = config["algorithm"]
    payload = {"sub": subject, "exp": datetime.utcnow() + timedelta(hours=24)}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def verify_token(
    config: Annotated[dict, Depends(config_store)],
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token, config["secret_key"], algorithms=[config["algorithm"]]
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/get_token")
def get_token(
    username: str, password: str, config: Annotated[dict, Depends(config_store)]
):
    api_username = config["api_username"]
    api_password = config["api_password"]
    if username == api_username and password == api_password:
        return {"access_token": create_token(username, config)}
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/register")
async def register_user(
    images: list[UploadFile],
    config: Annotated[dict, Depends(config_store)],
    first_name: str = Form(...),
    last_name: str = Form(...),
    subject: str = Depends(verify_token),
):
    min_face_confidence = config["min_face_confidence"]
    user_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)

    file_paths = []
    for image in images:
        file_path = f"uploads/{user_id}_{image.filename}"
        with open(file_path, "wb") as f:
            f.write(await image.read())
        file_paths.append(file_path)

    embeddings = [get_face_embedding(file_path, config) for file_path in file_paths]
    embeddings = list(filter(lambda x: x is not None, embeddings))
    medoid_embedding = medoid(embeddings)

    if medoid_embedding is not None:
        user_db = UserModel(first_name, last_name, medoid_embedding)
        vector_store.add_user(user_id, user_db)

    return {"id": user_id}


@app.post("/identify")
async def identify(
    config: Annotated[dict, Depends(config_store)],
    image: UploadFile = File(...),
    subject: str = Depends(verify_token),
):
    image_id = str(uuid.uuid4())
    os.makedirs("uploads", exist_ok=True)
    file_path = f"uploads/{image_id}_{image.filename}"
    with open(file_path, "wb") as f:
        f.write(await image.read())

    embedding = get_face_embedding(file_path, config)
    pos_id_thresh = config["pos_id_thresh"]

    if embedding is not None:
        found = vector_store.search(embedding)
        found_filtered = list(filter(lambda x: x["score"] <= pos_id_thresh, found))
        return {"found": found_filtered}
    return {"found": []}
