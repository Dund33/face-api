from dotenv import load_dotenv
import os


def init_config_store():
    load_dotenv()


async def config_store():

    min_face_confidence = os.getenv("MIN_FACE_CONFIDENCE")
    min_face_confidence = (
        float(min_face_confidence) if min_face_confidence is not None else 0
    )
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = "HS256"
    API_USER = os.getenv("API_USER")
    API_PASSWORD = os.getenv("API_PASSWORD")
    POS_ID_THRESH = os.getenv("POSITIVE_ID_THRESH")
    POS_ID_THRESH = float(POS_ID_THRESH) if POS_ID_THRESH is not None else 0

    return {
        "secret_key": SECRET_KEY,
        "algorithm": ALGORITHM,
        "api_username": API_USER,
        "api_password": API_PASSWORD,
        "pos_id_thresh": POS_ID_THRESH,
        "min_face_confidence": min_face_confidence,
    }
