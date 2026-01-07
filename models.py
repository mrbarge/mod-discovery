"""
Database Models

Defines the database schema for ModPlayer.
"""
from datetime import datetime
from typing import Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class DailySelection(db.Model):
    """Represents a daily module selection."""
    
    __tablename__ = 'daily_selections'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[datetime] = mapped_column(db.Date, unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    modules = relationship(
        'Module',
        secondary='selection_modules',
        back_populates='daily_selections',
        lazy='joined'
    )
    
    def __repr__(self) -> str:
        return f'<DailySelection {self.date}>'


class Module(db.Model):
    """Represents a module file from Mod Archive."""
    
    __tablename__ = 'modules'
    
    id: Mapped[int] = mapped_column(primary_key=True)  # Mod Archive module ID
    filename: Mapped[str] = mapped_column(db.String(255), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(db.String(255))
    artist: Mapped[Optional[str]] = mapped_column(db.String(255))
    format: Mapped[Optional[str]] = mapped_column(db.String(10), index=True)
    size: Mapped[Optional[int]] = mapped_column(db.Integer)  # File size in bytes
    download_url: Mapped[Optional[str]] = mapped_column(db.String(512))
    modarchive_url: Mapped[Optional[str]] = mapped_column(db.String(512))
    date_added: Mapped[Optional[datetime]] = mapped_column(db.Date)  # When added to Mod Archive
    source_type: Mapped[Optional[str]] = mapped_column(db.String(20), index=True)  # recent/rated/random
    cached_at: Mapped[Optional[datetime]] = mapped_column(db.DateTime)
    
    # Relationships
    daily_selections = relationship(
        'DailySelection',
        secondary='selection_modules',
        back_populates='modules'
    )
    ratings = relationship('UserRating', back_populates='module', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f'<Module {self.id}: {self.filename}>'
    
    def to_dict(self, include_rating: bool = False) -> dict:
        """Convert module to dictionary representation."""
        data = {
            'id': self.id,
            'filename': self.filename,
            'title': self.title,
            'artist': self.artist,
            'format': self.format,
            'size': self.size,
            'download_url': self.download_url,
            'modarchive_url': self.modarchive_url,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'source_type': self.source_type,
        }
        
        if include_rating and self.ratings:
            rating = self.ratings[0]  # Should only be one rating per user
            data['user_rating'] = {
                'rating': rating.rating,
                'comment': rating.comment,
                'rated_at': rating.rated_at.isoformat(),
            }
        else:
            data['user_rating'] = None
        
        return data


class SelectionModule(db.Model):
    """Join table linking daily selections to modules."""
    
    __tablename__ = 'selection_modules'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    selection_id: Mapped[int] = mapped_column(ForeignKey('daily_selections.id'), nullable=False, index=True)
    module_id: Mapped[int] = mapped_column(ForeignKey('modules.id'), nullable=False, index=True)
    position: Mapped[int] = mapped_column(db.Integer, nullable=False)  # Order in list (1-5)
    
    __table_args__ = (
        UniqueConstraint('selection_id', 'module_id', name='uq_selection_module'),
    )
    
    def __repr__(self) -> str:
        return f'<SelectionModule selection={self.selection_id} module={self.module_id} pos={self.position}>'


class UserRating(db.Model):
    """Represents a user rating for a module."""
    
    __tablename__ = 'user_ratings'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey('modules.id'), nullable=False, index=True, unique=True)
    rating: Mapped[int] = mapped_column(db.Integer, nullable=False)  # 1-5 stars
    comment: Mapped[Optional[str]] = mapped_column(db.Text)
    rated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    module = relationship('Module', back_populates='ratings')
    
    def __repr__(self) -> str:
        return f'<UserRating module={self.module_id} rating={self.rating}>'
    
    def to_dict(self) -> dict:
        """Convert rating to dictionary representation."""
        return {
            'id': self.id,
            'module_id': self.module_id,
            'rating': self.rating,
            'comment': self.comment,
            'rated_at': self.rated_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
