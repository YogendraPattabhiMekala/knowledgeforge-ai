"use client";
import { api, setCsrf } from "@/lib/api";
import type {
  Audit,
  Conv,
  Doc,
  Me,
  Member,
  Msg,
  Org,
  Source,
  Stat,
  Workspace,
} from "@/lib/types";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Activity,
  ChartNoAxesCombined,
  Files,
  FolderOpen,
  LayoutDashboard,
  MessageSquare,
  Plus,
  Search,
  Settings,
  Sparkles,
  Users,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
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
const authSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(12, "Use at least 12 characters").max(128),
  name: z.string().optional(),
  organization: z.string().optional(),
});
type AuthData = z.infer<typeof authSchema>;
export default function useForgeController() {
  const pathname = usePathname();
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null),
    [org, setOrg] = useState<Org | null>(null),
    [boot, setBoot] = useState(true),
    [dark, setDark] = useState(false),
    [mobile, setMobile] = useState(false);
  const view = pathname.split("/")[1] || (me ? "dashboard" : "landing");
  const [docs, setDocs] = useState<Doc[]>([]),
    [workspaces, setWorkspaces] = useState<Workspace[]>([]),
    [stats, setStats] = useState<Stat | null>(null),
    [convs, setConvs] = useState<Conv[]>([]),
    [members, setMembers] = useState<Member[]>([]),
    [audits, setAudits] = useState<Audit[]>([]);
  const [busy, setBusy] = useState(false),
    [loading, setLoading] = useState(false),
    [notice, setNotice] = useState(""),
    [error, setError] = useState(""),
    [modal, setModal] = useState(""),
    [selected, setSelected] = useState<Doc | null>(null),
    [source, setSource] = useState<Source | null>(null),
    [confirm, setConfirm] = useState<{
      label: string;
      run: () => Promise<void>;
    } | null>(null);
  const [query, setQuery] = useState(""),
    [results, setResults] = useState<Source[] | null>(null),
    [filter, setFilter] = useState("all"),
    [docQuery, setDocQuery] = useState(""),
    [workspaceFilter, setWorkspaceFilter] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]),
    [conversation, setConversation] = useState<string | null>(null),
    [question, setQuestion] = useState("");
  const [formName, setFormName] = useState(""),
    [description, setDescription] = useState(""),
    [memberEmail, setMemberEmail] = useState(""),
    [memberRole, setMemberRole] = useState("member"),
    [uploadWorkspace, setUploadWorkspace] = useState(""),
    [visibility, setVisibility] = useState("organization"),
    [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null),
    chatEnd = useRef<HTMLDivElement>(null);
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<AuthData>({ resolver: zodResolver(authSchema) });
  const base = org ? "/organizations/" + org.id : "";
  const canWrite = org?.role === "owner" || org?.role === "admin";
  const notify = (text: string) => {
    setNotice(text);
    setTimeout(() => setNotice(""), 5000);
  };
  const fail = (e: unknown) =>
    setError(
      e instanceof Error ? e.message : "Something went wrong. Try again.",
    );
  const loadMe = useCallback(async () => {
    const data = await api<Me>("/auth/me");
    setCsrf(data.csrf);
    setMe(data);
    setOrg(
      (current) =>
        data.organizations.find((o) => o.id === current?.id) ||
        data.organizations[0] ||
        null,
    );
    return data;
  }, []);
  useEffect(() => {
    loadMe()
      .catch(() => {})
      .finally(() => setBoot(false));
    setDark(localStorage.getItem("kf-theme") === "dark");
  }, [loadMe]);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    localStorage.setItem("kf-theme", dark ? "dark" : "light");
  }, [dark]);
  const activeBase = useRef(base);
  activeBase.current = base;
  useEffect(() => {
    setDocs([]);
    setWorkspaces([]);
    setStats(null);
    setConvs([]);
    setMembers([]);
    setAudits([]);
    setMessages([]);
    setConversation(null);
    setResults(null);
    setSource(null);
    setSelected(null);
    setModal("");
    setConfirm(null);
    setUploadWorkspace("");
    setQuestion("");
    setQuery("");
    setNotice("");
    setWorkspaceFilter("");
  }, [base]);
  const setCurrentMembers: typeof setMembers = (value) => {
    if (activeBase.current === base) setMembers(value);
  };
  const refresh = useCallback(async () => {
    if (!base) return;
    const [d, w, s, c] = await Promise.all([
      api<Doc[]>(base + "/documents"),
      api<Workspace[]>(base + "/workspaces"),
      api<Stat>(base + "/analytics"),
      api<Conv[]>(base + "/conversations"),
    ]);
    if (activeBase.current !== base) return;
    setDocs(d);
    setWorkspaces(w);
    setStats(s);
    setConvs(c);
  }, [base]);
  useEffect(() => {
    if (!base) return;
    setLoading(true);
    refresh()
      .catch(fail)
      .finally(() => setLoading(false));
    const timer = setInterval(() => refresh().catch(() => {}), 15000);
    return () => clearInterval(timer);
  }, [refresh, base]);
  useEffect(() => {
    setError("");
    setMobile(false);
    if (!base) return;
    if (view === "members")
      api<Member[]>(base + "/members")
        .then((data) => {
          if (activeBase.current === base) setMembers(data);
        })
        .catch(fail);
    if (view === "audit")
      api<Audit[]>(base + "/audit")
        .then((data) => {
          if (activeBase.current === base) setAudits(data);
        })
        .catch(fail);
  }, [view, base]);
  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        router.push("/search");
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [router]);
  const action = async (fn: () => Promise<void>) => {
    setError("");
    setBusy(true);
    try {
      await fn();
    } catch (e) {
      fail(e);
    } finally {
      setBusy(false);
    }
  };
  const signIn = async (data: AuthData) =>
    action(async () => {
      if (
        view === "register" &&
        (!data.name?.trim() || !data.organization?.trim())
      )
        throw new Error("Name and organization are required.");
      const result = await api<{ csrf: string }>(
        "/auth/" + (view === "register" ? "register" : "login"),
        { method: "POST", body: JSON.stringify(data) },
      );
      setCsrf(result.csrf);
      await loadMe();
      router.push("/dashboard");
      reset();
    });
  const demo = () =>
    action(async () => {
      const data = await api<{ csrf: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: "alex@demo.knowledgeforge.local",
          password: "DemoWorkspace!2026",
        }),
      });
      setCsrf(data.csrf);
      await loadMe();
      router.push("/dashboard");
    });
  const logout = () =>
    action(async () => {
      await api("/auth/logout", { method: "POST" });
      setMe(null);
      setOrg(null);
      setCsrf("");
      setMessages([]);
      router.push("/");
    });
  const upload = async (files: FileList | File[]) => {
    if (!files.length) return;
    await action(async () => {
      for (const file of Array.from(files)) {
        if (activeBase.current !== base) return;
        const data = new FormData();
        data.append("file", file);
        if (uploadWorkspace) data.append("workspace_id", uploadWorkspace);
        data.append("visibility", visibility);
        await api(base + "/documents", { method: "POST", body: data });
      }
      if (activeBase.current !== base) return;
      setModal("");
      await refresh();
      if (activeBase.current !== base) return;
      notify("Documents uploaded. Ingestion has started.");
      router.push("/documents");
    });
  };
  const ask = async (text = question) => {
    if (!text.trim() || busy) return;
    await action(async () => {
      const data = await api<{
        conversation_id: string;
        content: string;
        citations: Source[];
      }>(base + "/chat", {
        method: "POST",
        body: JSON.stringify({ question: text, conversation_id: conversation }),
      });
      if (activeBase.current !== base) return;
      setMessages((old) => [
        ...old,
        { role: "user", content: text, citations: [] },
        { role: "assistant", content: data.content, citations: data.citations },
      ]);
      setConversation(data.conversation_id);
      setQuestion("");
      await refresh();
    });
  };
  const openConversation = async (c: Conv) =>
    action(async () => {
      const data = await api<Msg[]>(base + "/conversations/" + c.id);
      if (activeBase.current !== base) return;
      setMessages(data);
      setConversation(c.id);
      router.push("/chat");
    });
  const openDoc = (doc: Doc) =>
    action(async () => {
      const detail = await api<Doc>(base + "/documents/" + doc.id);
      if (activeBase.current !== base) return;
      setSelected(detail);
      setModal("document");
    });
  const search = async (e: React.FormEvent) => {
    e.preventDefault();
    await action(async () => {
      const data = await api<Source[]>(
        base + "/search?q=" + encodeURIComponent(query),
      );
      if (activeBase.current === base) setResults(data);
    });
  };
  const newChat = () => {
    setConversation(null);
    setMessages([]);
    setQuestion("");
    router.push("/chat");
  };
  const exportActivity = () => {
    const blob = new Blob([JSON.stringify(audits, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "knowledgeforge-audit.json";
    a.click();
    URL.revokeObjectURL(url);
  };
  const uploadButton = (
    <button className="btn primary" onClick={() => setModal("upload")}>
      <Plus size={16} />
      Upload documents
    </button>
  );
  const filteredDocs = docs.filter(
    (d) =>
      (filter === "all" || d.status === filter) &&
      (!workspaceFilter || d.workspace_id === workspaceFilter) &&
      d.name.toLowerCase().includes(docQuery.toLowerCase()),
  );
  const title =
    [...nav, ...adminNav].find((n) => n.path === view)?.label ||
    (
      {
        profile: "Your profile",
        collections: "Knowledge collections",
        onboarding: "Create an organization",
      } as Record<string, string>
    )[view] ||
    "Not found";

  const screenContracts = {
    public: {
      error,
      setError,
      view,
      action,
      notify,
      router,
      busy,
      me: me,
      loadMe,
      memberEmail,
      setMemberEmail,
      handleSubmit,
      signIn,
      register,
      errors,
      demo,
      notice,
    },
    dashboard: {
      me: me!,
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
    },
    documents: {
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
    },
    chat: {
      stats,
      newChat,
      messages,
      busy,
      org,
      ask,
      me: me!,
      setSource,
      chatEnd,
      question,
      setQuestion,
    },
    search: {
      title,
      description,
      search,
      query,
      setQuery,
      busy,
      stats,
      results,
      setSource,
    },
    conversations: {
      title,
      description,
      action,
      newChat,
      convs,
      openConversation,
      setConfirm,
      base,
      conversation,
      refresh,
    },
    analytics: { title, description, action, refresh, stats },
    members: {
      title,
      description,
      action,
      org,
      setModal,
      members,
      base,
      setMembers: setCurrentMembers,
      notify,
      setConfirm,
    },
    audit: { title, description, action, exportActivity, audits },
  };
  return {
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
    setMembers: setCurrentMembers,
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
    screenContracts,
  };
}
export type ForgeController = ReturnType<typeof useForgeController>;
export type ScreenContracts = ForgeController["screenContracts"];
