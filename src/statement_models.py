from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class DispatchStatus(StrEnum):
    SCHEDULED = "scheduled"
    EN_ROUTE = "en_route"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrder(BaseModel):
    work_order_id: str = Field(min_length=1)
    service_date: date
    dispatch_status: DispatchStatus
    technician: str = Field(min_length=1)
    photo_refs: list[str] = Field(default_factory=list)
    technician_follow_up: str | None = None


class StatementRequest(BaseModel):
    customer_name: str = Field(min_length=1)
    customer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    period_start: date
    period_end: date
    work_orders: list[WorkOrder]

    @model_validator(mode="after")
    def period_is_ordered(self) -> "StatementRequest":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be on or after period_start")
        return self


class StatementResult(BaseModel):
    message_id: str
    pdf: dict[str, object]
    work_order_count: int
    photo_count: int
    follow_up_count: int
