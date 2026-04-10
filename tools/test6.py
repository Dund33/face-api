import asyncio
import itertools as it
import os
from dataclasses import dataclass
from random import choice

import matplotlib.pyplot as plt
import numpy as np
import tqdm
from dotenv import load_dotenv
from faker import Faker

from helptools import clear_data, login_user, register_user
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
        image = choice(user.login_imgs)
        result = await login_user(image, user.id)
        results.append(result.json())

    return results


async def test_incorrect_auth(users):
    results = []
    for user in tqdm.tqdm(users):
        other_user = choice(users)
        while other_user is user:
            other_user = choice(users)

        image = choice(other_user.login_imgs)
        result = await login_user(image, user.id)
        results.append(result.json())

    return results


def get_frr(auths, threshold):
    FR = 0
    for auth in auths:
        if auth["score"] > threshold:
            FR += 1
    return FR / len(auths)


def get_far(auths, threshold):
    FA = 0
    for auth in auths:
        if auth["score"] <= threshold:
            FA += 1
    return FA / len(auths)


async def main():
    await clear_data()
    dataset = PersonDataset("../data/vggface2/train")
    subset = list(it.islice(dataset, 200))
    registered_users = await register(subset)
    correct_auth = await test_correct_auth(registered_users)
    incorrect_auth = await test_incorrect_auth(registered_users)

    correct_auth = [item for item in correct_auth if "score" in item]
    incorrect_auth = [item for item in incorrect_auth if "score" in item]

    thresholds = np.arange(0.1, 1.1, 0.1)

    frr = {thresh: get_frr(correct_auth, thresh) for thresh in thresholds}
    far = {thresh: get_far(incorrect_auth, thresh) for thresh in thresholds}

    sorted_thresh = sorted(thresholds)

    far_values = [far[t] for t in sorted_thresh]
    frr_values = [frr[t] for t in sorted_thresh]
    tpr_values = [1 - frr[t] for t in sorted_thresh]

    plt.figure()
    plt.plot(far_values, tpr_values, marker="o")
    plt.xlabel("False Acceptance Rate (FAR)")
    plt.ylabel("True Positive Rate (TPR)")
    plt.title("ROC Curve")

    for i, t in enumerate(sorted_thresh):
        plt.annotate(f"{t:.1f}", (far_values[i], tpr_values[i]))

    plt.savefig("roc_curve.png")
    plt.close()


if __name__ == "__main__":
    asyncio.run(main())
