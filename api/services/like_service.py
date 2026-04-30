"""Service for managing outfit likes."""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from api.models.like import Like


class LikeService:
    """Service for managing outfit likes."""

    def __init__(self, db):
        """
        Initialize LikeService.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    def get_outfit_likes(self, outfit_id: ObjectId) -> Tuple[Dict[str, Any], int]:
        """Get all likes for an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            likes_cursor = self.db.likes.find(
                {'outfit_id': outfit_id}
            ).sort('created_at', -1)
            
            likes = [Like.from_doc(doc).to_dict() for doc in likes_cursor]
            
            return {
                'status': 'success',
                'count': len(likes),
                'likes': likes
            }, 200
        except Exception as e:
            return {'error': f'Failed to fetch likes: {str(e)}'}, 500

    def like_outfit(self, outfit_id: ObjectId, user_id: ObjectId) -> Tuple[Dict[str, Any], int]:
        """Like an outfit. If already liked, return existing like.
        
        Args:
            outfit_id: ObjectId of the outfit
            user_id: ObjectId of the user
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            like_doc = {
                'outfit_id': outfit_id,
                'user_id': user_id,
                'created_at': datetime.now(timezone.utc),
            }

            try:
                result = self.db.likes.insert_one(like_doc)
                created = self.db.likes.find_one({'_id': result.inserted_id})
                return Like.from_doc(created).to_dict(), 201
            except DuplicateKeyError:
                # Already liked - return existing like with 200 status
                existing = self.db.likes.find_one({
                    'outfit_id': outfit_id,
                    'user_id': user_id
                })
                return Like.from_doc(existing).to_dict(), 200

        except Exception as e:
            return {'error': f'Failed to like outfit: {str(e)}'}, 500

    def unlike_outfit(self, outfit_id: ObjectId, user_id: ObjectId) -> Tuple[Dict[str, Any], int]:
        """Unlike an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            user_id: ObjectId of the user
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            result = self.db.likes.delete_one({
                'outfit_id': outfit_id,
                'user_id': user_id
            })

            if result.deleted_count == 0:
                return {'error': 'like not found'}, 404

            return {'status': 'unliked', 'message': 'Successfully unliked outfit'}, 200

        except Exception as e:
            return {'error': f'Failed to unlike outfit: {str(e)}'}, 500

    def is_liked_by_user(self, outfit_id: ObjectId, user_id: ObjectId) -> bool:
        """Check if an outfit is liked by a user.
        
        Args:
            outfit_id: ObjectId of the outfit
            user_id: ObjectId of the user
            
        Returns:
            True if liked, False otherwise
        """
        try:
            like = self.db.likes.find_one({
                'outfit_id': outfit_id,
                'user_id': user_id
            })
            return like is not None
        except Exception:
            return False

    def get_like_count(self, outfit_id: ObjectId) -> int:
        """Get the number of likes for an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            
        Returns:
            Number of likes
        """
        try:
            return self.db.likes.count_documents({'outfit_id': outfit_id})
        except Exception:
            return 0
