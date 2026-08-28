"""Alert response models (camelCase for Nexus Console)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SOCAlert(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    timestamp: str
    severity: Literal["critical", "high", "medium", "low", "informational"]
    source: Literal["wazuh", "suricata"]
    rule_name: str = Field(alias="ruleName")
    affected_host: str = Field(alias="affectedHost")
    acknowledged: bool = False
    athena_scenario: str | None = Field(None, alias="athenaScenario")
    payload: dict[str, Any] = Field(default_factory=dict)
    wazuh_dashboard_url: str | None = Field(None, alias="wazuhDashboardUrl")


class AlertsResponse(BaseModel):
    alerts: list[SOCAlert]
    total: int


class TriageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    confidence_score: float = Field(alias="confidenceScore")
    recommended_action: str = Field(alias="recommendedAction")
    reasoning_excerpt: str = Field(alias="reasoningExcerpt")
