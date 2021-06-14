#!/usr/bin/env python3

from app.db.crud import create_user
from app.db.schemas import UserCreate
from app.db.session import SessionLocal


def init() -> None:
    db = SessionLocal()

    create_user(
        db,
        UserCreate(
            email="test@refns.com",
            username="chewie",
            name="wookie_god",
            organization="UMMI",
            password="mega_secret",
            is_active=True,
            is_contributor=True,
            is_superuser=True,
            can_sync=True,
        ),
    )


if __name__ == "__main__":
    print("Creating superuser test@refns.com")
    init()
    print("Superuser created")
