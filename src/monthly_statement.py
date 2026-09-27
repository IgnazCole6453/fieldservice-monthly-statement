import hashlib
import html
import json

from .infrai_client import InfraiClient
from .statement_models import DispatchStatus, StatementRequest, StatementResult


def _statement_html(request: StatementRequest, usage: object) -> tuple[str, int, int]:
    photo_count = sum(len(order.photo_refs) for order in request.work_orders)
    follow_ups = [
        order
        for order in request.work_orders
        if order.dispatch_status == DispatchStatus.COMPLETED and order.technician_follow_up
    ]
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(order.work_order_id)}</td>"
        f"<td>{order.service_date.isoformat()}</td>"
        f"<td>{html.escape(order.dispatch_status.value)}</td>"
        f"<td>{html.escape(order.technician)}</td>"
        f"<td>{len(order.photo_refs)}</td>"
        f"<td>{html.escape(order.technician_follow_up or '')}</td>"
        "</tr>"
        for order in request.work_orders
    )
    usage_json = html.escape(json.dumps(usage, sort_keys=True, default=str))
    document = f"""<!doctype html>
<html><head><meta charset="utf-8"><style>
body {{ font: 12px sans-serif; color: #17202a; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 7px; border: 1px solid #ccd1d1; text-align: left; }}
</style></head><body>
<h1>Monthly usage statement</h1>
<p>{html.escape(request.customer_name)} | {request.period_start} to {request.period_end}</p>
<p>Work orders: {len(request.work_orders)} | Photos: {photo_count} | Follow-ups: {len(follow_ups)}</p>
<table><thead><tr><th>Work order</th><th>Service date</th><th>Dispatch</th><th>Technician</th><th>Photos</th><th>Follow-up</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Account usage</h2><pre>{usage_json}</pre>
</body></html>"""
    return document, photo_count, len(follow_ups)


def send_monthly_statement(
    client: InfraiClient, request: StatementRequest
) -> StatementResult:
    identity = hashlib.sha256(
        f"{request.customer_email}:{request.period_start}:{request.period_end}".encode()
    ).hexdigest()

    usage = client.request(method="GET", path="/account/usage")
    document, photo_count, follow_up_count = _statement_html(request, usage)
    pdf = client.request(
        method="POST",
        path="/pdf/generate",
        json={"html": document, "page_size": "A4", "orientation": "portrait", "store": True},
        idempotency_key=f"statement-pdf-{identity}",
    )
    email_data = client.request(
        method="POST",
        path="/email/send",
        json={
            "to": request.customer_email,
            "subject": f"Usage statement: {request.period_start} to {request.period_end}",
            "html": document,
        },
        idempotency_key=f"statement-email-{identity}",
    )
    return StatementResult(
        message_id=email_data["message_id"],
        pdf=pdf,
        work_order_count=len(request.work_orders),
        photo_count=photo_count,
        follow_up_count=follow_up_count,
    )

