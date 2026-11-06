"use client";
import type { ForgeController } from "@/hooks/use-forge-controller";
import { api } from "@/lib/api";
import { ArrowUpRight, FolderOpen, Plus, Trash2 } from "lucide-react";
import { Empty, PageHeading } from "../shared/ui";
type Props = Pick<
  ForgeController,
  | "view"
  | "canWrite"
  | "setFormName"
  | "setDescription"
  | "setModal"
  | "workspaces"
  | "setConfirm"
  | "base"
  | "refresh"
  | "docs"
  | "setWorkspaceFilter"
  | "router"
>;
export default function WorkspacesScreen({
  view,
  canWrite,
  setFormName,
  setDescription,
  setModal,
  workspaces,
  setConfirm,
  base,
  refresh,
  docs,
  setWorkspaceFilter,
  router,
}: Props) {
  return (
    <>
      <PageHeading
        eyebrow="ORGANIZE WITH INTENTION"
        title={
          view === "collections" ? "Knowledge collections" : "Your workspaces"
        }
        description="Give every project, team, and big idea a place to belong."
        action={
          canWrite && (
            <button
              className="btn primary"
              onClick={() => {
                setFormName("");
                setDescription("");
                setModal("workspace");
              }}
            >
              <Plus size={16} />
              New workspace
            </button>
          )
        }
      />
      {view === "collections" && (
        <div className="info-box">
          Collections currently map to workspaces. Nested collections are a
          future feature.
        </div>
      )}
      <div className="workspace-grid">
        {workspaces.map((w, i) => (
          <article className="panel workspace-card" key={w.id}>
            <div className="workspace-card-top">
              <span className={"folder-icon color-" + (i % 3)}>
                <FolderOpen size={24} />
              </span>
              {canWrite && (
                <button
                  aria-label={"Delete " + w.name}
                  className="icon-btn"
                  onClick={() =>
                    setConfirm({
                      label:
                        "Delete “" + w.name + "”? Workspaces must be empty.",
                      run: async () => {
                        await api(base + "/workspaces/" + w.id, {
                          method: "DELETE",
                        });
                        await refresh();
                      },
                    })
                  }
                >
                  <Trash2 size={15} />
                </button>
              )}
            </div>
            <h2>{w.name}</h2>
            <p>
              {w.description || "A shared space for your team’s knowledge."}
            </p>
            <div className="workspace-card-bottom">
              <span>
                {docs.filter((d) => d.workspace_id === w.id).length} documents
              </span>
              <button
                className="text-link"
                onClick={() => {
                  setWorkspaceFilter(w.id);
                  router.push("/documents");
                }}
              >
                Open workspace <ArrowUpRight size={15} />
              </button>
            </div>
          </article>
        ))}
      </div>
      {!workspaces.length && (
        <Empty
          icon={FolderOpen}
          title="A place for every project"
          description="Create a workspace to organize your documents."
        />
      )}
    </>
  );
}
