from fastapi import APIRouter

api_router = APIRouter()

# 各ドメインルーターをここに登録する。
# 例) api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
