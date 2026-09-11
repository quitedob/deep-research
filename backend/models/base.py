"""Declarative base; PostgreSQL schema creation is owned by the DAO initializer."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
