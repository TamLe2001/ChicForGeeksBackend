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
        """Get all comments for an outfit with author info via lookup.
        
        Args:
            outfit_id: ObjectId of the outfit
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        try:
            pipeline = [
                {'$match': {'outfit_id': outfit_id}},
                {'$sort': {'created_at': -1}},
                {
                    '$lookup': {
                        'from': 'users',
                        'localField': 'user_id',
                        'foreignField': '_id',
                        'as': 'author'
                    }
                },
                {'$unwind': {'path': '$author', 'preserveNullAndEmptyArrays': True}},
                {
                    '$project': {
                        '_id': 1,
                        'content': 1,
                        'outfit_id': 1,
                        'user_id': 1,
                        'author_name': '$author.name',
                        'author_profile_picture': '$author.profile_picture',
                        'created_at': 1,
                    }
                }
            ]
            
            docs = list(self.db.comments.aggregate(pipeline))
            comments = [self._doc_to_dict(doc) for doc in docs]
            
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
            user_name: Name of the user (validation only, not stored)
            user_profile_picture: User's profile picture URL (validation only, not stored)
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
                'content': content,
                'created_at': datetime.now(timezone.utc),
                'updated_at': datetime.now(timezone.utc),
            }

            result = self.db.comments.insert_one(comment_doc)
            created = self.db.comments.find_one({'_id': result.inserted_id})
            comment_dict = Comment.from_doc(created).to_dict()
            
            # Fetch author info for response
            user = self.db.users.find_one({'_id': user_id})
            if user:
                comment_dict['author_name'] = user.get('name')
                comment_dict['author_profile_picture'] = user.get('profile_picture')
            
            return comment_dict, 201

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

    def _doc_to_dict(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert aggregated comment document to dict with author info.
        
        Args:
            doc: Document from aggregation pipeline (includes author fields)
            
        Returns:
            Dictionary representation of comment
        """
        return {
            'id': str(doc.get('_id')),
            'content': doc.get('content', ''),
            'outfit_id': str(doc.get('outfit_id')),
            'user_id': str(doc.get('user_id')),
            'author_name': doc.get('author_name'),
            'author_profile_picture': doc.get('author_profile_picture'),
            'created_at': doc.get('created_at'),
        }
