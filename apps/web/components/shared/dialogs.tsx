"use client";
import { api, bytes, date } from "@/lib/api";
import type { Doc, Member } from "@/lib/types";
import {
  ArrowDownToLine,
  Check,
  CheckCircle2,
  FileText,
  Lock,
  Plus,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Upload,
  Users,
  X,
} from "lucide-react";
import { Modal, Status } from "./ui";

import type { ForgeController } from "@/hooks/use-forge-controller";
type Props = Pick<
  ForgeController,
  | "notice"
  | "setNotice"
  | "modal"
  | "setModal"
  | "dragging"
  | "setDragging"
  | "upload"
  | "busy"
  | "fileInput"
  | "uploadWorkspace"
  | "setUploadWorkspace"
  | "workspaces"
  | "visibility"
  | "setVisibility"
  | "action"
  | "base"
  | "formName"
  | "description"
  | "refresh"
  | "notify"
  | "setFormName"
  | "setDescription"
  | "memberEmail"
  | "memberRole"
  | "setMembers"
  | "setMemberEmail"
  | "setMemberRole"
  | "selected"
  | "setSelected"
  | "canWrite"
  | "setConfirm"
  | "source"
  | "setSource"
  | "confirm"
>;
export default function WorkspaceDialogs({
  notice,
  setNotice,
  modal,
  setModal,
  dragging,
  setDragging,
  upload,
  busy,
  fileInput,
  uploadWorkspace,
  setUploadWorkspace,
  workspaces,
  visibility,
  setVisibility,
  action,
  base,
  formName,
  description,
  refresh,
  notify,
  setFormName,
  setDescription,
  memberEmail,
  memberRole,
  setMembers,
  setMemberEmail,
  setMemberRole,
  selected,
  setSelected,
  canWrite,
  setConfirm,
  source,
  setSource,
  confirm,
}: Props) {
  return (
    <>
      {notice && (
        <div className="toast" role="status">
          <CheckCircle2 size={17} />
          {notice}
          <button
            aria-label="Dismiss notification"
            onClick={() => setNotice("")}
          >
            <X size={15} />
          </button>
        </div>
      )}
      {modal === "upload" && (
        <Modal title="Add to your knowledge" close={() => setModal("")}>
          <p className="muted">
            Upload once. Put your knowledge to work everywhere.
          </p>
          <label
            className={"dropzone " + (dragging ? "dragging" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              upload(e.dataTransfer.files);
            }}
          >
            <span className="empty-icon">
              <Upload size={27} />
            </span>
            <strong>
              {busy ? "Uploading your documents…" : "Drop your documents here"}
            </strong>
            <span>
              or <b>browse files</b> to get started
            </span>
            <small>PDF, DOCX, MD, TXT · up to 20 MB each</small>
            <input
              ref={fileInput}
              type="file"
              multiple
              accept=".pdf,.docx,.md,.txt"
              disabled={busy}
              onChange={(e) => {
                if (e.target.files) upload(e.target.files);
              }}
            />
          </label>
          <label>
            Workspace
            <select
              value={uploadWorkspace}
              onChange={(e) => setUploadWorkspace(e.target.value)}
            >
              <option value="">Unassigned</option>
              {workspaces.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            Access
            <select
              value={visibility}
              onChange={(e) => setVisibility(e.target.value)}
            >
              <option value="organization">
                Everyone in this organization
              </option>
              <option value="private">
                Private · you and administrators only
              </option>
            </select>
          </label>
          <div className="info-box">
            <Lock size={15} />
            Files stay within your organization. Scanned PDFs require OCR, which
            is not supported.
          </div>
        </Modal>
      )}
      {modal === "workspace" && (
        <Modal title="A space for shared knowledge" close={() => setModal("")}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              action(async () => {
                await api(base + "/workspaces", {
                  method: "POST",
                  body: JSON.stringify({ name: formName, description }),
                });
                setModal("");
                await refresh();
                notify("Workspace created");
              });
            }}
          >
            <label>
              Workspace name
              <input
                required
                minLength={2}
                maxLength={100}
                autoFocus
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Engineering"
              />
            </label>
            <label>
              Description
              <textarea
                maxLength={500}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What belongs in this space?"
              />
            </label>
            <button className="btn primary wide" disabled={busy}>
              <Plus size={16} />
              Create workspace
            </button>
          </form>
        </Modal>
      )}
      {modal === "member" && (
        <Modal title="Bring your team together" close={() => setModal("")}>
          <p className="muted">
            Add an existing KnowledgeForge user. Email invitations are not yet
            available.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              action(async () => {
                await api(base + "/members", {
                  method: "POST",
                  body: JSON.stringify({
                    email: memberEmail,
                    role: memberRole,
                  }),
                });
                setMembers(await api<Member[]>(base + "/members"));
                setModal("");
                notify("Member added");
              });
            }}
          >
            <label>
              Email address
              <input
                type="email"
                required
                value={memberEmail}
                onChange={(e) => setMemberEmail(e.target.value)}
              />
            </label>
            <label>
              Role
              <select
                value={memberRole}
                onChange={(e) => setMemberRole(e.target.value)}
              >
                <option value="admin">Administrator · manage knowledge</option>
                <option value="member">Member · search and ask</option>
                <option value="viewer">Viewer · read and search</option>
              </select>
            </label>
            <button className="btn primary wide" disabled={busy}>
              <Users size={15} />
              Add member
            </button>
          </form>
        </Modal>
      )}
      {modal === "document" && selected && (
        <Modal
          title="Document intelligence"
          close={() => {
            setModal("");
            setSelected(null);
          }}
        >
          <div className="document-identity">
            <span className="file-icon">
              <FileText size={24} />
            </span>
            <div>
              <h3>{selected.name}</h3>
              <p>
                {bytes(selected.size)} · Added {date(selected.created_at)}
              </p>
            </div>
            <Status value={selected.status} />
          </div>
          <div className="detail-grid">
            <div>
              <small>SEARCHABLE PASSAGES</small>
              <strong>{selected.chunks}</strong>
            </div>
            <div>
              <small>ACCESS</small>
              <strong>
                {selected.visibility === "private" ? "Private" : "Organization"}
              </strong>
            </div>
            <div>
              <small>PROCESSING ATTEMPTS</small>
              <strong>{selected.attempts}</strong>
            </div>
          </div>
          {selected.error && (
            <div className="info-box error-text">{selected.error}</div>
          )}
          <div className="detail-actions">
            <a
              className="btn"
              href={"/api" + base + "/documents/" + selected.id + "/download"}
            >
              <ArrowDownToLine size={15} />
              Download original
            </a>
            {canWrite && selected.status === "failed" && (
              <button
                className="btn"
                onClick={() =>
                  action(async () => {
                    await api(base + "/documents/" + selected.id + "/retry", {
                      method: "POST",
                    });
                    setModal("");
                    await refresh();
                    notify("Retry queued");
                  })
                }
              >
                <RefreshCw size={15} />
                Retry
              </button>
            )}
            {canWrite && (
              <button
                className="btn danger-text"
                onClick={() =>
                  setConfirm({
                    label:
                      "Permanently delete “" +
                      selected.name +
                      "” and all its searchable passages?",
                    run: async () => {
                      await api(base + "/documents/" + selected.id, {
                        method: "DELETE",
                      });
                      setModal("");
                      await refresh();
                    },
                  })
                }
              >
                <Trash2 size={15} />
                Delete
              </button>
            )}
          </div>
          {canWrite && (
            <form
              className="document-permissions"
              onSubmit={(e) => {
                e.preventDefault();
                const form = new FormData(e.currentTarget);
                action(async () => {
                  const updated = await api<Doc>(
                    base + "/documents/" + selected.id,
                    {
                      method: "PATCH",
                      body: JSON.stringify({
                        visibility: form.get("visibility"),
                        workspace_id: form.get("workspace_id") || null,
                      }),
                    },
                  );
                  setSelected({ ...selected, ...updated });
                  await refresh();
                  notify("Document permissions updated");
                });
              }}
            >
              <label>
                Document access
                <select name="visibility" defaultValue={selected.visibility}>
                  <option value="organization">Organization</option>
                  <option value="private">
                    Private · uploader and administrators
                  </option>
                </select>
              </label>
              <label>
                Workspace
                <select
                  name="workspace_id"
                  defaultValue={selected.workspace_id || ""}
                >
                  <option value="">Unassigned</option>
                  {workspaces.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name}
                    </option>
                  ))}
                </select>
              </label>
              <button className="btn" disabled={busy}>
                <ShieldCheck size={14} />
                Save access
              </button>
            </form>
          )}
          <h3 className="passage-title">
            Extracted passages <span className="muted">(first 100)</span>
          </h3>
          <div className="passage-list">
            {selected.passages?.map((p) => (
              <div key={p.id}>
                <span>
                  {p.page ? "PAGE " + p.page : "PASSAGE " + (p.ordinal + 1)}
                </span>
                <p>{p.text}</p>
              </div>
            ))}
            {!selected.passages?.length && (
              <p className="muted">
                Extracted content will appear once processing completes.
              </p>
            )}
          </div>
        </Modal>
      )}
      {source && (
        <Modal title="Straight from the source" close={() => setSource(null)}>
          <div className="source-heading">
            <FileText size={21} />
            <div>
              <h3>{source.name}</h3>
              <p>
                {source.page
                  ? "Page " + source.page
                  : "Passage " + (source.ordinal + 1)}
              </p>
            </div>
            <span className="status ready">
              <Check size={12} />
              Retrieved evidence
            </span>
          </div>
          <blockquote className="source-text">{source.text}</blockquote>
          {source.document_id && (
            <a
              className="btn"
              href={
                "/api" + base + "/documents/" + source.document_id + "/download"
              }
            >
              <ArrowDownToLine size={15} />
              Download original
            </a>
          )}
          <p className="fineprint">
            A citation links to evidence; it does not guarantee the source is
            accurate or up to date.
          </p>
        </Modal>
      )}
      {confirm && (
        <Modal title="Let’s make sure" close={() => setConfirm(null)}>
          <p className="confirm-copy">{confirm.label}</p>
          <div className="confirm-actions">
            <button className="btn" onClick={() => setConfirm(null)}>
              Keep it
            </button>
            <button
              disabled={busy}
              className="btn danger"
              onClick={() =>
                action(async () => {
                  await confirm.run();
                  setConfirm(null);
                  notify("Deleted successfully");
                })
              }
            >
              <Trash2 size={15} />
              Confirm deletion
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
