from datetime import datetime, timezone
from typing import Optional, Dict, Any
from api.models.garment import Shirt, Pants, Skirt, Accessory
from api.models.garment.enums.gender import Gender


class Outfit:
	"""Outfit model class."""

	def __init__(
		self,
		name: str,
		user_id: str,
		gender: Gender,
		bio: Optional[str] = None,
		shirt: Optional[str] = None,
		pants: Optional[str] = None,
		skirt: Optional[str] = None,
		accessory: Optional[str] = None,
		published: bool = False,
		created_at: Optional[datetime] = None,
	):
		"""
		Initialize an Outfit.

		Args:
			name: Outfit name
			user_id: User ID who created this outfit
			gender: Gender of the outfit
			bio: Outfit description/bio
			shirt: Shirt garment id
			pants: Pants garment id
			skirt: Skirt garment id
			accessory: Accessory garment id
			published: Whether outfit is published
			created_at: Creation timestamp
		"""
		self.name = name
		self.user_id = user_id
		self.gender = gender
		self.bio = bio
		self.shirt = shirt
		self.pants = pants
		self.skirt = skirt
		self.accessory = accessory
		self.published = published
		self.created_at = created_at or datetime.now(timezone.utc)
		self._id = None  # Set by database

	@staticmethod
	def from_payload(payload: Optional[Dict[str, Any]]) -> 'Outfit':
		"""Create Outfit instance from API payload."""
		if payload is None:
			payload = {}

		return Outfit(
			name=payload.get('name'),
			user_id=payload.get('user_id'),
			gender=Gender(payload.get('gender')) if payload.get('gender') else None,
			bio=payload.get('bio'),
			shirt=payload.get('shirt'),  
			pants=payload.get('pants'),
			skirt=payload.get('skirt'),
			accessory=payload.get('accessory'),
			published=payload.get('published', False),
			created_at=payload.get('created_at'),
		)

	@staticmethod
	def from_doc(outfit_doc: Optional[Dict[str, Any]]) -> Optional['Outfit']:
		"""Create Outfit instance from database document."""
		if not outfit_doc:
			return None

		outfit = Outfit(
			name=outfit_doc.get('name'),
			user_id=outfit_doc.get('user_id'),
			gender=Gender(outfit_doc.get('gender')) if outfit_doc.get('gender') else None,
			bio=outfit_doc.get('bio'),
			shirt=outfit_doc.get('shirt'),
			pants=outfit_doc.get('pants'),
			skirt=outfit_doc.get('skirt'),
			accessory=outfit_doc.get('accessory'),
			published=outfit_doc.get('published', False),
			created_at=outfit_doc.get('created_at'),
		)
		outfit._id = outfit_doc.get('_id')
		return outfit

	def to_dict(self) -> Dict[str, Any]:
		"""Serialize to dictionary."""
		return {
			'id': str(self._id) if self._id else None,
			'name': self.name,
			'user_id': self.user_id,
			'bio': self.bio,
			'gender': self.gender.value if self.gender else None,
			'shirt': self.shirt,
			'pants': self.pants,
			'skirt': self.skirt,
			'accessory': self.accessory,
			'published': self.published,
			'created_at': self.created_at,
		}
	
