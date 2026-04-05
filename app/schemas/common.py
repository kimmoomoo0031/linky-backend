from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    has_next: bool


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: PaginatedData[T]


class MessageResponse(BaseModel):
    success: bool = True
    message: str = "OK"
