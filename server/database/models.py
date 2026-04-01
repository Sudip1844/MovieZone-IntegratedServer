# IntegratedServer/database/models.py
# SQLAlchemy Models for all tables

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, UniqueConstraint, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class MovieLink(Base):
    """Single movie download links"""
    __tablename__ = 'movie_links'
    
    id = Column(Integer, primary_key=True)
    movie_name = Column(String, nullable=False)
    original_link = Column(String, nullable=False)
    short_id = Column(String, unique=True, nullable=False)
    views = Column(Integer, default=0)
    date_added = Column(DateTime, default=func.now())
    ads_enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<MovieLink {self.short_id}: {self.movie_name}>"


class QualityMovieLink(Base):
    """Multi-quality movie downloads (480p/720p/1080p)"""
    __tablename__ = 'quality_movie_links'
    
    id = Column(Integer, primary_key=True)
    movie_name = Column(String, nullable=False)
    short_id = Column(String, unique=True, nullable=False)
    quality_480p = Column(String, nullable=True)
    quality_720p = Column(String, nullable=True)
    quality_1080p = Column(String, nullable=True)
    views = Column(Integer, default=0)
    date_added = Column(DateTime, default=func.now())
    ads_enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<QualityMovieLink {self.short_id}: {self.movie_name}>"


class QualityEpisode(Base):
    """Series with episodes (JSON format)"""
    __tablename__ = 'quality_episodes'
    
    id = Column(Integer, primary_key=True)
    series_name = Column(String, nullable=False)
    short_id = Column(String, unique=True, nullable=False)
    start_from_episode = Column(Integer, default=1)
    episodes = Column(Text, nullable=False)  # JSON string
    views = Column(Integer, default=0)
    date_added = Column(DateTime, default=func.now())
    ads_enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<QualityEpisode {self.short_id}: {self.series_name}>"


class QualityZip(Base):
    """Episode range downloads"""
    __tablename__ = 'quality_zips'
    
    id = Column(Integer, primary_key=True)
    movie_name = Column(String, nullable=False)
    short_id = Column(String, unique=True, nullable=False)
    from_episode = Column(Integer, nullable=False)
    to_episode = Column(Integer, nullable=False)
    quality_480p = Column(String, nullable=True)
    quality_720p = Column(String, nullable=True)
    quality_1080p = Column(String, nullable=True)
    views = Column(Integer, default=0)
    date_added = Column(DateTime, default=func.now())
    ads_enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<QualityZip {self.short_id}: Episode {self.from_episode}-{self.to_episode}>"


class ApiToken(Base):
    """API authentication tokens"""
    __tablename__ = 'api_tokens'
    
    id = Column(Integer, primary_key=True)
    token_name = Column(String, nullable=False)
    token_value = Column(String, unique=True, nullable=False)
    token_type = Column(String, default='single')  # 'single', 'quality', 'episode', 'zip'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ApiToken {self.token_name}>"


class AdminSetting(Base):
    """Admin credentials"""
    __tablename__ = 'admin_settings'
    
    id = Column(Integer, primary_key=True)
    admin_id = Column(String, unique=True, nullable=False)
    admin_password = Column(String, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AdminSetting {self.admin_id}>"


class AdViewSession(Base):
    """IP-based 5-minute timer for ads skip system"""
    __tablename__ = 'ad_view_sessions'
    
    id = Column(Integer, primary_key=True)
    ip_address = Column(String, nullable=False)
    short_id = Column(String, nullable=False)
    link_type = Column(String, default='single')  # 'single', 'quality', 'episode', 'zip'
    viewed_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, default=func.now())
    
    # Unique constraint to prevent duplicate sessions
    __table_args__ = (
        UniqueConstraint('ip_address', 'short_id', 'link_type', name='unique_session'),
    )
    
    def __repr__(self):
        return f"<AdViewSession {self.ip_address} - {self.short_id}>"
