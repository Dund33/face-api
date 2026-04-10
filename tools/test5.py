import asyncio
import itertools as it
import time
from dataclasses import dataclass

import tqdm
from faker import Faker

from helptools import clear_data, login_user, register_user
from PersonsDataset import PersonDataset

N_REPEAT = 10


@dataclass
class User:
    first_name: str
    last_name: str
    id: str
    register_imgs: list
    login_imgs: list


async def populate():
    dataset = PersonDataset("../data/vggface2/train")
    fake = Faker()
    subset = list(it.islice(dataset, 500))
    ids = []
    for images, person_id in tqdm.tqdm(subset):
        first_name = fake.unique.first_name()
        last_name = fake.unique.last_name()

        imgs = images[3:]
        response = await register_user(
            images=imgs, first_name=first_name, last_name=last_name
        )

        user_id = response.json()["id"]
        ids.append(user_id)

    return ids


async def time_register():
    await clear_data()
    dataset = PersonDataset("../data/vggface2/train")
    imgs, id = dataset[0]
    imgs = imgs[3:]

    start = time.perf_counter()
    for _ in range(N_REPEAT):
        await register_user(imgs, "John", "Doe")
    end = time.perf_counter()

    return (end - start) / N_REPEAT


async def time_login(user_ids):
    dataset = PersonDataset("../data/vggface2/train")
    imgs, id = dataset[0]
    img = imgs[0]
    user_id = user_ids[0]
    start = time.perf_counter()
    for _ in range(N_REPEAT):
        await login_user(img, user_id)
    end = time.perf_counter()

    return (end - start) / N_REPEAT


async def main():
    register_time = await time_register()
    user_ids = await populate()
    login_time = await time_login(user_ids)
    print(f"Register time {register_time}")
    print(f"Login time {login_time}")


if __name__ == "__main__":
    asyncio.run(main())


# Register time 0.5803541900000709
# Login time 0.471075109999947
