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
API_URL = "http://localhost:8000/register"
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
        response = await client.post(API_URL, headers=headers, files=files, data=data)

    for _, (name, f, _) in files:
        f.close()

    return response


async def main():
    dataset = PersonDataset("../data/vggface2/train")
    fake = Faker()
    subset = list(it.islice(dataset, 200))
    for images, person_id in tqdm.tqdm(subset):
        first_name = fake.unique.first_name()
        last_name = fake.unique.last_name()

        response = await register_user(
            images=images, first_name=first_name, last_name=last_name
        )

        print("Status:", response.status_code)
        print("Response:", response.text)


if __name__ == "__main__":
    asyncio.run(main())
