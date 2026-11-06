"use client";
import type { ForgeController } from "@/hooks/use-forge-controller";
import { api } from "@/lib/api";
import { Check, LogOut, Moon, ShieldCheck, Sun } from "lucide-react";
import { PageHeading } from "../shared/ui";
type Props = Pick<
  ForgeController,
  | "title"
  | "view"
  | "action"
  | "loadMe"
  | "router"
  | "base"
  | "notify"
  | "me"
  | "org"
  | "busy"
  | "setDark"
  | "dark"
  | "logout"
> & { me: NonNullable<ForgeController["me"]> };
export default function SettingsScreen({
  title,
  view,
  action,
  loadMe,
  router,
  base,
  notify,
  me,
  org,
  busy,
  setDark,
  dark,
  logout,
}: Props) {
  return (
    <>
      <PageHeading
        eyebrow="MAKE IT YOURS"
        title={title}
        description={
          view === "profile"
            ? "Your identity in your knowledge workspace."
            : "A few thoughtful defaults for a well-connected team."
        }
      />
      <div className="settings-grid">
        <section className="panel settings-panel">
          <h2>
            {view === "profile"
              ? "Personal details"
              : view === "onboarding"
                ? "Create organization"
                : "Organization details"}
          </h2>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const data = new FormData(e.currentTarget);
              action(async () => {
                if (view === "profile") {
                  await api("/profile", {
                    method: "PATCH",
                    body: JSON.stringify({ name: data.get("name") }),
                  });
                  await loadMe();
                } else if (view === "onboarding") {
                  await api("/organizations", {
                    method: "POST",
                    body: JSON.stringify({ name: data.get("name") }),
                  });
                  await loadMe();
                  router.push("/dashboard");
                } else {
                  await api(base, {
                    method: "PATCH",
                    body: JSON.stringify({ name: data.get("name") }),
                  });
                  await loadMe();
                }
                notify("Changes saved");
              });
            }}
          >
            <label>
              {view === "profile" ? "Display name" : "Organization name"}
              <input
                name="name"
                minLength={2}
                maxLength={100}
                required
                defaultValue={
                  view === "profile"
                    ? me.user.name
                    : view === "onboarding"
                      ? ""
                      : org?.name
                }
                key={view + org?.id}
              />
            </label>
            {view === "profile" && (
              <>
                <label>
                  Email address
                  <input value={me.user.email} readOnly />
                </label>
                <span
                  className={
                    "status " + (me.user.verified ? "ready" : "queued")
                  }
                >
                  {me.user.verified ? "Email verified" : "Email not verified"}
                </span>
                <p className="fineprint">
                  Email verification requires an SMTP provider. Email address
                  changes are not supported yet.
                </p>
              </>
            )}
            <button
              className="btn primary"
              disabled={busy || (view === "settings" && org?.role !== "owner")}
            >
              {view === "onboarding" ? "Create organization" : "Save changes"}
              <Check size={15} />
            </button>
          </form>
        </section>
        <section className="panel settings-panel">
          <h2>Workspace preferences</h2>
          <div className="setting-row">
            <div>
              <strong>Appearance</strong>
              <p>Choose the view that works for you.</p>
            </div>
            <button className="btn" onClick={() => setDark(!dark)}>
              {dark ? <Sun size={15} /> : <Moon size={15} />}{" "}
              {dark ? "Light" : "Dark"}
            </button>
          </div>
          <div className="setting-row">
            <div>
              <strong>Account session</strong>
              <p>HttpOnly cookie · 8-hour expiry</p>
            </div>
            <span className="status ready">Active</span>
          </div>
          <button className="btn" onClick={logout}>
            <LogOut size={15} />
            Sign out
          </button>
        </section>
      </div>
      <section className="panel settings-panel integration-info">
        <div>
          <ShieldCheck size={24} />
          <h2>Designed to keep knowledge in the right hands.</h2>
          <p>
            Organization-level isolation and document permissions are enforced
            by the API, not just the interface.
          </p>
        </div>
        <span className="tag">SECURITY BY DESIGN</span>
      </section>
    </>
  );
}
