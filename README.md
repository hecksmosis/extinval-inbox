# Extinval Inbox Automation

A desktop-first AI system that watches a client's inbox, finds product request emails, parses arbitrary email bodies and attachments (including images, scanned PDFs, and ZIP bundles of PDFs), normalizes requested products to canonical names, and writes every processed request into a quote-ready Excel workbook.

## What this implementation includes

- Multi-provider inbox ingestion design for IMAP-compatible providers, Microsoft 365, and Gmail.
- Attachment parsing pipeline with ZIP expansion, OCR fallback, and LlamaParse integration.
- LLM-driven classification and extraction with deterministic validation against a canonical catalog.
- Excel aggregation into a master workbook plus a per-email quote sheet.
- A modern desktop UI built with `customtkinter` for setup, monitoring, and failed-serialization review.
- Packaging guidance for a single executable workflow using PyInstaller.
- Cost estimation guidance for ~20 emails/day.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m app.main
```

## Configuration strategy

The end user should not need to define model/API options. You can set these before packaging by filling `.env` values or editing the defaults in `app/core/config.py`.

Important settings:

- `MODEL_PROVIDER`: `gemini` or `claude`
- `MODEL_NAME`: e.g. `gemini-2.0-flash` or `claude-3-5-sonnet-latest`
- `MODEL_API_KEY`: packaged or injected during installation
- `EMAIL_PROVIDER`: `imap`, `gmail`, or `m365`
- `EMAIL_USERNAME`, `EMAIL_PASSWORD`
- `CANONICAL_CATALOG_PATH`: CSV/Excel containing canonical product names
- `TEMPLATE_WORKBOOK_PATH`: the Excel template whose style must be preserved

## Recommended production flow

1. Configure credentials once.
2. Load the Extinval template workbook and product catalog.
3. Start the desktop app.
4. The app pulls all unseen messages since the last checkpoint when it reconnects.
5. Every email is archived into a local audit store and summarized in the reporting dashboard.
6. Failed or low-confidence serializations are surfaced for review.

## Cost estimate

For about 20 emails/day (~600/month), assuming:

- Most emails are short and a subset have attachments.
- LlamaParse is used for attachment parsing.
- Gemini/Claude is used only after text/attachment aggregation.

A practical working budget is usually around **$10-$45/month** depending on attachment volume and model choice. A conservative planning model:

- 600 emails/month.
- 1 LLM extraction call per email.
- Average 4k-12k input tokens after parsing.
- Average 500-1,500 output tokens.
- OCR adds CPU cost locally but not API cost.
- ZIPs are acceptable, but they increase parse volume and therefore API spend.

If you keep OCR local and use a cost-efficient extraction model, you can often stay near the lower end. If many ZIP attachments contain many scanned PDFs, budget closer to the upper end.

## Hallucination control

Do **not** rely primarily on temperature tuning. The better method is:

- keep temperature low (`0` to `0.2`),
- force JSON schema output,
- validate each extracted line against the canonical product catalog,
- reject unknown matches below a confidence threshold,
- run a second-pass validator only on low-confidence cases,
- mark unresolved records for human review instead of guessing.

## How to provide `.eml` examples

You can add example files into a folder such as:

```text
samples/emails/
samples/attachments/
```

Recommended bundle for evaluation:

- original `.eml` files,
- any referenced PDFs/images/ZIPs if they are detached,
- the target Excel template,
- a gold-standard output workbook if available.

Once those are in the repo, the parser and tests can be adapted to your real documents.
