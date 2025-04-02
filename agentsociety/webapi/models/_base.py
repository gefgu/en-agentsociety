from datetime import datetime
from typing import Any

from sqlalchemy import Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

__all__ = ["Base", "TABLE_PREFIX"]

# The base class of sqlalchemy models
Base = declarative_base(
    type_annotation_map={Any: JSONB, str: Text, datetime: TIMESTAMP(timezone=True)}
)

TABLE_PREFIX = "as_"
