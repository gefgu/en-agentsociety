from datetime import datetime
from typing import Any
from decimal import Decimal
from sqlalchemy import Text, TIMESTAMP, DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base

__all__ = ["Base", "BaseNoInit", "TABLE_PREFIX"]


# The base class of sqlalchemy models
Base = declarative_base(
    type_annotation_map={
        Any: JSONB,
        str: Text,
        datetime: TIMESTAMP(timezone=True),
        Decimal: DECIMAL,
    }
)
"""
If the table needs to be initialized, use this base class.
"""

BaseNoInit = declarative_base(
    type_annotation_map={
        Any: JSONB,
        str: Text,
        datetime: TIMESTAMP(timezone=True),
        Decimal: DECIMAL,
    }
)
"""
If the table does not need to be initialized, use this base class.
"""

TABLE_PREFIX = "as_"
