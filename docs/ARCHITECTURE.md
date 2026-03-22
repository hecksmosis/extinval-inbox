# Architecture

## Core workflow

1. Inbox connector fetches all emails since the last checkpoint.
2. Every raw email is archived locally for auditability.
3. Attachments are expanded, including ZIP bundles.
4. LlamaParse is used as the preferred parser for PDFs, scans, and mixed files.
5. The extracted email context is sent to a fixed vendor-selected LLM (Gemini or Claude).
6. The model returns structured JSON only.
7. Canonical product names are validated against the supplied catalog.
8. Results are appended into a single workbook that can be used to prepare outbound quotes.
9. Failures and low-confidence serializations are stored in a reporting queue.

## Reliability strategy

To drive the practical error rate as low as possible:

- Temperature remains low, but deterministic prompting alone is not enough.
- The system constrains outputs to JSON.
- Canonical names must come from the provided catalog.
- Unknown or weak matches are escalated instead of guessed.
- A future production deployment should add a second-pass validator and benchmark set from real `.eml` examples.

## ZIP attachments

ZIP files full of PDFs are acceptable. The parser expands ZIP members one by one and parses each contained document. In production you may want to add:

- ZIP bomb protection,
- MIME allowlists,
- total attachment size caps,
- duplicate file detection.

## Packaging

The application is designed so you can hardcode or preconfigure provider/model settings before distributing to a client. The intended packaging route is PyInstaller, producing a single desktop executable with bundled assets.
