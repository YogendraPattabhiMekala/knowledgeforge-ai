"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { api } from "@/lib/api";
import type { Member } from "@/lib/types";
import { Plus, ShieldCheck, Trash2 } from "lucide-react";
import { PageHeading } from "../shared/ui";
export default function MembersScreen({
  title,
  description,
  action,
  org,
  setModal,
  members,
  base,
  setMembers,
  notify,
  setConfirm,
}: ScreenContracts["members"]) {
  return (
    <>
      <PageHeading
        eyebrow="KNOWLEDGE IS A TEAM EFFORT"
        title="Members & permissions"
        description="The right people. The right access."
        action={
          org?.role === "owner" && (
            <button className="btn primary" onClick={() => setModal("member")}>
              <Plus size={16} />
              Add member
            </button>
          )
        }
      />
      <section className="panel">
        <div className="section-head">
          <h2>
            Organization members{" "}
            <span className="count-badge">{members.length}</span>
          </h2>
          <span className="muted">Server-enforced roles</span>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>MEMBER</th>
                <th>ROLE</th>
                <th>ACCESS</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {members.map((m) => (
                <tr key={m.id}>
                  <td>
                    <div className="member-cell">
                      <span className="avatar">{m.name[0]}</span>
                      <span>
                        <strong>{m.name}</strong>
                        <small>{m.email}</small>
                      </span>
                    </div>
                  </td>
                  <td>
                    {org?.role === "owner" && m.role !== "owner" ? (
                      <select
                        aria-label={"Role for " + m.name}
                        value={m.role}
                        onChange={(e) =>
                          action(async () => {
                            await api(base + "/members/" + m.id, {
                              method: "PATCH",
                              body: JSON.stringify({ role: e.target.value }),
                            });
                            setMembers(await api<Member[]>(base + "/members"));
                            notify("Role updated");
                          })
                        }
                      >
                        <option>admin</option>
                        <option>member</option>
                        <option>viewer</option>
                      </select>
                    ) : (
                      <span className="role-badge">{m.role}</span>
                    )}
                  </td>
                  <td className="muted">
                    {["owner", "admin"].includes(m.role)
                      ? "Manage knowledge"
                      : m.role === "member"
                        ? "Search & ask"
                        : "Read & search"}
                  </td>
                  <td>
                    {org?.role === "owner" && m.role !== "owner" && (
                      <button
                        className="icon-btn danger-text"
                        aria-label={"Remove " + m.name}
                        onClick={() =>
                          setConfirm({
                            label:
                              "Remove " + m.name + " from this organization?",
                            run: async () => {
                              await api(base + "/members/" + m.id, {
                                method: "DELETE",
                              });
                              setMembers(
                                await api<Member[]>(base + "/members"),
                              );
                            },
                          })
                        }
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="info-box">
        <ShieldCheck size={17} />
        Private documents are limited to their uploader and organization
        administrators. Members only see their own conversations.
      </div>
    </>
  );
}
