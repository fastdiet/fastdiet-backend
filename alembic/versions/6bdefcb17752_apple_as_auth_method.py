"""apple as auth method

Revision ID: 6bdefcb17752
Revises: 1951d42bd83d
Create Date: 2025-10-29 19:17:07.091667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bdefcb17752'
down_revision: Union[str, None] = '1951d42bd83d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE users 
        MODIFY COLUMN auth_method 
        ENUM('google', 'traditional', 'apple') 
        NOT NULL 
        DEFAULT 'traditional';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE users 
        MODIFY COLUMN auth_method 
        ENUM('google', 'traditional') 
        NOT NULL 
        DEFAULT 'traditional';
    """)
