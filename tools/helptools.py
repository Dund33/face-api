import asyncio
import httpx
import os
import tqdm
import itertools as it
from faker import Faker
from pathlib import Path
from dotenv import load_dotenv
from PersonsDataset import PersonDataset

load_dotenv()
REGISTER_URL = "http://localhost:8000/register"
LOGIN_URL = "http://localhost:8000/login"
IDENTIFY_URL = "http://localhost:8000/identify"
TOKEN = os.getenv("TOKEN")

async def register_user(images, first_name, last_name):
    headers = {"Authorization": f"Bearer {TOKEN}"}

    files = []
    for img_path in images:
        img_path = Path(img_path)
        files.append(("images", (img_path.name, open(img_path, "rb"), "image/jpeg")))

    data = {"first_name": first_name, "last_name": last_name}
    timeout = httpx.Timeout(120)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(REGISTER_URL, headers=headers, files=files, data=data)

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
