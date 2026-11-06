"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { Activity, ArrowDownToLine } from "lucide-react";
import { Empty, PageHeading } from "../shared/ui";
export default function AuditScreen({
  title,
  description,
  action,
  exportActivity,
  audits,
}: ScreenContracts["audit"]) {
  return (
    <>
      <PageHeading
        eyebrow="TRANSPARENCY, BUILT IN"
        title="Audit activity"
        description="Recent administrative and knowledge events in your organization."
        action={
          <button className="btn" onClick={exportActivity}>
            <ArrowDownToLine size={15} />
            Export JSON
          </button>
        }
      />
      <section className="panel">
        <div className="section-head">
          <h2>Latest events</h2>
          <span className="muted">Most recent 100</span>
        </div>
        {audits.map((a) => (
          <div className="audit-row" key={a.id}>
            <span className="audit-icon">
              <Activity size={16} />
            </span>
            <div>
              <strong>
                {a.action.replaceAll(".", " · ").replaceAll("_", " ")}
              </strong>
              <p>{a.detail || "Organization activity"}</p>
            </div>
            <time>{new Date(a.created_at).toLocaleString()}</time>
          </div>
        ))}
        {!audits.length && (
          <Empty
            icon={Activity}
            title="A clean slate"
            description="Events will appear as your team uses the workspace."
          />
        )}
      </section>
    </>
  );
}
