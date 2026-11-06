"use client";
import useForgeController from "@/hooks/use-forge-controller";
import { api } from "@/lib/api";
import type { Org } from "@/lib/types";
import {
  Activity,
  AlertCircle,
  ArrowRight,
  ArrowUpRight,
  ChartNoAxesCombined,
  Check,
  ChevronDown,
  ChevronRight,
  Files,
  FolderOpen,
  Layers,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  MessageSquare,
  Moon,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  Sun,
  Users,
  X,
} from "lucide-react";
import Link from "next/link";
import AnalyticsScreen from "./screens/analytics";
import AuditScreen from "./screens/audit";
import ChatScreen from "./screens/chat";
import ConversationsScreen from "./screens/conversations";
import DashboardScreen from "./screens/dashboard";
import DocumentsScreen from "./screens/documents";
import MembersScreen from "./screens/members";
import PublicScreen from "./screens/public";
import SearchScreen from "./screens/search";
import SettingsScreen from "./screens/settings";
import WorkspacesScreen from "./screens/workspaces";
import WorkspaceDialogs from "./shared/dialogs";
import { Empty, Logo, Modal } from "./shared/ui";

const nav = [
  { label: "Overview", path: "dashboard", icon: LayoutDashboard },
  { label: "AI assistant", path: "chat", icon: Sparkles },
  { label: "Search", path: "search", icon: Search },
  { label: "Document library", path: "documents", icon: Files },
  { label: "Workspaces", path: "workspaces", icon: FolderOpen },
  { label: "Conversations", path: "conversations", icon: MessageSquare },
];
const adminNav = [
  { label: "Usage & analytics", path: "analytics", icon: ChartNoAxesCombined },
  { label: "Members", path: "members", icon: Users },
  { label: "Audit activity", path: "audit", icon: Activity },
  { label: "Settings", path: "settings", icon: Settings },
];

