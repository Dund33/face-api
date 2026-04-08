import redis
import numpy as np
from redis.commands.search.field import VectorField, TextField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from User import UserModel


class RedisVectorStore:
    def __init__(self, host="redis", port=6379, index_name="vector_index", dim=128):
        self.client = redis.Redis(host=host, port=port, decode_responses=False)
        self.index_name = index_name
        self.dim = dim

    def create_index(self):
        try:
            self.client.ft(self.index_name).create_index(
                fields=[
                    TextField("id"),
                    TextField("firstName"),
                    TextField("lastName"),
                    VectorField(
                        "vector",
                        "HNSW",
                        {
                            "TYPE": "FLOAT32",
                            "DIM": self.dim,
                            "DISTANCE_METRIC": "COSINE",
                        },
                    ),
                ],
                definition=IndexDefinition(prefix=["vec:"], index_type=IndexType.HASH),
            )
        except Exception:
            pass

    def add_user(self, user_id: str, user: UserModel):
        key = f"vec:{user_id}"
        self.client.hset(
            key,
            mapping={
                "id": user_id,
                "firstName": user.first_name,
                "lastName": user.last_name,
                "vector": user.embedding.astype(np.float32).tobytes(),
            },
        )

    def search(self, query_vector: np.ndarray, k=5):
        q = (
            Query(f"*=>[KNN {k} @vector $vec AS score]")
            .sort_by("score")
            .return_fields("id", "score", "firstName", "lastName")
            .dialect(2)
        )

        params = {"vec": query_vector.astype(np.float32).tobytes()}

        results = self.client.ft(self.index_name).search(q, query_params=params)

        return [
            {
                "id": doc.id,
                "first_name": doc.firstName,
                "last_name": doc.lastName,
                "score": float(doc.score),
            }
            for doc in results.docs
        ]
    
    def similarity_by_id(self, user_id: str, query_vector: np.ndarray):
        q = Query(
            f'@id:"{user_id}"=>[KNN 1 @vector $vec AS score]'
            ).sort_by("score").return_fields("score").dialect(2)
        
        params = {"vec": query_vector.astype(np.float32).tobytes()}
        
        result = self.client.ft(self.index_name).search(q, query_params=params)

        if result.total == 0:
            return None
        
        return float(result.docs[0].score)
