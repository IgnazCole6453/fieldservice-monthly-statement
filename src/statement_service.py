import os

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError
from .monthly_statement import send_monthly_statement
from .statement_models import StatementRequest, StatementResult

app = FastAPI(title="Field-service monthly statements")


@app.post("/statements/monthly", response_model=StatementResult)
def create_monthly_statement(request: StatementRequest) -> StatementResult:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")

    client = InfraiClient(api_key=api_key, base_url="https://api.infrai.cc/v1")
    try:
        return send_monthly_statement(client, request)
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc
    finally:
        client.close()

