"""add missing columns: follows/leads/opens/sends on metrics, serving_hold_reasons on creatives

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -- campaign_daily_metrics: add follows, leads, opens, sends --
    op.add_column("campaign_daily_metrics", sa.Column("follows", sa.Integer(), server_default="0"))
    op.add_column("campaign_daily_metrics", sa.Column("leads", sa.Integer(), server_default="0"))
    op.add_column("campaign_daily_metrics", sa.Column("opens", sa.Integer(), server_default="0"))
    op.add_column("campaign_daily_metrics", sa.Column("sends", sa.Integer(), server_default="0"))

    # -- creative_daily_metrics: add follows, leads, opens, sends --
    op.add_column("creative_daily_metrics", sa.Column("follows", sa.Integer(), server_default="0"))
    op.add_column("creative_daily_metrics", sa.Column("leads", sa.Integer(), server_default="0"))
    op.add_column("creative_daily_metrics", sa.Column("opens", sa.Integer(), server_default="0"))
    op.add_column("creative_daily_metrics", sa.Column("sends", sa.Integer(), server_default="0"))

    # -- creatives: add serving_hold_reasons --
    op.add_column("creatives", sa.Column("serving_hold_reasons", sa.Text()))


def downgrade() -> None:
    op.drop_column("creatives", "serving_hold_reasons")

    op.drop_column("creative_daily_metrics", "sends")
    op.drop_column("creative_daily_metrics", "opens")
    op.drop_column("creative_daily_metrics", "leads")
    op.drop_column("creative_daily_metrics", "follows")

    op.drop_column("campaign_daily_metrics", "sends")
    op.drop_column("campaign_daily_metrics", "opens")
    op.drop_column("campaign_daily_metrics", "leads")
    op.drop_column("campaign_daily_metrics", "follows")
