import { useState } from "react";
import { documentFileUrl, submitCorrections } from "../api";
import type { DocumentDetail } from "../types";
import { DocumentViewer } from "./DocumentViewer";
import { StatusBadge } from "./StatusBadge";

interface Column {
  key: string;
  label: string;
  numeric?: boolean;
}

type Section =
  | { kind: "fields"; title: string; fields: string[] }
  | { kind: "table"; title: string; key: string; columns: Column[] }
  | { kind: "skills"; title: string; key: string };

// One config per implemented document type — this is the thing to extend
// when a new type gets real extraction wired up (see backend
// app/schemas/registry.py for the matching schema side).
const SECTIONS_BY_TYPE: Record<string, Section[]> = {
  invoice: [
    {
      kind: "fields",
      title: "Overview",
      fields: ["invoice_number", "invoice_date", "due_date"],
    },
    {
      kind: "fields",
      title: "Parties",
      fields: ["vendor_name", "customer_name"],
    },
    { kind: "fields", title: "Amounts", fields: ["subtotal", "tax_amount", "total_amount"] },
    {
      kind: "table",
      title: "Line Items",
      key: "line_items",
      columns: [
        { key: "description", label: "Item" },
        { key: "quantity", label: "Qty", numeric: true },
        { key: "unit_price", label: "Price", numeric: true },
        { key: "line_total", label: "Total", numeric: true },
      ],
    },
  ],
  resume: [
    { kind: "fields", title: "Contact", fields: ["full_name", "email", "phone"] },
    { kind: "fields", title: "Summary", fields: ["professional_summary"] },
    { kind: "skills", title: "Skills", key: "skills" },
    {
      kind: "table",
      title: "Work Experience",
      key: "work_experience",
      columns: [
        { key: "company", label: "Company" },
        { key: "title", label: "Title" },
        { key: "start_date", label: "Start" },
        { key: "end_date", label: "End" },
        { key: "description", label: "Description" },
      ],
    },
    {
      kind: "table",
      title: "Projects",
      key: "projects",
      columns: [
        { key: "name", label: "Name" },
        { key: "description", label: "Description" },
        { key: "technologies", label: "Tech" },
      ],
    },
    {
      kind: "table",
      title: "Education",
      key: "education",
      columns: [
        { key: "institution", label: "Institution" },
        { key: "degree", label: "Degree" },
        { key: "field_of_study", label: "Field" },
        { key: "graduation_year", label: "Year" },
      ],
    },
  ],
};

const LOW_CONFIDENCE_THRESHOLD = 0.6;

interface Props {
  document: DocumentDetail;
  onDone: () => void;
  onError: (err: unknown) => void;
  isAdmin: boolean;
}

export function ReviewScreen({ document, onDone, onError, isAdmin }: Props) {
  const sections = SECTIONS_BY_TYPE[document.document_type] ?? [];
  const extraction = (document.extraction ?? {}) as Record<string, unknown>;

  const [activeIndex, setActiveIndex] = useState(0);
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {};
    for (const section of sections) {
      if (section.kind === "fields") {
        for (const field of section.fields) {
          const v = extraction[field];
          initial[field] = v == null ? "" : String(v);
        }
      } else if (section.kind === "skills") {
        const v = extraction[section.key];
        initial[section.key] = Array.isArray(v) ? v.join(", ") : "";
      }
    }
    return initial;
  });
  const [tables, setTables] = useState<Record<string, Record<string, string>[]>>(() => {
    const initial: Record<string, Record<string, string>[]> = {};
    for (const section of sections) {
      if (section.kind === "table") {
        const rows = extraction[section.key];
        initial[section.key] = Array.isArray(rows)
          ? rows.map((row) => {
              const out: Record<string, string> = {};
              for (const col of section.columns) {
                const v = (row as Record<string, unknown>)[col.key];
                out[col.key] = v == null ? "" : String(v);
              }
              return out;
            })
          : [];
      }
    }
    return initial;
  });
  const [submitting, setSubmitting] = useState(false);

  const confidenceByField = new Map(
    (document.confidence?.fields ?? []).map((f) => [f.field_name, f.composite]),
  );

  function updateTableCell(tableKey: string, rowIndex: number, colKey: string, raw: string) {
    setTables((prev) => ({
      ...prev,
      [tableKey]: prev[tableKey].map((row, i) => (i === rowIndex ? { ...row, [colKey]: raw } : row)),
    }));
  }

  async function handleSubmit(approve: boolean) {
    setSubmitting(true);
    try {
      const correctedFields: Record<string, string | number | null | Record<string, unknown>[]> = {
        ...values,
      };

      for (const section of sections) {
        if (section.kind === "skills") {
          // handled below, not sent as a plain string
          delete correctedFields[section.key];
        }
      }

      for (const section of sections) {
        if (section.kind === "table") {
          correctedFields[section.key] = tables[section.key].map((row) => {
            const out: Record<string, unknown> = {};
            for (const col of section.columns) {
              const raw = row[col.key];
              out[col.key] = col.numeric ? (raw === "" ? null : Number(raw)) : raw;
            }
            return out;
          });
        } else if (section.kind === "skills") {
          correctedFields[section.key] = values[section.key]
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean) as unknown as Record<string, unknown>[];
        }
      }

      await submitCorrections(document.id, correctedFields, approve);
      onDone();
    } catch (err) {
      onError(err);
    } finally {
      setSubmitting(false);
    }
  }

  const active = sections[activeIndex];

  return (
    <div className="review-screen">
      <div className="review-panel review-original">
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

        <div className="section-tabs">
          {sections.map((section, i) => (
            <button
              key={section.title}
              className={`section-tab ${i === activeIndex ? "section-tab--active" : ""}`}
              onClick={() => setActiveIndex(i)}
            >
              {section.title}
            </button>
          ))}
        </div>

        {active?.kind === "fields" &&
          active.fields.map((field) => {
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

        {active?.kind === "skills" && (
          <label>
            <div className="field-label-row">
              <span className="field-name">Skills (comma-separated)</span>
            </div>
            <input
              disabled={!isAdmin}
              value={values[active.key] ?? ""}
              onChange={(e) => setValues({ ...values, [active.key]: e.target.value })}
            />
          </label>
        )}

        {active?.kind === "table" && (
          <table className="line-items-table">
            <thead>
              <tr>
                {active.columns.map((col) => (
                  <th key={col.key}>{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(tables[active.key] ?? []).map((row, i) => (
                <tr key={i}>
                  {active.columns.map((col) => (
                    <td key={col.key}>
                      <input
                        disabled={!isAdmin}
                        className={col.numeric ? "qty" : undefined}
                        value={row[col.key] ?? ""}
                        onChange={(e) => updateTableCell(active.key, i, col.key, e.target.value)}
                      />
                    </td>
                  ))}
                </tr>
              ))}
              {(tables[active.key] ?? []).length === 0 && (
                <tr>
                  <td colSpan={active.columns.length} className="page-subtitle">
                    Nothing extracted here.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

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
