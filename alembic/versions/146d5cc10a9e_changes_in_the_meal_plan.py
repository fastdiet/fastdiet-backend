"""Changes in the meal plan

Revision ID: 146d5cc10a9e
Revises: 30c324efc3bb
Create Date: 2025-05-15 13:55:38.578295

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '146d5cc10a9e'
down_revision: Union[str, None] = '30c324efc3bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('meal_items', sa.Column('recipe_id', sa.Integer(), nullable=False))
    op.alter_column('meal_items', 'day',
               existing_type=mysql.VARCHAR(length=50),
               type_=sa.Integer(),
               existing_nullable=False)
    op.create_foreign_key(None, 'meal_items', 'recipes', ['recipe_id'], ['id'], ondelete='CASCADE')
    op.drop_column('meal_items', 'item_id')
    op.drop_column('meal_items', 'position')
    op.drop_column('meal_items', 'item_type')
    op.drop_column('meal_items', 'date')
    op.drop_column('meal_plans', 'start_date')
    op.drop_column('user_preferences', 'low_fodmap')
    op.drop_column('user_preferences', 'gluten_free')
    op.drop_column('user_preferences', 'vegetarian')
    op.drop_column('user_preferences', 'dairy_free')
    op.drop_column('user_preferences', 'vegan')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user_preferences', sa.Column('vegan', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('user_preferences', sa.Column('dairy_free', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('user_preferences', sa.Column('vegetarian', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('user_preferences', sa.Column('gluten_free', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('user_preferences', sa.Column('low_fodmap', mysql.TINYINT(display_width=1), autoincrement=False, nullable=True))
    op.add_column('meal_plans', sa.Column('start_date', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False))
    op.add_column('meal_items', sa.Column('date', mysql.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False))
    op.add_column('meal_items', sa.Column('item_type', mysql.ENUM('RECIPE', 'PRODUCT', 'INGREDIENT', 'MENU_ITEM', 'CUSTOM_FOOD'), nullable=False))
    op.add_column('meal_items', sa.Column('position', mysql.INTEGER(), autoincrement=False, nullable=False))
    op.add_column('meal_items', sa.Column('item_id', mysql.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'meal_items', type_='foreignkey')
    op.alter_column('meal_items', 'day',
               existing_type=sa.Integer(),
               type_=mysql.VARCHAR(length=50),
               existing_nullable=False)
    op.drop_column('meal_items', 'recipe_id')
    # ### end Alembic commands ###
