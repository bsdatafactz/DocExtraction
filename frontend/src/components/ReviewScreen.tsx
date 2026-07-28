import { useState } from "react";
import { documentFileUrl, submitCorrections } from "../api";
import type { DocumentDetail, LineItem } from "../types";
import { DocumentViewer } from "./DocumentViewer";
import { StatusBadge } from "./StatusBadge";

const EDITABLE_FIELDS: Array<keyof NonNullable<DocumentDetail["extraction"]>> = [
  "invoice_number",
  "invoice_date",
  "due_date",
  "po_number",
  "vendor_name",
  "vendor_address",
  "customer_name",
  "currency",
  "subtotal",
  "tax_amount",
  "total_amount",
  "payment_terms",
];

const LOW_CONFIDENCE_THRESHOLD = 0.6;

interface Props {
  document: DocumentDetail;
  onDone: () => void;
  onError: (err: unknown) => void;
  isAdmin: boolean;
}

export function ReviewScreen({ document, onDone, onError, isAdmin }: Props) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const field of EDITABLE_FIELDS) {
      const value = document.extraction?.[field];
      initial[field] = value == null ? "" : String(value);
    }
    return initial;
  });
  const [lineItems, setLineItems] = useState<LineItem[]>(document.extraction?.line_items ?? []);
  const [submitting, setSubmitting] = useState(false);

  const confidenceByField = new Map(
    (document.confidence?.fields ?? []).map((f) => [f.field_name, f.composite]),
  );

  function updateLineItem(index: number, key: keyof LineItem, raw: string) {
    setLineItems((prev) =>
      prev.map((item, i) =>
        i === index
          ? {
              ...item,
              [key]: key === "description" ? raw : raw === "" ? null : Number(raw),
            }
          : item,
      ),
    );
  }

  async function handleSubmit(approve: boolean) {
    setSubmitting(true);
    try {
      await submitCorrections(
        document.id,
        { ...values, line_items: lineItems as unknown as Record<string, unknown>[] },
        approve,
      );
      onDone();
    } catch (err) {
      onError(err);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="review-screen">
      <div className="review-panel review-original">
        <h3>Original document</h3>
        <DocumentViewer fileUrl={documentFileUrl(document.id)} filename={document.filename} />
      </div>

      <div className="review-panel review-fields">
        <div className="review-panel-header">
          <h3>Extracted fields</h3>
          <StatusBadge status={document.status} />
        </div>

        {!isAdmin && (
          <p className="page-subtitle">
            Read-only — only Admins can correct fields and approve documents.
          </p>
        )}

        {EDITABLE_FIELDS.map((field) => {
          const confidence = confidenceByField.get(field);
          const low = confidence != null && confidence < LOW_CONFIDENCE_THRESHOLD;
          return (
            <label key={field} className={low ? "field-low-confidence" : ""}>
              <div className="field-label-row">
                <span className="field-name">{field.replaceAll("_", " ")}</span>
                {confidence != null &&
                  (low ? (
                    <span className="badge badge-failed">Low confidence</span>
                  ) : (
                    <span className="field-confidence">{Math.round(confidence * 100)}%</span>
                  ))}
              </div>
              <input
                disabled={!isAdmin}
                value={values[field] ?? ""}
                onChange={(e) => setValues({ ...values, [field]: e.target.value })}
              />
            </label>
          );
        })}

        <h4>Line items</h4>
        <table className="line-items-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {lineItems.map((item, i) => (
              <tr key={i}>
                <td>
                  <input
                    disabled={!isAdmin}
                    value={item.description}
                    onChange={(e) => updateLineItem(i, "description", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    disabled={!isAdmin}
                    className="qty"
                    value={item.quantity ?? ""}
                    onChange={(e) => updateLineItem(i, "quantity", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    disabled={!isAdmin}
                    className="price"
                    value={item.unit_price ?? ""}
                    onChange={(e) => updateLineItem(i, "unit_price", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    disabled={!isAdmin}
                    className="total"
                    value={item.line_total ?? ""}
                    onChange={(e) => updateLineItem(i, "line_total", e.target.value)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {isAdmin && (
          <div className="review-actions">
            <button
              className="btn btn-primary"
              disabled={submitting}
              onClick={() => handleSubmit(true)}
            >
              {submitting ? "Saving…" : "Approve"}
            </button>
            <button className="btn" disabled={submitting} onClick={() => handleSubmit(false)}>
              Flag for follow-up
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
