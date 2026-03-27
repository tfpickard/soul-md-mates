from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import HumanUserCreate, HumanUserResponse
from services.users import create_human_user, serialize_human_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=HumanUserResponse)
async def register_user(payload: HumanUserCreate, db: AsyncSession = Depends(get_db)) -> HumanUserResponse:
    user = await create_human_user(db, email=payload.email, password=payload.password)
    await db.commit()
    await db.refresh(user)
    return serialize_human_user(user)
