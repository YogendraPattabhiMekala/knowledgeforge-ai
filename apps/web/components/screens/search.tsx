"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import {
  ArrowRight,
  ArrowUpRight,
  FileText,
  LoaderCircle,
  Search,
  ShieldCheck,
} from "lucide-react";
import { Empty, PageHeading } from "../shared/ui";
export default function SearchScreen({
  title,
  description,
  search,
  query,
  setQuery,
  busy,
  stats,
  results,
  setSource,
}: ScreenContracts["search"]) {
  return (
    <>
      <PageHeading
        eyebrow="FIND YOUR NEXT PIECE OF CONTEXT"
        title="Search your knowledge"
        description="The right information, without the endless tabs."
      />
      <form className="search-box" onSubmit={search}>
        <Search size={21} />
        <input
          required
          minLength={2}
          maxLength={4000}
          autoFocus
          aria-label="Search documents"
          placeholder="Search policies, playbooks, projects…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn primary" disabled={busy}>
          {busy ? <LoaderCircle size={16} className="spin" /> : "Search"}
          <ArrowRight size={15} />
        </button>
      </form>
      <div className="search-meta">
        <span>
          {stats?.retrieval === "hybrid"
            ? "Hybrid retrieval · semantic + full-text"
            : stats?.retrieval === "full-text"
              ? "PostgreSQL full-text retrieval · no embedding provider"
              : "Development keyword retrieval · no semantic provider"}
        </span>
        <span>
          <ShieldCheck size={13} />
          Permission-filtered results
        </span>
      </div>
      {results === null ? (
        <Empty
          icon={Search}
          title="A good question opens doors"
          description="Search for a topic, a phrase, or something you’ve been meaning to find."
        />
      ) : results.length ? (
        <div className="search-results">
          <span className="muted">{results.length} relevant passages</span>
          {results.map((r) => (
            <button
              className="panel result-card"
              key={r.id}
              onClick={() => setSource(r)}
            >
              <div>
                <FileText size={17} />
                <strong>{r.name}</strong>
                <span>
                  {r.page ? "Page " + r.page : "Passage " + (r.ordinal + 1)}
                </span>
                <ArrowUpRight size={15} />
              </div>
              <p>
                {r.text.slice(0, 550)}
                {r.text.length > 550 ? "…" : ""}
              </p>
              <span className="text-link">
                View original context <ArrowRight size={13} />
              </span>
            </button>
          ))}
        </div>
      ) : (
        <Empty
          icon={Search}
          title="No evidence found"
          description="Try a different phrase, or add a document covering this topic."
        />
      )}
    </>
  );
}
