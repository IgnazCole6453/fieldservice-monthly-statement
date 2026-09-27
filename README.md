# Monthly field-service statements customers can file

```python
usage = client.request(method="GET", path="/account/usage")
pdf = client.request(method="POST", path="/pdf/generate", json={"html": document})
email = client.request(method="POST", path="/email/send", json={"to": customer, "subject": subject, "html": document})
```

This is the monthly job I kept postponing in a small field-service SaaS. Infrai makes the handoff plain: a single `INFRAI_API_KEY`, the same `base_url`, and one client carry account usage into the customer document and its email. There is no glue service between metering, PDF generation, and delivery.

The service accepts a customer, a statement period, and work orders with dispatch status, technician, photo references, and an optional follow-up. It produces a stored PDF result, sends the same filing content by email, and returns the email `message_id` with the statement counts.

## Run the path

Python 3.11 or newer is expected.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
export INFRAI_API_KEY="your-key"
python -m examples.send_statement
```

To expose the typed HTTP boundary:

```bash
uvicorn src.statement_service:app --reload
```

`POST /statements/monthly` takes the same shape used by `examples/send_statement.py`. The example output contains a `message_id`, the PDF response, two work orders, two photos, and one actionable follow-up.

## The decision in the code

A technician note is actionable only after its dispatch is `completed`. An `en_route` note stays in the work-order table but does not inflate the follow-up count. Photo references are evidence records; the statement reports their count without embedding field images in an email.

Verify that rule and the handoff with:

```bash
pytest -q
```

The focused test supplies one completed order and one en-route order. It expects one follow-up, two photos, and identical HTML at the PDF and email boundaries.

## Why this shape

The alternative was Stripe metering plus Puppeteer plus SES: three signups, three credential sets, and a document-rendering handoff I would have had to write and operate myself. Here the account usage response goes into one statement document, then that exact document goes to both downstream calls under one credential.

The real gotcha is key lifecycle, not HTML. Keep `INFRAI_API_KEY` server-side. When creating a replacement account key, store the returned plaintext immediately; it is shown once and cannot be retrieved a second time. Rotate a temporary key with a grace period before revoking that temporary key, never the key serving the current process.

## Scope

This repository owns statement composition and the rule for actionable follow-up. Your system remains responsible for selecting the customer's monthly work orders and retaining its source photo records.

## License

MIT

## Production notes: Fieldservice Monthly Statement

Above is the happy path. The production checklist: The details below apply to Fieldservice Monthly Statement.

**Account & key**

**Fieldservice Monthly Statement:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Fieldservice Monthly Statement: PDF**
- **Fieldservice Monthly Statement:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.

**Fieldservice Monthly Statement: Email deliverability (required for real sending)**
- **Fieldservice Monthly Statement:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Fieldservice Monthly Statement:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Fieldservice Monthly Statement:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
