"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Command,
  Files,
  FileText,
  FolderOpen,
  Layers,
  MessageSquare,
  Plus,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import Link from "next/link";
import { DocTable, Empty, StatCard } from "../shared/ui";
export default function DashboardScreen({
  me,
  canWrite,
  uploadButton,
  stats,
  newChat,
  docs,
  openDoc,
  title,
  description,
  action,
  workspaces,
  setWorkspaceFilter,
  router,
  setFormName,
  setDescription,
  setModal,
}: ScreenContracts["dashboard"]) {
  return (
    <>
      <div className="page-heading">
        <div>
          <div className="eyebrow page-eyebrow">
            <span className="live-dot" /> YOUR KNOWLEDGE, CONNECTED
          </div>
          <h1>
            Welcome back, {me.user.name.split(" ")[0]}{" "}
            <span className="wave">✳</span>
          </h1>
          <p>Bring your team’s knowledge together. Put it to work.</p>
        </div>
        {canWrite && uploadButton}
      </div>
      <div className="stat-grid">
        <StatCard
          label="Total documents"
          value={stats?.documents || 0}
          icon={Files}
          note="Across your accessible library"
        />
        <StatCard
          label="Indexed & ready"
          value={stats?.ready || 0}
          icon={CheckCircle2}
          note={
            stats?.processing
              ? `${stats.processing} processing`
              : "Ready to search and explore"
          }
          accent
        />
        <StatCard
          label="Knowledge chunks"
          value={stats?.chunks || 0}
          icon={Layers}
          note="Searchable, source-linked passages"
        />
        <StatCard
          label="Your conversations"
          value={stats?.conversations || 0}
          icon={MessageSquare}
          note="Ideas explored, context preserved"
        />
      </div>
      <section className="ask-banner">
        <div className="banner-grid" />
        <div className="ask-copy">
          <span className="banner-eyebrow">
            <Sparkles size={15} /> MEET YOUR KNOWLEDGE ASSISTANT
          </span>
          <h2>
            Your next answer is already
            <br />
            in your knowledge.
          </h2>
          <p>Ask a question. Get context. See exactly where it came from.</p>
          <button className="btn light" onClick={newChat}>
            Ask your knowledge <ArrowUpRight size={16} />
          </button>
        </div>
        <div className="banner-art" aria-hidden="true">
          <div className="art-ring ring-one" />
          <div className="art-ring ring-two" />
          <span className="floating-doc doc-a">
            <FileText size={24} />
            <i />
            <i />
            <i />
          </span>
          <div className="art-center">
            <Sparkles size={39} />
          </div>
          <span className="floating-doc doc-b">
            <FileText size={21} />
            <i />
            <i />
            <i />
          </span>
          <span className="art-spark">✦</span>
        </div>
      </section>
      <div className="dashboard-columns">
        <section className="panel recent-panel">
          <div className="section-head">
            <div>
              <h2>
                Recent documents{" "}
                <span className="count-badge">{docs.length}</span>
              </h2>
              <p>Your latest additions to the knowledge base</p>
            </div>
            <Link className="text-link" href="/documents">
              View library <ArrowRight size={14} />
            </Link>
          </div>
          {docs.length ? (
            <DocTable docs={docs.slice(0, 5)} open={openDoc} compact />
          ) : (
            <Empty
              title="A home for your knowledge"
              description="Upload your first document to start finding answers."
              action={canWrite && uploadButton}
            />
          )}
          <div className="panel-footer">
            <span>
              <ShieldCheck size={14} />
              Only documents you can access are shown
            </span>
            <span>{stats?.ready || 0} indexed</span>
          </div>
        </section>
        <section className="panel workspace-panel">
          <div className="section-head">
            <div>
              <h2>Your workspaces</h2>
              <p>Keep knowledge in good company</p>
            </div>
            <Link
              href="/workspaces"
              aria-label="View all workspaces"
              className="icon-btn"
            >
              <ArrowUpRight size={16} />
            </Link>
          </div>
          <div className="workspace-list">
            {workspaces.slice(0, 3).map((w, i) => (
              <button
                className="workspace-row"
                key={w.id}
                onClick={() => {
                  setWorkspaceFilter(w.id);
                  router.push("/documents");
                }}
              >
                <span className={"folder-icon color-" + i}>
                  <FolderOpen size={20} />
                </span>
                <span>
                  <strong>{w.name}</strong>
                  <small>
                    {docs.filter((d) => d.workspace_id === w.id).length}{" "}
                    documents
                  </small>
                </span>
                <ChevronRight size={15} />
              </button>
            ))}
            {!workspaces.length && <p className="muted">No workspaces yet.</p>}
          </div>
          <button
            className="new-workspace"
            onClick={() => {
              if (canWrite) {
                setFormName("");
                setDescription("");
                setModal("workspace");
              } else router.push("/workspaces");
            }}
          >
            <Plus size={15} />
            {canWrite ? "Create workspace" : "View workspaces"}
          </button>
          <div className="tip-card">
            <span>
              <BookOpen size={16} />A little knowledge goes a long way
            </span>
            <p>
              Better sources make better answers. Keep your documents clear,
              current, and connected.
            </p>
          </div>
        </section>
      </div>
      <section className="quick-start">
        <div>
          <span className="small-icon">
            <Command size={18} />
          </span>
          <div>
            <h3>Make room for your next big idea.</h3>
            <p>Explore your knowledge from a different angle.</p>
          </div>
        </div>
        <button onClick={() => router.push("/search")}>
          Search your library <ArrowRight size={15} />
        </button>
      </section>
    </>
  );
}
