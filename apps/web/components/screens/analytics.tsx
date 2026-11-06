"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { bytes } from "@/lib/api";
import {
  Check,
  Database,
  Files,
  Layers,
  MessageSquare,
  RefreshCw,
} from "lucide-react";
import { PageHeading, StatCard } from "../shared/ui";
export default function AnalyticsScreen({
  title,
  description,
  action,
  refresh,
  stats,
}: ScreenContracts["analytics"]) {
  return (
    <>
      <PageHeading
        eyebrow="A CLEARER VIEW"
        title="Usage & analytics"
        description="A live snapshot of the knowledge available to you."
        action={
          <button className="btn" onClick={() => action(refresh)}>
            <RefreshCw size={15} />
            Refresh metrics
          </button>
        }
      />
      <div className="stat-grid">
        <StatCard
          label="Accessible documents"
          value={stats?.documents || 0}
          icon={Files}
          note="Current library"
        />
        <StatCard
          label="Searchable passages"
          value={stats?.chunks || 0}
          icon={Layers}
          note="Successfully extracted chunks"
          accent
        />
        <StatCard
          label="Your conversations"
          value={stats?.conversations || 0}
          icon={MessageSquare}
          note="Personal conversation count"
        />
        <StatCard
          label="Stored content"
          value={bytes(stats?.storage_bytes || 0)}
          icon={Database}
          note="Original document bytes"
        />
      </div>
      <div className="analytics-grid">
        <section className="panel analytics-panel">
          <h2>Document processing</h2>
          <p className="muted">Current state, not historical throughput</p>
          {[
            ["Indexed", stats?.ready || 0, "green"],
            ["Processing", stats?.processing || 0, "amber"],
            ["Failed", stats?.failed || 0, "red"],
          ].map(([label, value, color]) => (
            <div className="bar-row" key={label}>
              <div>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
              <div className="bar-track">
                <i
                  className={String(color)}
                  style={{
                    width: `${(Number(value) / Math.max(stats?.documents || 1, 1)) * 100}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </section>
        <section className="panel analytics-panel">
          <h2>Intelligence configuration</h2>
          <div className="setting-row">
            <span>Retrieval engine</span>
            <strong>
              {stats?.retrieval === "hybrid"
                ? "PostgreSQL hybrid"
                : stats?.retrieval === "full-text"
                  ? "PostgreSQL full-text"
                  : "Development keyword"}
            </strong>
          </div>
          <div className="setting-row">
            <span>Answer generation</span>
            <strong>
              {stats?.provider_configured
                ? "OpenAI-compatible model"
                : "Extractive passages"}
            </strong>
          </div>
          <div className="setting-row">
            <span>Source attribution</span>
            <span className="status ready">
              <Check size={12} />
              Enabled
            </span>
          </div>
          <div className="info-box">
            Token-level cost accounting and historical charts are not
            implemented. No estimated or simulated usage is displayed.
          </div>
        </section>
      </div>
    </>
  );
}
