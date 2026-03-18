from datetime import datetime, timezone
from typing import Optional, Dict, Any
from api.models.garment import Shirt, Pants, Skirt, Accessory


class Outfit:
	"""Outfit model class."""

	def __init__(
		self,
		name: str,
		user_id: str,
		bio: Optional[str] = None,
		shirt: Optional[Shirt] = None,
		pants: Optional[Pants] = None,
		skirt: Optional[Skirt] = None,
		accessory: Optional[Accessory] = None,
		published: bool = False,
		created_at: Optional[datetime] = None,
	):
		"""
		Initialize an Outfit.

		Args:
			name: Outfit name
			user_id: User ID who created this outfit
			bio: Outfit description/bio
			shirt: Shirt garment instance
			pants: Pants garment instance
			skirt: Skirt garment instance
			accessory: Accessory garment instance
			published: Whether outfit is published
			created_at: Creation timestamp
		"""
		self.name = name
		self.user_id = user_id
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
			bio=payload.get('bio'),
			shirt=Shirt.from_dict(payload.get('shirt')) if payload.get('shirt') else None,
			pants=Pants.from_dict(payload.get('pants')) if payload.get('pants') else None,
			skirt=Skirt.from_dict(payload.get('skirt')) if payload.get('skirt') else None,
			accessory=Accessory.from_dict(payload.get('accessory')) if payload.get('accessory') else None,
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
			bio=outfit_doc.get('bio'),
			shirt=Shirt.from_dict(outfit_doc.get('shirt')) if outfit_doc.get('shirt') else None,
			pants=Pants.from_dict(outfit_doc.get('pants')) if outfit_doc.get('pants') else None,
			skirt=Skirt.from_dict(outfit_doc.get('skirt')) if outfit_doc.get('skirt') else None,
			accessory=Accessory.from_dict(outfit_doc.get('accessory')) if outfit_doc.get('accessory') else None,
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
			'shirt': self.shirt.to_dict() if self.shirt else None,
			'pants': self.pants.to_dict() if self.pants else None,
			'skirt': self.skirt.to_dict() if self.skirt else None,
			'accessory': self.accessory.to_dict() if self.accessory else None,
			'published': self.published,
			'created_at': self.created_at,
		}
	
