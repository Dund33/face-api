import asyncio
import itertools as it
import os
from dataclasses import dataclass
from random import choice

import matplotlib.pyplot as plt
import tqdm
from dotenv import load_dotenv
from faker import Faker

from helptools import (
    add_jpeg_artifacts_to_tempfile,
    clear_data,
    login_user,
    register_user,
)
from PersonsDataset import PersonDataset

load_dotenv()
REGISTER_API_URL = "http://localhost:8000/register"
LOGIN_API_URL = "http://localhost:8000/login"
TOKEN = os.getenv("TOKEN")


@dataclass
class User:
    first_name: str
    last_name: str
    id: str
    register_imgs: list
    login_imgs: list


async def register(dataset, quality):
    fake = Faker()
    users = []
    for images, _ in dataset:
        first_name = fake.unique.first_name()
        last_name = fake.unique.last_name()

        register_imgs = list(
            map(lambda x: add_jpeg_artifacts_to_tempfile(x, quality), images[3:8])
        )
        login_imgs = list(
            map(lambda x: add_jpeg_artifacts_to_tempfile(x, quality), images[:3])
        )

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
    for user in users:
        image = choice(user.login_imgs)
        result = await login_user(image, user.id)
        results.append(result.json())

    return results


async def test_incorrect_auth(users):
    results = []
    for user in users:
        other_user = choice(users)
        while other_user is user:
            other_user = choice(users)

        image = choice(other_user.login_imgs)
        result = await login_user(image, user.id)
        results.append(result.json())

    return results


def get_frr(auths):
    FR = 0
    for auth in auths:
        if not auth["success"]:
            FR += 1
    return FR / len(auths)


def get_far(auths):
    FA = 0
    for auth in auths:
        if auth["success"]:
            FA += 1
    return FA / len(auths)


def plot_frr_far(res, filepath):
    qualities = sorted(res.keys())
    fars = [res[q]["far"] for q in qualities]
    frrs = [res[q]["frr"] for q in qualities]

    plt.figure()
    plt.plot(qualities, fars, marker="o", label="FAR")
    plt.plot(qualities, frrs, marker="o", label="FRR")

    for q, f in zip(qualities, fars):
        plt.text(q, f, str(q))
    for q, f in zip(qualities, frrs):
        plt.text(q, f, str(q))

    plt.xlabel("Quality")
    plt.ylabel("Rate")
    plt.title("FAR and FRR vs Quality")
    plt.legend()
    plt.grid(True)

    plt.savefig(filepath, bbox_inches="tight")
    plt.close()


async def main():
    dataset = PersonDataset("../data/vggface2/train")
    subset = list(it.islice(dataset, 200))
    res = {}

    qualities = list(range(20, 95 + 1, 20))
    for quality in tqdm.tqdm(qualities):
        await clear_data()
        registered_users = await register(subset, quality)
        correct_auth = await test_correct_auth(registered_users)
        incorrect_auth = await test_incorrect_auth(registered_users)
        correct_auth = [item for item in correct_auth if "success" in item]
        incorrect_auth = [item for item in incorrect_auth if "success" in item]
        frr = get_frr(correct_auth)
        far = get_far(incorrect_auth)
        res[quality] = {"frr": frr, "far": far}

    plot_frr_far(res, "7.png")


if __name__ == "__main__":
    asyncio.run(main())
