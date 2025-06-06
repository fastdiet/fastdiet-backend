"""Create confirmation_codes table

Revision ID: f96af77af390
Revises: e805a8ffaefa
Create Date: 2025-04-15 13:14:44.552324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f96af77af390'
down_revision: Union[str, None] = 'e805a8ffaefa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('confirmation_codes',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=255), nullable=False),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('used', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_confirmation_codes_code'), 'confirmation_codes', ['code'], unique=False)
    op.create_index(op.f('ix_confirmation_codes_id'), 'confirmation_codes', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_confirmation_codes_id'), table_name='confirmation_codes')
    op.drop_index(op.f('ix_confirmation_codes_code'), table_name='confirmation_codes')
    op.drop_table('confirmation_codes')
    # ### end Alembic commands ###
