"""MongoDB connection + serialization helpers for Khova AI."""
import os
import logging
from datetime import datetime, date
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

logger = logging.getLogger("khova.db")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# Directory for generated assets (PDF/XLSX/PNG/HTML)
GENERATED_DIR = ROOT_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


async def ensure_core_indexes():
    """Create the core indexes the hottest read paths depend on (idempotent).

    Before this, the only indexes in the whole app were the ones
    ratelimit.ensure_indexes() creates for anonymous rate limiting — every
    project/session/user lookup elsewhere was a full collection scan.

    Each index is created independently so that one failure (most likely:
    a unique index on users.email failing because duplicate emails already
    exist in this deployment's data) doesn't prevent the others from being
    created, and is logged clearly rather than silently swallowed.
    """
    index_specs = [
        ("projects", "id", {"unique": True}),
        ("projects", "user_id", {}),
        ("projects", "website.slug", {"sparse": True}),
        ("users", "user_id", {"unique": True}),
        ("users", "email", {"unique": True}),
        ("user_sessions", "session_token", {"unique": True}),
        ("generation_jobs", [("project_id", 1), ("task", 1), ("status", 1)], {}),
        ("redeem_codes", "code", {"unique": True}),
    ]
    for collection_name, keys, options in index_specs:
        try:
            await db[collection_name].create_index(keys, **options)
        except Exception as e:
            logger.warning(
                "ensure_core_indexes: failed to create index %s on %s.%s (non-fatal, "
                "app will continue but this collection may be unindexed/have duplicate "
                "data an operator should investigate): %s",
                options, collection_name, keys, e,
            )
    logger.info("core indexes ensured")


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
