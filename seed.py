import os
from datetime import datetime, timezone

from pymongo import MongoClient
from werkzeug.security import generate_password_hash

from api.config import Config
from run import ensure_indexes


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _seed_users(db):
    now = datetime.now(timezone.utc)
    user_fixtures = [
        # Original dummies
        {
            "id": "user:alex@dummy.local",
            "name": "Alex Dummy",
            "email": "alex@dummy.local",
            "password": "dummy123",
            "role": "user",
            "bio": "Dummy account for local development",
            "birthday": "2000-01-01",
            "profile_picture": None,
        },
        {
            "id": "user:maya@dummy.local",
            "name": "Maya Dummy",
            "email": "maya@dummy.local",
            "password": "dummy123",
            "role": "admin",
            "bio": "Admin dummy account for local development",
            "birthday": "1998-05-12",
            "profile_picture": None,
        },
        # New users from user request
        {
            "id": "user:boringlasse@gmail.com",
            "name": "BoringLasse",
            "email": "boringlasse@gmail.com",
            "password": "dummy123",
            "role": "user",
            "bio": "well actually",
            "birthday": "1995-01-01",
            "profile_picture": "LasseMedHatten",
        },
        {
            "id": "user:tiltthora@gmail.com",
            "name": "TiltThora",
            "email": "tiltthora@gmail.com",
            "password": "dummy123",
            "role": "user",
            "bio": "make a driver AH",
            "birthday": "1996-02-02",
            "profile_picture": "default picture",
        },
        {
            "id": "user:banjobenjamin@gmail.com",
            "name": "BanjoBenjamin",
            "email": "banjobenjamin@gmail.com",
            "password": "dummy123",
            "role": "user",
            "bio": "ready to fight",
            "birthday": "1997-03-03",
            "profile_picture": "Banjo",
        },
    ]

    user_ids_by_email = {}
    for user in user_fixtures:
        db.users.update_one(
            {"email": user["email"]},
            {
                "$set": {
                    "name": user["name"],
                    "email": user["email"],
                    "password_hash": generate_password_hash(user["password"]),
                    "role": user["role"],
                    "bio": user["bio"],
                    "birthday": user["birthday"],
                    "profile_picture": user["profile_picture"],
                    "is_dummy": True,
                    "fixture_key": user["fixture_key"],
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

        user_doc = db.users.find_one({"email": user["email"]}, {"_id": 1})
        user_ids_by_email[user["email"]] = str(user_doc["_id"])

    return user_ids_by_email


def _seed_outfits(db, user_ids_by_email):
    now = datetime.now(timezone.utc)
    # Garment helper: only fields read by Garment.from_dict() matter.
    # Fields: type, name, user_id (set at seed time), gender, style, reference, created_at.
    # Valid gender values: "male", "female", "unisex"
    # Valid style values:  "streetwear", "formal", "casual", "sporty", "preppy", "y2k"
    outfit_fixtures = [
        # Original dummies
        {
            "id": "outfit:alex:casual-1",
            "owner_email": "alex@dummy.local",
            "name": "Casual Street",
            "bio": "Comfy daily street style",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "White Tee",
                "gender": "unisex",
                "style": "casual",
                "reference": "shirt_white_unisex",
            },
            "pants": {
                "type": "pants",
                "name": "Blue Jeans",
                "gender": "unisex",
                "style": "casual",
                "reference": "pants_denim_unisex",
            },
        },
        {
            "id": "outfit:maya:smart-1",
            "owner_email": "maya@dummy.local",
            "name": "Smart Office",
            "bio": "Clean office-ready look",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "Black Blouse",
                "gender": "female",
                "style": "formal",
                "reference": "shirt_blouse_black_female",
            },
            "pants": {
                "type": "pants",
                "name": "Office Trousers",
                "gender": "female",
                "style": "formal",
                "reference": "pants_trousers_black_female",
            },
        },
        # BoringLasse outfits
        {
            "id": "outfit:boringlasse:1",
            "owner_email": "boringlasse@gmail.com",
            "name": "White Longsleeve & Black Pants",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "White Longsleeve Tee",
                "gender": "male",
                "style": "casual",
                "reference": "tshirt_longsleeve_white_male",
            },
            "pants": {
                "type": "pants",
                "name": "Black Pants",
                "gender": "male",
                "style": "casual",
                "reference": "pants_black_male",
            },
        },
        {
            "id": "outfit:boringlasse:2",
            "owner_email": "boringlasse@gmail.com",
            "name": "Black Tee & Denim Pants",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "Black T-shirt",
                "gender": "male",
                "style": "casual",
                "reference": "tshirt_black_male",
            },
            "pants": {
                "type": "pants",
                "name": "Denim Pants",
                "gender": "male",
                "style": "casual",
                "reference": "pants_denim_male",
            },
        },
        # TiltThora outfits
        {
            "id": "outfit:tiltthora:1",
            "owner_email": "tiltthora@gmail.com",
            "name": "Fitted Black Tee & A-line Skirt",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "Fitted Black T-shirt",
                "gender": "female",
                "style": "casual",
                "reference": "tshirt_fitted_black_female",
            },
            "skirt": {
                "type": "skirt",
                "name": "A-line Black Skirt",
                "gender": "female",
                "style": "casual",
                "reference": "skirt_aline_black_female",
            },
        },
        {
            "id": "outfit:tiltthora:2",
            "owner_email": "tiltthora@gmail.com",
            "name": "White Longsleeve & Baggy Denim Pants",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "White Longsleeve Tee",
                "gender": "female",
                "style": "casual",
                "reference": "tshirt_longsleeve_white_female",
            },
            "pants": {
                "type": "pants",
                "name": "Baggy Denim Pants",
                "gender": "female",
                "style": "casual",
                "reference": "pants_baggy_denim_female",
            },
        },
        # BanjoBenjamin outfits
        {
            "id": "outfit:banjobenjamin:1",
            "owner_email": "banjobenjamin@gmail.com",
            "name": "White Longsleeve & Camo Pants",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "White Longsleeve Tee",
                "gender": "male",
                "style": "casual",
                "reference": "tshirt_longsleeve_white_male",
            },
            "pants": {
                "type": "pants",
                "name": "Camo Pants",
                "gender": "male",
                "style": "streetwear",
                "reference": "pants_camo_male",
            },
        },
        {
            "id": "outfit:banjobenjamin:2",
            "owner_email": "banjobenjamin@gmail.com",
            "name": "Black Longsleeve & Denim Shorts",
            "bio": "",
            "published": True,
            "shirt": {
                "type": "shirt",
                "name": "Black Longsleeve Tee",
                "gender": "male",
                "style": "casual",
                "reference": "tshirt_longsleeve_black_male",
            },
            "pants": {
                "type": "pants",
                "name": "Denim Shorts",
                "gender": "male",
                "style": "casual",
                "reference": "pants_shorts_denim_male",
            },
        },
    ]

    outfit_ids_by_owner = {}
    for outfit in outfit_fixtures:
        owner_id = user_ids_by_email.get(outfit["owner_email"])
        if not owner_id:
            continue

        # Build garment slots dynamically — only include slots present in the fixture.
        # Inject user_id and created_at into each garment sub-doc at seed time.
        garment_slots = ["shirt", "pants", "skirt", "accessory"]
        garments = {}
        for slot in garment_slots:
            if slot in outfit:
                garments[slot] = {
                    **outfit[slot],
                    "user_id": owner_id,
                    "created_at": now,
                }

        db.outfits.update_one(
            {"id": outfit["id"]},
            {
                "$set": {
                    "name": outfit["name"],
                    "user_id": owner_id,
                    "bio": outfit["bio"],
                    **garments,
                    "published": outfit["published"],
                    "is_dummy": True,
                    "id": outfit["id"],
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

        outfit_doc = db.outfits.find_one({"id": outfit["id"]}, {"_id": 1, "user_id": 1})
        user_id = outfit_doc.get("user_id")
        outfit_ids_by_owner.setdefault(user_id, []).append(outfit_doc["_id"])

    return outfit_ids_by_owner


def _seed_wardrobes(db, outfit_ids_by_owner):
    now = datetime.now(timezone.utc)
    for user_id, outfit_ids in outfit_ids_by_owner.items():
        db.wardrobes.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "outfit_ids": outfit_ids,
                    "updated_at": now,
                    "is_dummy": True,
                    "fixture_key": f"wardrobe:{user_id}",
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )


def seed_dummy_data():
    if not _env_bool("SEED_DUMMY_DATA", default=False):
        print("SEED_DUMMY_DATA is disabled; skipping dummy seed.")
        return

    mongo_uri = Config.MONGO_URI
    db_name = Config.MONGO_DB_NAME

    client = MongoClient(
        mongo_uri,
        connectTimeoutMS=5000,
        serverSelectionTimeoutMS=5000,
        retryWrites=False,
        tlsAllowInvalidCertificates=True,
        tlsAllowInvalidHostnames=True,
    )
    db = client[db_name]

    ensure_indexes(db)
    user_ids_by_email = _seed_users(db)
    outfit_ids_by_owner = _seed_outfits(db, user_ids_by_email)
    _seed_wardrobes(db, outfit_ids_by_owner)

    print("Dummy data seed complete (upsert mode).")


if __name__ == "__main__":
    seed_dummy_data()