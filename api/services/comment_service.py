"""Service for managing outfit comments."""

from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime, timezone
from bson import ObjectId
from api.models.comment import Comment


class CommentService:
    """Service for managing outfit comments."""

    def __init__(self, db):
        """
        Initialize CommentService.

        Args:
            db: MongoDB database instance
        """
        self.db = db

    MAX_COMMENT_LENGTH = 1000

    def get_outfit_comments(self, outfit_id: ObjectId) -> Tuple[Dict[str, Any], int]:
        """Get all comments for an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            comments_cursor = self.db.comments.find(
                {'outfit_id': outfit_id}
            ).sort('created_at', -1)
            
            comments = [Comment.from_doc(doc).to_dict() for doc in comments_cursor]
            
            return {
                'status': 'success',
                'count': len(comments),
                'comments': comments
            }, 200
        except Exception as e:
            return {'error': f'Failed to fetch comments: {str(e)}'}, 500

    def create_comment(
        self,
        outfit_id: ObjectId,
        user_id: ObjectId,
        user_name: str,
        user_profile_picture: Optional[str],
        content: str
    ) -> Tuple[Dict[str, Any], int]:
        """Create a comment on an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            user_id: ObjectId of the user creating comment
            user_name: Name of the user
            user_profile_picture: User's profile picture URL
            content: Comment content
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Validate content
            content = (content or '').strip()
            if not content:
                return {'error': 'content is required'}, 400
            if len(content) > self.MAX_COMMENT_LENGTH:
                return {'error': f'content must be at most {self.MAX_COMMENT_LENGTH} characters'}, 400

            comment_doc = {
                'outfit_id': outfit_id,
                'user_id': user_id,
                'author': {
                    'name': user_name,
                    'profile_picture': user_profile_picture,
                },
                'content': content,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
            }

            result = self.db.comments.insert_one(comment_doc)
            created = self.db.comments.find_one({'_id': result.inserted_id})
            return Comment.from_doc(created).to_dict(), 201

        except Exception as e:
            return {'error': f'Failed to create comment: {str(e)}'}, 500

    def update_comment(
        self,
        comment_id: ObjectId,
        outfit_id: ObjectId,
        current_user_id: ObjectId,
        current_user_role: str,
        content: str
    ) -> Tuple[Dict[str, Any], int]:
        """Update a comment.
        
        Args:
            comment_id: ObjectId of the comment
            outfit_id: ObjectId of the outfit
            current_user_id: ObjectId of the current user
            current_user_role: Role of the current user
            content: New comment content
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Find comment
            comment = self.db.comments.find_one({
                '_id': comment_id,
                'outfit_id': outfit_id
            })
            
            if not comment:
                return {'error': 'comment not found'}, 404

            # Check authorization
            is_owner = comment.get('user_id') == current_user_id
            is_admin = current_user_role == 'admin'
            
            if not is_owner and not is_admin:
                return {'error': 'forbidden'}, 403

            # Validate content
            content = (content or '').strip()
            if not content:
                return {'error': 'content is required'}, 400
            if len(content) > self.MAX_COMMENT_LENGTH:
                return {'error': f'content must be at most {self.MAX_COMMENT_LENGTH} characters'}, 400

            # Update comment
            self.db.comments.update_one(
                {'_id': comment_id},
                {'$set': {
                    'content': content,
                    'updated_at': datetime.now(timezone.utc)
                }},
            )

            updated = self.db.comments.find_one({'_id': comment_id})
            return Comment.from_doc(updated).to_dict(), 200

        except Exception as e:
            return {'error': f'Failed to update comment: {str(e)}'}, 500

    def delete_comment(
        self,
        comment_id: ObjectId,
        outfit_id: ObjectId,
        current_user_id: ObjectId,
        current_user_role: str
    ) -> Tuple[Dict[str, Any], int]:
        """Delete a comment.
        
        Args:
            comment_id: ObjectId of the comment
            outfit_id: ObjectId of the outfit
            current_user_id: ObjectId of the current user
            current_user_role: Role of the current user
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            # Find comment
            comment = self.db.comments.find_one({
                '_id': comment_id,
                'outfit_id': outfit_id
            })
            
            if not comment:
                return {'error': 'comment not found'}, 404

            # Check authorization
            is_owner = comment.get('user_id') == current_user_id
            is_admin = current_user_role == 'admin'
            
            if not is_owner and not is_admin:
                return {'error': 'forbidden'}, 403

            # Delete comment
            self.db.comments.delete_one({'_id': comment_id})
            
            return {'status': 'deleted', 'message': 'Comment deleted successfully'}, 200

        except Exception as e:
            return {'error': f'Failed to delete comment: {str(e)}'}, 500

    def get_comment_count(self, outfit_id: ObjectId) -> int:
        """Get the number of comments on an outfit.
        
        Args:
            outfit_id: ObjectId of the outfit
            
        Returns:
            Number of comments
        """
        try:
            return self.db.comments.count_documents({'outfit_id': outfit_id})
        except Exception:
            return 0
