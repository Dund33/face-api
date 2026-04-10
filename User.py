from dataclasses import dataclass

import numpy as np


@dataclass
class UserModel:
    first_name: str
    last_name: str
    embedding: np.ndarray
