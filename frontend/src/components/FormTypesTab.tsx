import { DOCUMENT_TYPES } from "../constants";

const DESCRIPTIONS: Record<string, string> = {
  invoice: "Invoice number, dates, vendor/customer, amounts, and line items.",
  resume: "Contact info, summary, skills, work experience, projects, education.",
  contract: "Not yet implemented — no extraction schema defined for this type yet.",
};

export function FormTypesTab() {
  return (
    <div>
      <p className="page-subtitle">
        Each document type has one fixed field set — every upload of that type extracts into the
        same schema, not something that varies per document.
      </p>
      <div className="project-grid">
        {DOCUMENT_TYPES.map((t) => (
          <div key={t.value} className="project-card project-card--static">
            <div className="project-card-top">
              <span className={`badge badge-doctype-${t.value}`}>{t.label}</span>
              {!t.implemented && <span className="doctype-soon">Coming soon</span>}
            </div>
            <h3>{t.label}</h3>
            <span className="project-card-meta">{DESCRIPTIONS[t.value]}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
