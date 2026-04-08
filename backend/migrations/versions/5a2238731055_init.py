"""init

Revision ID: 5a2238731055
Revises: 
Create Date: 2026-04-08 09:40:02.195816

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a2238731055'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 检查表是否存在，如果不存在则创建
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # User favorites table
    if 'user_favorites' not in inspector.get_table_names():
        op.create_table('user_favorites',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('album_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_user_favorites_user_id', 'user_favorites', ['user_id'], unique=False)
        op.create_index('idx_user_favorites_album_id', 'user_favorites', ['album_id'], unique=False)
        op.create_index('idx_user_favorites_user_album', 'user_favorites', ['user_id', 'album_id'], unique=True)
    
    # User history table
    if 'user_history' not in inspector.get_table_names():
        op.create_table('user_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('album_id', sa.Integer(), nullable=False),
            sa.Column('viewed_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['album_id'], ['albums.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_user_history_user_id', 'user_history', ['user_id'], unique=False)
        op.create_index('idx_user_history_album_id', 'user_history', ['album_id'], unique=False)
        op.create_index('idx_user_history_viewed_at', 'user_history', ['viewed_at'], unique=False)
        op.create_index('idx_user_history_user_viewed', 'user_history', ['user_id', 'viewed_at'], unique=False)
    
    # Add view_count to albums
    columns = [col['name'] for col in inspector.get_columns('albums')]
    if 'view_count' not in columns:
        op.add_column('albums', sa.Column('view_count', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    # 注意：生产环境不要轻易降级
    op.drop_column('albums', 'view_count')
    op.drop_table('user_history')
    op.drop_table('user_favorites')