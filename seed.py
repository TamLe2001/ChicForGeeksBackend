import os
from datetime import datetime, timezone

from pymongo import MongoClient, ASCENDING

from api.config import Config


def _seed_default_garments(db):
    """Seed default garments (shirts, pants, skirts, accessories) with user_id='default'."""
    now = datetime.now(timezone.utc)

    # Default shirts
    shirts = [
        {
            "type": "shirt",
            "_id": "tshirt_fitted_black_female",
            "name": "tshirt_fitted_black_female.glb",
            "display_name": "Fitted Black Tshirt",
            "user_id": "default",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_fitted_white_female",
            "name": "tshirt_fitted_white_female.glb",
            "display_name": "Fitted White Tshirt",
            "user_id": "default",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_longsleeve_black_female",
            "name": "tshirt_longsleeve_black_female.glb",
            "display_name": "Black Longsleeve",
            "user_id": "default",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_longsleeve_white_female",
            "name": "tshirt_longsleeve_white_female.glb",
            "display_name": "White Longsleeve",
            "user_id": "default",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_white_male",
            "name": "tshirt_white_male.glb",
            "display_name": "White Tshirt",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_black_male",
            "name": "tshirt_black_male.glb",
            "display_name": "Black Tshirt",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_longsleeve_white_male",
            "name": "tshirt_longsleeve_white_male.glb",
            "display_name": "White Longsleeve",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "_id": "tshirt_longsleeve_black_male",
            "name": "tshirt_longsleeve_black_male.glb",
            "display_name": "Black Longsleeve",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
    ]

    # Default pants
    pants = [
        {
            "type": "pants",
            "_id": "pants_baggy_black_female",
            "name": "pants_baggy_black_female.glb",
            "display_name": "Baggy Black Pants",
            "user_id": "default",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_baggy_denim_female",
            "name": "pants_baggy_denim_female.glb",
            "display_name": "Baggy Denim Pants",
            "user_id": "default",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_baggy_camo_female",
            "name": "pants_baggy_camo_female.glb",
            "display_name": "Baggy Camo Pants",
            "user_id": "default",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_leggings_female",
            "name": "pants_leggings_female.glb",
            "display_name": "Leggings",
            "user_id": "default",
            "gender": "female",
            "style": "sporty",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_shorts_black_female",
            "name": "pants_shorts_black_female.glb",
            "display_name": "Black Shorts",
            "user_id": "default",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_shorts_camo_female",
            "name": "pants_shorts_camo_female.glb",
            "display_name": "Camo Shorts",
            "user_id": "default",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_black_male",
            "name": "pants_black_male.glb",
            "display_name": "Black Pants",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_denim_male",
            "name": "pants_denim_male.glb",
            "display_name": "Denim Pants",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_camo_male",
            "name": "pants_camo_male.glb",
            "display_name": "Camo Pants",
            "user_id": "default",
            "gender": "male",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_shorts_black_male",
            "name": "pants_shorts_black_male.glb",
            "display_name": "Black Shorts",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_shorts_denim_male",
            "name": "pants_shorts_denim_male.glb",
            "display_name": "Denim Shorts",
            "user_id": "default",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "_id": "pants_shorts_camo_male",
            "name": "pants_shorts_camo_male.glb",
            "display_name": "Camo Shorts",
            "user_id": "default",
            "gender": "male",
            "style": "streetwear",
            "published": True,
        },
    ]

    # Default skirts
    skirts = [
        {
            "type": "skirt",
            "_id": "skirt_long_lace_female",
            "name": "skirt_long_lace_female.glb",
            "display_name": "Long Lace Skirt",
            "user_id": "default",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "_id": "skirt_long_white_female",
            "name": "skirt_long_white_female.glb",
            "display_name": "Long White Skirt",
            "user_id": "default",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "_id": "skirt_aline_black_female",
            "name": "skirt_aline_black_female.glb",
            "display_name": "A-line Black Skirt",
            "user_id": "default",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "_id": "skirt_short_black_female",
            "name": "skirt_short_black_female.glb",
            "display_name": "Short Black Skirt",
            "user_id": "default",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
    ]

    # Default accessories
    accessories = [
        {
            "type": "accessory",
            "_id": "accessories_skirt_lace_female",
            "name": "accessories_skirt_lace_female.glb",
            "display_name": "Lace Skirt Accessory",
            "user_id": "default",
            "gender": "female",
            "style": "y2k",
            "published": True,
        },
    ]

    # Seed all garments
    all_garments = shirts + pants + skirts + accessories

    for garment in all_garments:
        db.garments.update_one(
            {"_id": garment["_id"]},
            {
                "$set": {
                    **garment,
                    "default": True,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

    print(
        f"Default garments seed complete: {len(all_garments)} items seeded to garment_default."
    )


def seed_default_garments():
    """Main function to seed default garments to the database."""
    mongo_uri = Config.MONGO_URI
    db_name = Config.MONGO_DB_NAME

    try:
        client = MongoClient(
            mongo_uri,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            retryWrites=False,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
        )
        db = client[db_name]
        
        # Create indexes on garment for faster queries
        db.garments.create_index([('user_id', ASCENDING)])
        db.garments.create_index([('default', ASCENDING)])
        db.garments.create_index([('._id', ASCENDING)], unique=True)
        
        _seed_default_garments(db)
        print("✓ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during seeding: {str(e)}")
        raise


if __name__ == "__main__":
    seed_default_garments()