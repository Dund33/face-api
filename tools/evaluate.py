import asyncio
import httpx
import os
import tqdm
from faker import Faker
from pathlib import Path
from dotenv import load_dotenv
from PersonsDataset import PersonDataset

load_dotenv()
TOKEN = os.getenv('TOKEN')
API_URL = "http://localhost:8000/identify" 

async def identify(image_path):
    headers = {
        "Authorization": f"Bearer {TOKEN}"
    }

    image_path = Path(image_path)

    with open(image_path, "rb") as f:
        files = {
            "image": (image_path.name, f, "image/jpeg")
        }

        timeout = httpx.Timeout(120.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                API_URL,
                headers=headers,
                files=files
            )

    return response



async def main():
    dataset = PersonDataset('../data/vggface2/val')
    fake = Faker()
    for images, person_id in tqdm.tqdm(dataset):
        responses = [await identify(image) for image in images]
        contents = list(map(lambda resp: len(resp.json()['found']), responses))
        print(contents)
if __name__ == "__main__":
    asyncio.run(main())
