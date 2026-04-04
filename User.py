import numpy as np
from pydantic import BaseModel
from dataclasses import dataclass


@dataclass
class UserModel:
    first_name: str
    last_name: str
    embedding: np.ndarray
