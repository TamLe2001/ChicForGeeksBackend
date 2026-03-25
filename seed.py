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
            "id": "tshirt_fitted_black_female",
            "name": "tshirt_fitted_black_female.glb",
            "display_name": "Fitted Black Tshirt",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_fitted_white_female",
            "name": "tshirt_fitted_white_female.glb",
            "display_name": "Fitted White Tshirt",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_longsleeve_black_female",
            "name": "tshirt_longsleeve_black_female.glb",
            "display_name": "Black Longsleeve",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_longsleeve_white_female",
            "name": "tshirt_longsleeve_white_female.glb",
            "display_name": "White Longsleeve",
            "gender": "female",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_white_male",
            "name": "tshirt_white_male.glb",
            "display_name": "White Tshirt",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_black_male",
            "name": "tshirt_black_male.glb",
            "display_name": "Black Tshirt",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_longsleeve_white_male",
            "name": "tshirt_longsleeve_white_male.glb",
            "display_name": "White Longsleeve",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "shirt",
            "id": "tshirt_longsleeve_black_male",
            "name": "tshirt_longsleeve_black_male.glb",
            "display_name": "Black Longsleeve",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
    ]

    # Default pants
    pants = [
        {
            "type": "pants",
            "id": "pants_baggy_black_female",
            "name": "pants_baggy_black_female.glb",
            "display_name": "Baggy Black Pants",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_baggy_denim_female",
            "name": "pants_baggy_denim_female.glb",
            "display_name": "Baggy Denim Pants",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_baggy_camo_female",
            "name": "pants_baggy_camo_female.glb",
            "display_name": "Baggy Camo Pants",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_leggings_female",
            "name": "pants_leggings_female.glb",
            "display_name": "Leggings",
            "gender": "female",
            "style": "sporty",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_shorts_black_female",
            "name": "pants_shorts_black_female.glb",
            "display_name": "Black Shorts",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_shorts_camo_female",
            "name": "pants_shorts_camo_female.glb",
            "display_name": "Camo Shorts",
            "gender": "female",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_black_male",
            "name": "pants_black_male.glb",
            "display_name": "Black Pants",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_denim_male",
            "name": "pants_denim_male.glb",
            "display_name": "Denim Pants",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_camo_male",
            "name": "pants_camo_male.glb",
            "display_name": "Camo Pants",
            "gender": "male",
            "style": "streetwear",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_shorts_black_male",
            "name": "pants_shorts_black_male.glb",
            "display_name": "Black Shorts",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_shorts_denim_male",
            "name": "pants_shorts_denim_male.glb",
            "display_name": "Denim Shorts",
            "gender": "male",
            "style": "casual",
            "published": True,
        },
        {
            "type": "pants",
            "id": "pants_shorts_camo_male",
            "name": "pants_shorts_camo_male.glb",
            "display_name": "Camo Shorts",
            "gender": "male",
            "style": "streetwear",
            "published": True,
        },
    ]

    # Default skirts
    skirts = [
        {
            "type": "skirt",
            "id": "skirt_long_lace_female",
            "name": "skirt_long_lace_female.glb",
            "display_name": "Long Lace Skirt",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "id": "skirt_long_white_female",
            "name": "skirt_long_white_female.glb",
            "display_name": "Long White Skirt",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "id": "skirt_aline_black_female",
            "name": "skirt_aline_black_female.glb",
            "display_name": "A-line Black Skirt",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
        {
            "type": "skirt",
            "id": "skirt_short_black_female",
            "name": "skirt_short_black_female.glb",
            "display_name": "Short Black Skirt",
            "gender": "female",
            "style": "formal",
            "published": True,
        },
    ]

    # Default accessories
    accessories = [
        {
            "type": "accessory",
            "id": "accessories_skirt_lace_female",
            "name": "accessories_skirt_lace_female.glb",
            "display_name": "Lace Skirt Accessory",
            "gender": "female",
            "style": "y2k",
            "published": True,
        },
    ]

    # Seed all garments
    all_garments = shirts + pants + skirts + accessories

    for garment in all_garments:
        db.garments.update_one(
            {"id": garment["id"]},
            {
                "$set": {
                    **garment,
                    "updated_at": now,
                    "user_id": "default",
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
        db.garments.create_index([('id', ASCENDING)], unique=True)
        
        _seed_default_garments(db)
        print("✓ Database seeding completed successfully!")
        
    except Exception as e:
        print(f"✗ Error during seeding: {str(e)}")
        raise


if __name__ == "__main__":
    seed_default_garments()