export default function Forge() {
  const {
    pathname,
    router,
    me,
    setMe,
    org,
    setOrg,
    boot,
    setBoot,
    dark,
    setDark,
    mobile,
    setMobile,
    view,
    docs,
    setDocs,
    workspaces,
    setWorkspaces,
    stats,
    setStats,
    convs,
    setConvs,
    members,
    setMembers,
    audits,
    setAudits,
    busy,
    setBusy,
    loading,
    setLoading,
    notice,
    setNotice,
    error,
    setError,
    modal,
    setModal,
    selected,
    setSelected,
    source,
    setSource,
    confirm,
    setConfirm,
    query,
    setQuery,
    results,
    setResults,
    filter,
    setFilter,
    docQuery,
    setDocQuery,
    workspaceFilter,
    setWorkspaceFilter,
    messages,
    setMessages,
    conversation,
    setConversation,
    question,
    setQuestion,
    formName,
    setFormName,
    description,
    setDescription,
    memberEmail,
    setMemberEmail,
    memberRole,
    setMemberRole,
    uploadWorkspace,
    setUploadWorkspace,
    visibility,
    setVisibility,
    dragging,
    setDragging,
    fileInput,
    chatEnd,
    register,
    handleSubmit,
    errors,
    reset,
    base,
    canWrite,
    notify,
    fail,
    loadMe,
    refresh,
    action,
    signIn,
    demo,
    logout,
    upload,
    ask,
    openConversation,
    openDoc,
    search,
    newChat,
    exportActivity,
    uploadButton,
    filteredDocs,
    title,
  } = useForgeController();
  if (boot)
    return (
      <div className="boot">
        <Logo />
        <LoaderCircle className="spin" />
        <p>Opening your knowledge workspace…</p>
      </div>
    );
  const authViews = [
    "login",
    "register",
    "forgot-password",
    "reset-password",
    "verify-email",
  ];
  if (!me || authViews.includes(view))
    return (
      <PublicScreen
        error={error}
        setError={setError}
        view={view}
        action={action}
        notify={notify}
        router={router}
        busy={busy}
        me={me}
        loadMe={loadMe}
        memberEmail={memberEmail}
        setMemberEmail={setMemberEmail}
        handleSubmit={handleSubmit}
        signIn={signIn}
        register={register}
        errors={errors}
        demo={demo}
        notice={notice}
      />
    );
  return (
    <div className="app-shell">
      <aside className={"sidebar " + (mobile ? "mobile-open" : "")}>
        <Link href="/dashboard">
          <Logo />
        </Link>
        <button className="org-switch" onClick={() => setModal("switch-org")}>
          <span className="org-avatar">{org?.name[0] || "K"}</span>
          <span>
            <strong>{org?.name || "Create organization"}</strong>
            <small>
              {org?.name.includes("Demo")
                ? "Seeded demo workspace"
                : "Team workspace"}
            </small>
          </span>
          <ChevronDown size={15} />
        </button>
        <div className="nav-label">WORKSPACE</div>
        <nav>
          {nav.map((n) => (
            <Link
              key={n.path}
              href={"/" + n.path}
              className={"nav-item " + (view === n.path ? "active" : "")}
            >
              <n.icon size={18} />
              {n.label}
              {n.path === "chat" && <span className="nav-new">AI</span>}
              {n.path === "documents" && (
                <span className="nav-count">{docs.length}</span>
              )}
            </Link>
          ))}
        </nav>
        <div className="nav-label management-label">MANAGE</div>
        <nav>
          {adminNav
            .filter((n) => !["members", "audit"].includes(n.path) || canWrite)
            .map((n) => (
              <Link
                key={n.path}
                href={"/" + n.path}
                className={"nav-item " + (view === n.path ? "active" : "")}
              >
                <n.icon size={18} />
                {n.label}
              </Link>
            ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="workspace-health">
            <span className="live-dot" />
            <span>Workspace connected</span>
            <button
              aria-label="Refresh workspace"
              onClick={() => action(refresh)}
            >
              <RefreshCw size={13} />
            </button>
          </div>
          <button
            className="profile-button"
            onClick={() => router.push("/profile")}
          >
            <span className="avatar">
              {me.user.name
                .split(" ")
                .map((n) => n[0])
                .slice(0, 2)
                .join("")}
            </span>
            <span>
              <strong>{me.user.name}</strong>
              <small>{org?.role || "Member"}</small>
            </span>
            <Settings size={16} />
          </button>
        </div>
      </aside>
      {mobile && (
        <div className="sidebar-shade" onClick={() => setMobile(false)} />
      )}
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-btn mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobile(true)}
            >
              <Menu size={19} />
            </button>
            <span className="desktop-only">Workspace</span>
            <ChevronRight className="desktop-only" size={14} />
            <strong>{title}</strong>
          </div>
          <div className="topbar-actions">
            <button
              className="global-search"
              onClick={() => router.push("/search")}
            >
              <Search size={15} />
              Search anything…<kbd>⌘ K</kbd>
            </button>
            <button
              className="icon-btn"
              aria-label={dark ? "Use light theme" : "Use dark theme"}
              onClick={() => setDark(!dark)}
            >
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <div className="header-divider" />
            <button
              className="avatar small"
              onClick={() => router.push("/profile")}
              aria-label="Open profile"
            >
              {me.user.name[0]}
            </button>
          </div>
        </header>
        <main
          className={"main-content " + (view === "chat" ? "chat-main" : "")}
        >
          {error && (
            <div className="error-banner" role="alert">
              <AlertCircle size={17} />
              {error}
              <button aria-label="Dismiss error" onClick={() => setError("")}>
                <X size={16} />
              </button>
            </div>
          )}
          {org?.name.includes("Demo") && (
            <div className="demo-banner">
              <span>
                <Sparkles size={13} /> DEMO WORKSPACE
              </span>
              Synthetic documents · Real retrieval ·{" "}
              {stats?.provider_configured
                ? "AI provider enabled"
                : "Extractive mode, no LLM configured"}
              <button onClick={() => setModal("new-org")}>
                Create your own <ArrowUpRight size={12} />
              </button>
            </div>
          )}
          {loading && !stats ? (
            <div className="skeleton">
              <div />
              <div />
              <div />
            </div>
          ) : view === "dashboard" ? (
            <DashboardScreen
              me={me}
              canWrite={canWrite}
              uploadButton={uploadButton}
              stats={stats}
              newChat={newChat}
              docs={docs}
              openDoc={openDoc}
              title={title}
              description={description}
              action={action}
              workspaces={workspaces}
              setWorkspaceFilter={setWorkspaceFilter}
              router={router}
              setFormName={setFormName}
              setDescription={setDescription}
              setModal={setModal}
            />
          ) : view === "documents" ? (
            <DocumentsScreen
              title={title}
              description={description}
              action={action}
              canWrite={canWrite}
              uploadButton={uploadButton}
              stats={stats}
              filter={filter}
              setFilter={setFilter}
              docs={docs}
              docQuery={docQuery}
              setDocQuery={setDocQuery}
              workspaceFilter={workspaceFilter}
              setWorkspaceFilter={setWorkspaceFilter}
              workspaces={workspaces}
              filteredDocs={filteredDocs}
              openDoc={openDoc}
            />
          ) : view === "workspaces" || view === "collections" ? (
            <WorkspacesScreen
              view={view}
              canWrite={canWrite}
              setFormName={setFormName}
              setDescription={setDescription}
              setModal={setModal}
              workspaces={workspaces}
              setConfirm={setConfirm}
              base={base}
              refresh={refresh}
              docs={docs}
              setWorkspaceFilter={setWorkspaceFilter}
              router={router}
            />
          ) : view === "chat" ? (
            <ChatScreen
              stats={stats}
              newChat={newChat}
              messages={messages}
              busy={busy}
              org={org}
              ask={ask}
              me={me}
              setSource={setSource}
              chatEnd={chatEnd}
              question={question}
              setQuestion={setQuestion}
            />
          ) : view === "search" ? (
            <SearchScreen
              title={title}
              description={description}
              search={search}
              query={query}
              setQuery={setQuery}
              busy={busy}
              stats={stats}
              results={results}
              setSource={setSource}
            />
          ) : view === "conversations" ? (
            <ConversationsScreen
              title={title}
              description={description}
              action={action}
              newChat={newChat}
              convs={convs}
              openConversation={openConversation}
              setConfirm={setConfirm}
              base={base}
              conversation={conversation}
              refresh={refresh}
            />
          ) : view === "analytics" ? (
            <AnalyticsScreen
              title={title}
              description={description}
              action={action}
              refresh={refresh}
              stats={stats}
            />
          ) : view === "members" ? (
            <MembersScreen
              title={title}
              description={description}
              action={action}
              org={org}
              setModal={setModal}
              members={members}
              base={base}
              setMembers={setMembers}
              notify={notify}
              setConfirm={setConfirm}
            />
          ) : view === "audit" ? (
            <AuditScreen
              title={title}
              description={description}
              action={action}
              exportActivity={exportActivity}
              audits={audits}
            />
          ) : view === "settings" ||
            view === "profile" ||
            view === "onboarding" ? (
            <SettingsScreen
              title={title}
              view={view}
              action={action}
              loadMe={loadMe}
              router={router}
              base={base}
              notify={notify}
              me={me}
              org={org}
              busy={busy}
              setDark={setDark}
              dark={dark}
              logout={logout}
            />
          ) : (
            <Empty
              icon={AlertCircle}
              title="This page is off the map"
              description="The page you’re looking for doesn’t exist, or you don’t have access."
              action={
                <Link className="btn primary" href="/dashboard">
                  Back to overview <ArrowRight size={15} />
                </Link>
              }
            />
          )}
          {view !== "chat" && (
            <footer className="app-footer">
              <span>
                <Layers size={13} />
                KnowledgeForge AI
              </span>
              <span>Less searching. More knowing.</span>
              <span>
                <span className="live-dot" />
                Workspace connected
              </span>
            </footer>
          )}
        </main>
      </div>

      {(modal === "new-org" || modal === "switch-org") && (
        <Modal
          title={
            modal === "new-org"
              ? "Create your organization"
              : "Switch workspace"
          }
          close={() => setModal("")}
        >
          {modal === "switch-org" ? (
            <>
              <div className="org-list">
                {me.organizations.map((o) => (
                  <button
                    key={o.id}
                    onClick={() => {
                      setOrg(o);
                      setMessages([]);
                      setConversation(null);
                      setResults(null);
                      setModal("");
                      router.push("/dashboard");
                    }}
                  >
                    <span className="org-avatar">{o.name[0]}</span>
                    <span>
                      <strong>{o.name}</strong>
                      <small>{o.role}</small>
                    </span>
                    {org?.id === o.id ? (
                      <Check size={17} />
                    ) : (
                      <ArrowRight size={17} />
                    )}
                  </button>
                ))}
              </div>
              <button
                className="btn wide"
                onClick={() => {
                  setFormName("");
                  setModal("new-org");
                }}
              >
                <Plus size={16} />
                Create organization
              </button>
            </>
          ) : (
            <form
              onSubmit={(e) => {
                e.preventDefault();
                action(async () => {
                  const created = await api<Org>("/organizations", {
                    method: "POST",
                    body: JSON.stringify({ name: formName }),
                  });
                  await loadMe();
                  setOrg({ ...created, role: "owner" });
                  setModal("");
                  router.push("/dashboard");
                });
              }}
            >
              <label>
                Organization name
                <input
                  required
                  minLength={2}
                  maxLength={100}
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                />
              </label>
              <button className="btn primary wide" disabled={busy}>
                Create organization
                <ArrowRight size={15} />
              </button>
            </form>
          )}
        </Modal>
      )}

      <WorkspaceDialogs
        notice={notice}
        setNotice={setNotice}
        modal={modal}
        setModal={setModal}
        dragging={dragging}
        setDragging={setDragging}
        upload={upload}
        busy={busy}
        fileInput={fileInput}
        uploadWorkspace={uploadWorkspace}
        setUploadWorkspace={setUploadWorkspace}
        workspaces={workspaces}
        visibility={visibility}
        setVisibility={setVisibility}
        action={action}
        base={base}
        formName={formName}
        description={description}
        refresh={refresh}
        notify={notify}
        setFormName={setFormName}
        setDescription={setDescription}
        memberEmail={memberEmail}
        memberRole={memberRole}
        setMembers={setMembers}
        setMemberEmail={setMemberEmail}
        setMemberRole={setMemberRole}
        selected={selected}
        setSelected={setSelected}
        canWrite={canWrite}
        setConfirm={setConfirm}
        source={source}
        setSource={setSource}
        confirm={confirm}
      />
    </div>
  );
}
