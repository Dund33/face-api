import asyncio
import itertools as it
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from random import choice

import tqdm
from dotenv import load_dotenv
from faker import Faker

from helptools import clear_data, login_user, register_user
from PersonsDataset import PersonDataset

load_dotenv()
REGISTER_API_URL = "http://localhost:8000/register"
LOGIN_API_URL = "http://localhost:8000/login"
TOKEN = os.getenv("TOKEN")
POS_ID_THRESH = 0.7


@dataclass
class User:
    first_name: str
    last_name: str
    id: str
    register_imgs: list
    login_imgs: list


async def register(dataset):
    fake = Faker()
    users = []
    for images, _ in tqdm.tqdm(dataset):
        first_name = fake.unique.first_name()
        last_name = fake.unique.last_name()

        register_imgs = images[3:]
        login_imgs = images[:3]

        user = User(first_name, last_name, "", register_imgs, login_imgs)

        response = await register_user(
            images=register_imgs, first_name=first_name, last_name=last_name
        )

        user_id = response.json()["id"]
        user.id = user_id

        users.append(user)
    return users


async def test_correct_auth(users):
    results = []
    for user in tqdm.tqdm(users):
        image = user.login_imgs[0]
        response = await login_user(image, user.id)
        result = response.json()
        result["user_id"] = user.id
        results.append(result)

    return results


async def test_incorrect_auth(users):
    results = []
    for user in tqdm.tqdm(users):
        other_user = choice(users)
        while other_user is user:
            other_user = choice(users)

        image = other_user.login_imgs[0]
        response = await login_user(image, user.id)
        result = response.json()
        result["user_id"] = user.id
        result["other_user_id"] = other_user.id
        results.append(result)

    return results


def copy_to__dir(file_paths, target_dir):
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    for file_path in file_paths:
        src = Path(file_path)
        dst = target_path / src.name
        shutil.copy2(src, dst)


async def main():
    await clear_data()
    dataset = PersonDataset("../data/vggface2/train")
    subset = list(it.islice(dataset, 100))
    registered_users = await register(subset)
    correct_auth = await test_correct_auth(registered_users)
    incorrect_auth = await test_incorrect_auth(registered_users)

    correct_auth = [item for item in correct_auth if "score" in item]
    incorrect_auth = [item for item in incorrect_auth if "score" in item]

    false_rejects = [auth for auth in correct_auth if auth["score"] > POS_ID_THRESH]
    false_accepts = [auth for auth in incorrect_auth if auth["score"] <= POS_ID_THRESH]
    false_reject_ids = set([fr["user_id"] for fr in false_rejects])
    false_accept_ids = set([fa["other_user_id"] for fa in false_accepts])

    false_reject_users = [
        user for user in registered_users if user.id in false_reject_ids
    ]
    false_accept_users = [
        user for user in registered_users if user.id in false_accept_ids
    ]

    false_accept_imgs = [user.login_imgs[0] for user in false_accept_users]
    false_reject_imgs = [user.login_imgs[0] for user in false_reject_users]

    copy_to__dir(false_accept_imgs, "false_accept")
    copy_to__dir(false_reject_imgs, "false_reject")


if __name__ == "__main__":
    asyncio.run(main())
