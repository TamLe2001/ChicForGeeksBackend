from datetime import datetime, timezone
from typing import Optional, Dict, Any
from api.models.garment import Hat, Shirt, Pants, Shoes


class Outfit:
	"""Outfit model class."""

	def __init__(
		self,
		name: str,
		user_id: str,
		style: Optional[str] = None,
		bio: Optional[str] = None,
		hat: Optional[Hat] = None,
		shirt: Optional[Shirt] = None,
		pants: Optional[Pants] = None,
		shoes: Optional[Shoes] = None,
		published: bool = False,
		created_at: Optional[datetime] = None,
	):
		"""
		Initialize an Outfit.

		Args:
			name: Outfit name
			user_id: User ID who created this outfit
			style: Style/genre of the outfit
			bio: Outfit description/bio
			hat: Hat garment instance
			shirt: Shirt garment instance
			pants: Pants garment instance
			shoes: Shoes garment instance
			published: Whether outfit is published
			created_at: Creation timestamp
		"""
		self.name = name
		self.user_id = user_id
		self.style = style
		self.bio = bio
		self.hat = hat
		self.shirt = shirt
		self.pants = pants
		self.shoes = shoes
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
			style=payload.get('style'),
			bio=payload.get('bio'),
			hat=Hat.from_dict(payload.get('hat')) if payload.get('hat') else None,
			shirt=Shirt.from_dict(payload.get('shirt')) if payload.get('shirt') else None,
			pants=Pants.from_dict(payload.get('pants')) if payload.get('pants') else None,
			shoes=Shoes.from_dict(payload.get('shoes')) if payload.get('shoes') else None,
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
			style=outfit_doc.get('style'),
			bio=outfit_doc.get('bio'),
			hat=Hat.from_dict(outfit_doc.get('hat')) if outfit_doc.get('hat') else None,
			shirt=Shirt.from_dict(outfit_doc.get('shirt')) if outfit_doc.get('shirt') else None,
			pants=Pants.from_dict(outfit_doc.get('pants')) if outfit_doc.get('pants') else None,
			shoes=Shoes.from_dict(outfit_doc.get('shoes')) if outfit_doc.get('shoes') else None,
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
			'style': self.style,
			'bio': self.bio,
			'hat': self.hat.to_dict() if self.hat else None,
			'shirt': self.shirt.to_dict() if self.shirt else None,
			'pants': self.pants.to_dict() if self.pants else None,
			'shoes': self.shoes.to_dict() if self.shoes else None,
			'published': self.published,
			'created_at': self.created_at,
		}
	
