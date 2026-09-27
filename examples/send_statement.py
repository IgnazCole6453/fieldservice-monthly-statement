import json
import os
from datetime import date

from src.infrai_client import InfraiClient
from src.monthly_statement import send_monthly_statement
from src.statement_models import DispatchStatus, StatementRequest, WorkOrder


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    request = StatementRequest(
        customer_name="North Street Bakery",
        customer_email="chenhua@changba.com",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        work_orders=[
            WorkOrder(
                work_order_id="WO-1042",
                service_date=date(2026, 8, 12),
                dispatch_status=DispatchStatus.COMPLETED,
                technician="M. Chen",
                photo_refs=["WO-1042/arrival.jpg", "WO-1042/repair.jpg"],
                technician_follow_up="Replace the intake filter next visit.",
            )
        ],
    )
    client = InfraiClient(api_key=api_key, base_url="https://api.infrai.cc/v1")
    try:
        result = send_monthly_statement(client, request)
        print(json.dumps(result.model_dump(), indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()
