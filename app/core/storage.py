from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings


class StorageBackend(ABC):
    """ストレージ抽象インターフェイス。LocalStorage ↔ S3Storage 交換可能。"""

    @abstractmethod
    def save(self, source_path: str, dest_key: str) -> str:
        """ファイルを保存し、アクセス可能な URL を返す。"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """ファイルを削除する。"""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """キーからアクセス可能な URL を返す。"""


class LocalStorage(StorageBackend):
    """開発用: ローカルファイルシステムに保存する実装。"""

    def __init__(self) -> None:
        self.base_dir = Path(settings.UPLOAD_DIR)
        self.base_url = settings.UPLOAD_BASE_URL

    def save(self, source_path: str, dest_key: str) -> str:
        dest = self.base_dir / dest_key
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(source_path, str(dest))
        return self.get_url(dest_key)

    def delete(self, key: str) -> None:
        path = self.base_dir / key
        if path.exists():
            os.remove(str(path))

    def get_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"


storage = LocalStorage()
