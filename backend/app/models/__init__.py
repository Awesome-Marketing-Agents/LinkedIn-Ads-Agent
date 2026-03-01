"""Re-export all SQLModel tables for Alembic discovery."""

from app.models.ad_account import AdAccount
from app.models.campaign import Campaign
from app.models.creative import Creative
from app.models.metrics import CampaignDailyMetric, CreativeDailyMetric
from app.models.demographics import AudienceDemographic
from app.models.sync import SyncLog

__all__ = [
    "AdAccount",
    "Campaign",
    "Creative",
    "CampaignDailyMetric",
    "CreativeDailyMetric",
    "AudienceDemographic",
    "SyncLog",
]
