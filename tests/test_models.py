"""Tests for SQLAlchemy models."""


from netmap.database import Base
from netmap.models import BaseModel


def test_base_model_is_abstract():
    """BaseModel is declared abstract and not mapped to a table."""
    assert BaseModel.__abstract__ is True


def test_base_model_inherits_base():
    """BaseModel inherits from the declarative Base."""
    assert issubclass(BaseModel, Base)


def test_base_model_has_expected_attributes():
    """BaseModel defines id, created_at, updated_at as Column attributes."""
    assert "id" in BaseModel.__dict__
    assert "created_at" in BaseModel.__dict__
    assert "updated_at" in BaseModel.__dict__
