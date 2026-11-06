"use client";
import { bytes, date } from "@/lib/api";
import type { Doc } from "@/lib/types";
import {
  AlertCircle,
  CheckCircle2,
  Clock,
  Files,
  FileText,
  Layers,
  MoreHorizontal,
  X,
} from "lucide-react";
import React, { useEffect, useRef } from "react";
export function Logo() {
  return (
    <span className="brand">
      <span className="logo">
        <Layers size={21} />
      </span>
      KnowledgeForge<span className="ai-tag">AI</span>
    </span>
  );
}

export function Status({ value }: { value: string }) {
  return (
    <span className={"status " + value}>
      {value === "ready" ? (
        <CheckCircle2 size={12} />
      ) : value === "failed" ? (
        <AlertCircle size={12} />
      ) : (
        <Clock size={12} />
      )}{" "}
      {value === "ready" ? "Indexed" : value[0].toUpperCase() + value.slice(1)}
    </span>
  );
}

export function Empty({
  icon: Icon = Files,
  title,
  description,
  action,
}: {
  icon?: typeof Files;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon size={27} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}

const modalStack: HTMLElement[] = [];

export function Modal({
  title,
  children,
  close,
}: {
  title: string;
  children: React.ReactNode;
  close: () => void;
}) {
  const el = useRef<HTMLDivElement>(null);
  const onClose = useRef(close);
  onClose.current = close;
  useEffect(() => {
    const old = document.activeElement as HTMLElement;
    const node = el.current!;
    modalStack.push(node);
    const controls =
      "button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href]";
    (node.querySelector<HTMLElement>(controls) || node).focus();
    const key = (e: KeyboardEvent) => {
      if (modalStack[modalStack.length - 1] !== node) return;
      if (e.key === "Escape") onClose.current();
      if (e.key === "Tab") {
        const all = el.current?.querySelectorAll<HTMLElement>(controls);
        if (!all?.length) return;
        const first = all[0],
          last = all[all.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      const index = modalStack.indexOf(node);
      if (index >= 0) modalStack.splice(index, 1);
      old?.focus();
    };
  }, []);
  return (
    <div className="modal-backdrop" onClick={close}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        tabIndex={-1}
        ref={el}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-head">
          <h2>{title}</h2>
          <button
            className="icon-btn"
            aria-label="Close dialog"
            onClick={close}
          >
            <X size={19} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function PageHeading({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <div className="eyebrow page-eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action}
    </div>
  );
}

export function StatCard({
  label,
  value,
  icon: Icon,
  note,
  accent = false,
}: {
  label: string;
  value: number | string;
  icon: typeof Files;
  note: string;
  accent?: boolean;
}) {
  return (
    <article className={"stat-card " + (accent ? "accent" : "")}>
      <div>
        <span>{label}</span>
        <span className="stat-icon">
          <Icon size={17} />
        </span>
      </div>
      <strong>{value}</strong>
      <small>
        {accent && <span className="live-dot" />}
        {note}
      </small>
    </article>
  );
}

export function DocTable({
  docs,
  open,
  compact = false,
}: {
  docs: Doc[];
  open: (doc: Doc) => void;
  compact?: boolean;
}) {
  return (
    <div className="table-scroll">
      <table className={compact ? "compact-table" : ""}>
        <thead>
          <tr>
            <th>DOCUMENT NAME</th>
            <th>STATUS</th>
            {!compact && <th>SIZE</th>}
            <th>ADDED</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {docs.map((d) => (
            <tr key={d.id}>
              <td>
                <button className="document-cell" onClick={() => open(d)}>
                  <span
                    className={
                      "file-icon " +
                      (d.name.endsWith(".pdf")
                        ? "pdf"
                        : d.name.endsWith(".md")
                          ? "md"
                          : "")
                    }
                  >
                    <FileText size={19} />
                    <small>{d.name.split(".").pop()?.toUpperCase()}</small>
                  </span>
                  <span>
                    <strong>{d.name}</strong>
                    <small>
                      {d.visibility === "private"
                        ? "Private document"
                        : d.chunks + " searchable passages"}
                    </small>
                  </span>
                </button>
              </td>
              <td>
                <Status value={d.status} />
              </td>
              {!compact && <td className="muted">{bytes(d.size)}</td>}
              <td className="date-cell">{date(d.created_at)}</td>
              <td>
                <button
                  className="icon-btn"
                  aria-label={"View details for " + d.name}
                  onClick={() => open(d)}
                >
                  <MoreHorizontal size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
