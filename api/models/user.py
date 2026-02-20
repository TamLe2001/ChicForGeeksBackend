from datetime import datetime, timezone
from typing import Optional, Dict, Any
from werkzeug.security import check_password_hash, generate_password_hash


class User:
	"""User model class."""

	def __init__(
		self,
		name: str,
		email: str,
		profile_picture: Optional[str] = None,
		bio: Optional[str] = None,
		birthday: Optional[str] = None,
		role: str = 'user',
		created_at: Optional[datetime] = None,
	):
		"""
		Initialize a User.

		Args:
			name: User's name
			email: User's email
			profile_picture: URL to profile picture
			bio: User biography
			birthday: User's birthday
			role: User role (default: 'user')
			created_at: Creation timestamp
		"""
		self.name = name
		self.email = email
		self.profile_picture = profile_picture
		self.bio = bio
		self.birthday = birthday
		self.role = role
		self.created_at = created_at or datetime.now(timezone.utc)
		self.password_hash = None
		self._id = None  # Set by database

	@staticmethod
	def from_payload(payload: Optional[Dict[str, Any]]) -> 'User':
		"""Create User instance from API payload."""
		if payload is None:
			payload = {}

		return User(
			name=payload.get('name'),
			email=payload.get('email'),
			profile_picture=payload.get('profile_picture'),
			bio=payload.get('bio'),
			birthday=payload.get('birthday'),
			role=payload.get('role', 'user'),
			created_at=payload.get('created_at'),
		)

	@staticmethod
	def from_doc(user_doc: Optional[Dict[str, Any]]) -> Optional['User']:
		"""Create User instance from database document."""
		if not user_doc:
			return None

		user = User(
			name=user_doc.get('name'),
			email=user_doc.get('email'),
			profile_picture=user_doc.get('profile_picture'),
			bio=user_doc.get('bio'),
			birthday=user_doc.get('birthday'),
			role=user_doc.get('role', 'user'),
			created_at=user_doc.get('created_at'),
		)
		user._id = user_doc.get('_id')
		user.password_hash = user_doc.get('password_hash')
		return user

	def set_password(self, password: str) -> None:
		"""Hash and set password."""
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password: str) -> bool:
		"""Verify password against hash."""
		if self.password_hash is None:
			return False
		return check_password_hash(self.password_hash, password)

	def to_dict(self) -> Dict[str, Any]:
		"""Serialize to dictionary."""
		return {
			'id': str(self._id) if self._id else None,
			'name': self.name,
			'email': self.email,
			'profile_picture': self.profile_picture,
			'bio': self.bio,
			'birthday': self.birthday,
			'role': self.role,
			'created_at': self.created_at,
		}
