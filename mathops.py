import numpy as np


def medoid(arrays):
    arrays = np.array(arrays)
    distances = np.linalg.norm(arrays[:, None] - arrays[None, :], axis=2)
    total_distances = distances.sum(axis=1)
    medoid_index = np.argmin(total_distances)

    return arrays[medoid_index]
