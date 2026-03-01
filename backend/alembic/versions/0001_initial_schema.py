"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-03-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ad_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("currency", sa.Text()),
        sa.Column("type", sa.Text()),
        sa.Column("is_test", sa.Boolean()),
        sa.Column("created_at", sa.Text()),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("ad_accounts.id")),
        sa.Column("name", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("type", sa.Text()),
        sa.Column("daily_budget", sa.Float()),
        sa.Column("daily_budget_currency", sa.Text()),
        sa.Column("total_budget", sa.Float()),
        sa.Column("cost_type", sa.Text()),
        sa.Column("unit_cost", sa.Float()),
        sa.Column("bid_strategy", sa.Text()),
        sa.Column("creative_selection", sa.Text()),
        sa.Column("offsite_delivery_enabled", sa.Boolean()),
        sa.Column("audience_expansion_enabled", sa.Boolean()),
        sa.Column("campaign_group", sa.Text()),
        sa.Column("created_at", sa.Text()),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "creatives",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id")),
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("ad_accounts.id")),
        sa.Column("intended_status", sa.Text()),
        sa.Column("is_serving", sa.Boolean()),
        sa.Column("content_reference", sa.Text()),
        sa.Column("content_name", sa.Text()),
        sa.Column("serving_hold_reasons", sa.Text()),
        sa.Column("created_at", sa.BigInteger()),
        sa.Column("last_modified_at", sa.BigInteger()),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "campaign_daily_metrics",
        sa.Column("campaign_id", sa.Integer(), sa.ForeignKey("campaigns.id"), primary_key=True),
        sa.Column("date", sa.Text(), primary_key=True),
        sa.Column("impressions", sa.Integer(), server_default="0"),
        sa.Column("clicks", sa.Integer(), server_default="0"),
        sa.Column("spend", sa.Float(), server_default="0"),
        sa.Column("landing_page_clicks", sa.Integer(), server_default="0"),
        sa.Column("conversions", sa.Integer(), server_default="0"),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("comments", sa.Integer(), server_default="0"),
        sa.Column("shares", sa.Integer(), server_default="0"),
        sa.Column("follows", sa.Integer(), server_default="0"),
        sa.Column("leads", sa.Integer(), server_default="0"),
        sa.Column("opens", sa.Integer(), server_default="0"),
        sa.Column("sends", sa.Integer(), server_default="0"),
        sa.Column("ctr", sa.Float(), server_default="0"),
        sa.Column("cpc", sa.Float(), server_default="0"),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "creative_daily_metrics",
        sa.Column("creative_id", sa.Text(), sa.ForeignKey("creatives.id"), primary_key=True),
        sa.Column("date", sa.Text(), primary_key=True),
        sa.Column("impressions", sa.Integer(), server_default="0"),
        sa.Column("clicks", sa.Integer(), server_default="0"),
        sa.Column("spend", sa.Float(), server_default="0"),
        sa.Column("landing_page_clicks", sa.Integer(), server_default="0"),
        sa.Column("conversions", sa.Integer(), server_default="0"),
        sa.Column("likes", sa.Integer(), server_default="0"),
        sa.Column("comments", sa.Integer(), server_default="0"),
        sa.Column("shares", sa.Integer(), server_default="0"),
        sa.Column("follows", sa.Integer(), server_default="0"),
        sa.Column("leads", sa.Integer(), server_default="0"),
        sa.Column("opens", sa.Integer(), server_default="0"),
        sa.Column("sends", sa.Integer(), server_default="0"),
        sa.Column("ctr", sa.Float(), server_default="0"),
        sa.Column("cpc", sa.Float(), server_default="0"),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "audience_demographics",
        sa.Column("account_id", sa.Integer(), sa.ForeignKey("ad_accounts.id"), primary_key=True),
        sa.Column("pivot_type", sa.Text(), primary_key=True),
        sa.Column("segment", sa.Text(), primary_key=True),
        sa.Column("date_start", sa.Text(), primary_key=True),
        sa.Column("impressions", sa.Integer(), server_default="0"),
        sa.Column("clicks", sa.Integer(), server_default="0"),
        sa.Column("ctr", sa.Float(), server_default="0"),
        sa.Column("share_pct", sa.Float(), server_default="0"),
        sa.Column("date_end", sa.Text()),
        sa.Column("fetched_at", sa.Text()),
    )

    op.create_table(
        "sync_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("started_at", sa.Text(), nullable=False),
        sa.Column("finished_at", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="running"),
        sa.Column("trigger", sa.Text()),
        sa.Column("campaigns_fetched", sa.Integer(), server_default="0"),
        sa.Column("creatives_fetched", sa.Integer(), server_default="0"),
        sa.Column("api_calls_made", sa.Integer(), server_default="0"),
        sa.Column("errors", sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("sync_log")
    op.drop_table("audience_demographics")
    op.drop_table("creative_daily_metrics")
    op.drop_table("campaign_daily_metrics")
    op.drop_table("creatives")
    op.drop_table("campaigns")
    op.drop_table("ad_accounts")
