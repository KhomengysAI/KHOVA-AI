"""MongoDB connection + serialization helpers for Khova AI."""
import os
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# Directory for generated assets (PDF/XLSX/PNG/HTML)
GENERATED_DIR = ROOT_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def serialize_doc(doc):
    """Recursively convert Mongo/py types to JSON-serializable values and drop _id."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            if k == "_id":
                continue
            out[k] = serialize_doc(v)
        return out
    if isinstance(doc, (datetime, date)):
        return doc.isoformat()
    return doc
