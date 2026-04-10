import itertools as it
from pathlib import Path


class PersonDataset:
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform

        self.person_dirs = sorted([p for p in self.root_dir.iterdir() if p.is_dir()])

        self.data = []
        for idx, person_dir in enumerate(self.person_dirs):
            images = [
                p
                for p in person_dir.iterdir()
                if p.suffix.lower() in [".jpg", ".jpeg", ".png"]
            ]
            if images:
                images = list(it.islice(images, 5))
                self.data.append((idx, images))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        person_id, image_paths = self.data[idx]

        return image_paths, person_id
