# Test set

21 invoices total (15 digital + 6 scanned = 28.6% scanned, clears the ≥25% bar). Every file the pipeline actually ingests is a **PDF** — `digital/*.pdf` and `scanned/*.pdf` are what to upload; `originals/` in each folder is the source image kept for reference/visual comparison only.

## Why PDFs, and why they weren't PDFs at first

The parsing router (`backend/app/services/parsing.py`) decides digital-vs-scanned by whether a page has an extractable text layer, checked via PyMuPDF. Both source datasets only provide raster images (JPEGs) — an image has no text layer regardless of whether the invoice was originally "digitally generated" or scanned. Uploading the raw JPEGs would have made every single sample in the set route to the OCR path, defeating the point of having a "digital" half at all. Fixed by:

- **digital/** — the 15 samples are freshly rendered single-page PDFs with a **real embedded text layer**, laid out from the source dataset's own ground-truth field values (not OCR'd, not guessed). This is what a born-digital invoice (e.g. exported from an invoicing system) actually looks like to a parser, and is what exercises the PyMuPDF direct-extraction path.
- **scanned/** — the 6 samples are the original scanned JPEGs wrapped into single-page image-only PDFs (`fitz.new_page()` + `insert_image()`, no text layer). This is the realistic delivery format too — real scanned invoices arrive as PDFs from a scanner/copier/email attachment, not bare JPEG files — and it exercises the OCR-routing path via the PDF ingestion pipeline rather than a separate untested image-upload path.

Verified against the actual pipeline code, not just assumed: `parse_document()` on a `digital/*.pdf` returns `is_scanned=False` with the real text; on a `scanned/*.pdf` it returns `is_scanned=True` and raises `NotImplementedError` at the OCR stub, exactly as designed (PaddleOCR isn't wired in until Tuesday's task).

## digital/ — 15 samples

Source data: [mychen76/invoices-and-receipts_ocr_v1](https://huggingface.co/datasets/mychen76/invoices-and-receipts_ocr_v1) (Hugging Face) — used for its field annotations only; the PDF layout itself is a simple rendering, not a reproduction of the original image. `digital/manifest.json` has the raw parsed data for all 15; `digital/originals/*.jpg` are the original dataset images, kept so you can visually sanity-check the ground truth against something.

## scanned/ — 6 samples

Source: [chainyo/rvl-cdip-invoice](https://huggingface.co/datasets/chainyo/rvl-cdip-invoice) (Hugging Face), the invoice-labeled subset of RVL-CDIP (scanned business documents from the Legacy Tobacco Document Library / UCSF Industry Documents Library — public research corpus). Genuinely scanned: noise, skew, handwritten annotations, no digital text layer. No field-level ground truth — these need hand-labeling.

**Check before relying on all 6**: RVL-CDIP's "invoice" class label is known to be noisy. `scanned_00` (see `scanned/originals/scanned_00.jpg`) is an internal Accounts Payable Voucher, not a vendor invoice — decide whether to keep it as a deliberately messy edge case (worth a line in the design doc's schema section) or swap it for another sample from the same dataset. `scanned_02` is confirmed a real vendor invoice; spot-check the rest.

## ground_truth/ — 10 hand-labeled documents (brief's requirement)

Currently: 10 JSON files (`digital_00.json`–`digital_09.json`) auto-derived from the source dataset's own annotations, normalized to match `backend/app/schemas/invoice.py` field names — these are exactly the values rendered into the corresponding PDFs, so a correct extraction should match them exactly modulo formatting. This is a shortcut, not free ground truth — the source dataset's own labels can have errors, and normalization made a few calls worth knowing about:

- `vendor_address` / `customer_address`: the source combines name and address into one string, stored whole in `vendor_name` / `customer_name`. Address fields are `null` and noted in each file's `field_status_notes`.
- `due_date`, `po_number`, `payment_terms`: not present in the source annotations, marked not-applicable rather than guessed.
- Numeric fields normalize European-style decimal commas (`"7,50"` → `7.5`) — the source data mixes `$` prefixes with comma decimals, itself a good example of the messy-real-world-data problem to mention in the design doc.

**Before using these as your official ground truth**: spot-check each against `digital/originals/digital_NN.jpg` — "hand-labeled" in the brief means human-verified, not just machine-copied. Budget 10-15 min to confirm rather than skip this.

Per PLAN.md's own suggestion (mix digital + scanned in the ground-truth set so the accuracy report isn't just measuring the easy path), consider swapping 2-3 of the 10 for hand-labeled scanned docs once those are labeled Wednesday — that makes the accuracy number defensible for both parsing paths, not just the digital one.

## Licensing note

Neither dataset's license is fully pinned down in this pass (mychen76's isn't stated on its HF page; RVL-CDIP derives from a public research archive). Fine for this internship project; cite both sources in the design doc's data section rather than presenting the samples as originally sourced.
