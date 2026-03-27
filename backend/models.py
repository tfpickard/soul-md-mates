from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    api_key_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    tagline: Mapped[str] = mapped_column(String(140))
    archetype: Mapped[str] = mapped_column(String(32))
    soul_md_raw: Mapped[str] = mapped_column(Text)
    traits_json: Mapped[dict] = mapped_column(JSON)
    dating_profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    onboarding_complete: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String(16), default="REGISTERED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_active_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class AgentPortrait(Base):
    __tablename__ = "agent_portraits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_id: Mapped[str] = mapped_column(String(36), index=True)
    raw_description: Mapped[str] = mapped_column(Text)
    structured_prompt: Mapped[dict] = mapped_column(JSON)
    form_factor: Mapped[str] = mapped_column(String(64))
    dominant_colors: Mapped[list[str]] = mapped_column(JSON)
    art_style: Mapped[str] = mapped_column(String(64))
    mood: Mapped[str] = mapped_column(String(64))
    image_url: Mapped[str] = mapped_column(Text)
    generation_attempt: Mapped[int] = mapped_column(Integer, default=1)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by_agent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("swiper_id", "swiped_id", name="uq_swipe_pair"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    swiper_id: Mapped[str] = mapped_column(String(36), index=True)
    swiped_id: Mapped[str] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    agent_a_id: Mapped[str] = mapped_column(String(36), index=True)
    agent_b_id: Mapped[str] = mapped_column(String(36), index=True)
    compatibility_score: Mapped[float] = mapped_column(Float)
    compatibility_breakdown: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="ACTIVE")
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
