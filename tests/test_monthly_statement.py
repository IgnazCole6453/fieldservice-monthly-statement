from datetime import date

from src.monthly_statement import send_monthly_statement
from src.statement_models import DispatchStatus, StatementRequest, WorkOrder


class RecordingClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def request(self, method: str, path: str, **kwargs: object) -> object:
        self.calls.append({"method": method, "path": path, **kwargs})
        if path == "/account/usage":
            return {"total": 17}
        if path == "/pdf/generate":
            return {"document": "statement.pdf"}
        return {"message_id": "msg_123"}


def test_only_completed_orders_create_follow_up_count() -> None:
    request = StatementRequest(
        customer_name="North Street Bakery",
        customer_email="ops@example.com",
        period_start=date(2026, 8, 1),
        period_end=date(2026, 8, 31),
        work_orders=[
            WorkOrder(
                work_order_id="WO-1",
                service_date=date(2026, 8, 5),
                dispatch_status=DispatchStatus.COMPLETED,
                technician="M. Chen",
                photo_refs=["arrival.jpg", "repair.jpg"],
                technician_follow_up="Inspect next month.",
            ),
            WorkOrder(
                work_order_id="WO-2",
                service_date=date(2026, 8, 6),
                dispatch_status=DispatchStatus.EN_ROUTE,
                technician="J. Diaz",
                technician_follow_up="Customer requested a call.",
            ),
        ],
    )
    client = RecordingClient()

    result = send_monthly_statement(client, request)  # type: ignore[arg-type]

    assert result.follow_up_count == 1
    assert result.photo_count == 2
    assert result.message_id == "msg_123"
    assert [call["path"] for call in client.calls] == [
        "/account/usage",
        "/pdf/generate",
        "/email/send",
    ]
    pdf_html = client.calls[1]["json"]["html"]  # type: ignore[index]
    email_html = client.calls[2]["json"]["html"]  # type: ignore[index]
    assert pdf_html == email_html
    assert "Inspect next month." in str(pdf_html)

