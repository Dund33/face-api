import os
import tqdm
import io
import itertools as it
from faker import Faker
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()
REGISTER_URL = "http://localhost:8000/register"
LOGIN_URL = "http://localhost:8000/login"
IDENTIFY_URL = "http://localhost:8000/identify"
CLEAR_API_URL = "http://localhost:8000/clear"
TOKEN = os.getenv("TOKEN")

import io
import os
import tempfile
import uuid

from PIL import Image


def add_jpeg_artifacts_to_tempfile(image_path, quality=30, iterations=1):
    img = Image.open(image_path).convert("RGB")

    for _ in range(iterations):
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)
        img = Image.open(buffer).convert("RGB")

    temp_dir = tempfile.gettempdir()
    filename = f"jpeg_artifact_{uuid.uuid4().hex}.jpg"
    filepath = os.path.join(temp_dir, filename)

    img.save(filepath, format="JPEG", quality=quality)

    return filepath


async def clear_data():
    headers = {"Authorization": f"Bearer {TOKEN}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(CLEAR_API_URL, headers=headers)
        return response


async def register_user(images, first_name, last_name):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    files = []
    for img_path in images:
        img_path = Path(img_path)
        files.append(("images", (img_path.name, open(img_path, "rb"), "image/jpeg")))

    data = {"first_name": first_name, "last_name": last_name}
    timeout = httpx.Timeout(120)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            REGISTER_URL, headers=headers, files=files, data=data
        )

    for _, (name, f, _) in files:
        f.close()

    return response


async def login_user(image_path, user_id):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    data = {"user_id": user_id}

    image_path = Path(image_path)

    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/jpeg")}

        timeout = httpx.Timeout(120.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                LOGIN_URL, headers=headers, files=files, data=data
            )

    return response

async def login_user_image(image, user_id, name):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    data = {"user_id": user_id}

    file_obj = io.BytesIO(image)

    files = {"image": (name, file_obj, "image/png")}

    timeout = httpx.Timeout(120.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(LOGIN_URL, headers=headers, files=files, data=data)

    return response


async def identify(image_path):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    image_path = Path(image_path)

    with open(image_path, "rb") as f:
        files = {"image": (image_path.name, f, "image/jpeg")}

        timeout = httpx.Timeout(120.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(IDENTIFY_URL, headers=headers, files=files)

    return response
