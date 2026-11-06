"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { bytes } from "@/lib/api";
import { Clock, Database, Search, ShieldCheck } from "lucide-react";
import { DocTable, Empty, PageHeading } from "../shared/ui";
export default function DocumentsScreen({
  title,
  description,
  action,
  canWrite,
  uploadButton,
  stats,
  filter,
  setFilter,
  docs,
  docQuery,
  setDocQuery,
  workspaceFilter,
  setWorkspaceFilter,
  workspaces,
  filteredDocs,
  openDoc,
}: ScreenContracts["documents"]) {
  return (
    <>
      <PageHeading
        eyebrow="YOUR SOURCE OF TRUTH"
        title="Document library"
        description="A shared home for the knowledge that moves your team forward."
        action={canWrite && uploadButton}
      />
      <div className="library-summary">
        <span>
          <span className="live-dot" />
          {stats?.ready || 0} indexed
        </span>
        <span>
          <Clock size={14} />
          {stats?.processing || 0} processing
        </span>
        <span>
          <Database size={14} />
          {bytes(stats?.storage_bytes || 0)} stored
        </span>
      </div>
      <section className="panel">
        <div className="library-toolbar">
          <div className="tabs">
            {[
              ["all", "All documents"],
              ["ready", "Indexed"],
              ["processing", "Processing"],
              ["failed", "Failed"],
            ].map(([v, l]) => (
              <button
                key={v}
                className={filter === v ? "selected" : ""}
                onClick={() => setFilter(v)}
              >
                {l}
                {v === "all" && <span>{docs.length}</span>}
              </button>
            ))}
          </div>
          <div className="table-controls">
            <label className="input-icon">
              <Search size={15} />
              <input
                aria-label="Filter documents"
                placeholder="Find a document…"
                value={docQuery}
                onChange={(e) => setDocQuery(e.target.value)}
              />
            </label>
            <select
              aria-label="Filter by workspace"
              value={workspaceFilter}
              onChange={(e) => setWorkspaceFilter(e.target.value)}
            >
              <option value="">All workspaces</option>
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        {filteredDocs.length ? (
          <DocTable docs={filteredDocs} open={openDoc} />
        ) : (
          <Empty
            title={
              docs.length ? "No matching documents" : "Your library starts here"
            }
            description={
              docs.length
                ? "Try a different filter or search."
                : "Upload PDF, Word, Markdown, or text files. We’ll take it from there."
            }
            action={canWrite && uploadButton}
          />
        )}
        <div className="panel-footer">
          <span>{filteredDocs.length} documents</span>
          <span>
            <ShieldCheck size={14} />
            Permission-aware by default
          </span>
        </div>
      </section>
    </>
  );
}
