"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { api } from "@/lib/api";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  CheckCircle2,
  Database,
  FileText,
  Layers,
  LoaderCircle,
  Lock,
  Mail,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import Link from "next/link";
import { Logo } from "../shared/ui";
const authViews = [
  "login",
  "register",
  "forgot-password",
  "reset-password",
  "verify-email",
];
export default function PublicScreen({
  error,
  setError,
  view,
  action,
  notify,
  router,
  busy,
  me,
  loadMe,
  memberEmail,
  setMemberEmail,
  handleSubmit,
  signIn,
  register,
  errors,
  demo,
  notice,
}: ScreenContracts["public"]) {
  return (
    <div className="public-shell">
      <header className="public-header">
        <Link href="/" aria-label="Home">
          <Logo />
        </Link>
        <nav>
          <a href="#capabilities">Platform</a>
          <a href="#trust">Built for trust</a>
          <Link href="/login">Sign in</Link>
          <Link className="btn primary" href="/register">
            Get started <ArrowUpRight size={15} />
          </Link>
        </nav>
      </header>
      {error && (
        <div className="public-error" role="alert">
          {error}
          <button onClick={() => setError("")} aria-label="Dismiss error">
            <X size={16} />
          </button>
        </div>
      )}
      {authViews.includes(view) ? (
        <div className="auth-layout">
          <div className="auth-story">
            <span className="eyebrow">
              <span className="live-dot" /> A LITTLE LESS SEARCHING. A LOT MORE
              KNOWING.
            </span>
            <h1>
              Your team’s knowledge.
              <br />
              <em>Finally connected.</em>
            </h1>
            <p>
              Turn scattered documents into clear answers, grounded in sources
              you can actually verify.
            </p>
            <div className="quote-card">
              <span className="logo">
                <ShieldCheck />
              </span>
              <h3>Private by design. Grounded by default.</h3>
              <p>
                Organization-scoped access, verifiable citations, and an
                assistant that knows when it doesn’t know.
              </p>
            </div>
          </div>
          <section className="auth-card">
            <span className="tag">YOUR KNOWLEDGE STARTS HERE</span>
            <h2>
              {view === "register"
                ? "Create your workspace"
                : ["forgot-password", "reset-password"].includes(view)
                  ? "Reset your password"
                  : view === "verify-email"
                    ? "Verify your email"
                    : "Welcome back"}
            </h2>
            <p className="muted">
              {view === "register"
                ? "A clearer picture is just a few details away."
                : "Sign in to pick up where you left off."}
            </p>
            {view === "reset-password" ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  const password = String(
                    new FormData(e.currentTarget).get("password"),
                  );
                  action(async () => {
                    const token = new URLSearchParams(
                      window.location.search,
                    ).get("token");
                    await api("/auth/reset-password", {
                      method: "POST",
                      body: JSON.stringify({ token, password }),
                    });
                    notify("Password reset. Please sign in.");
                    router.push("/login");
                  });
                }}
              >
                <label>
                  New password
                  <input
                    name="password"
                    type="password"
                    required
                    minLength={12}
                    maxLength={128}
                    placeholder="At least 12 characters"
                  />
                </label>
                <button className="btn primary wide" disabled={busy}>
                  Reset password
                </button>
              </form>
            ) : view === "verify-email" ? (
              <>
                <p className="muted">
                  Confirm the email address associated with your account.
                </p>
                <button
                  className="btn primary wide"
                  disabled={busy}
                  onClick={() =>
                    action(async () => {
                      const token = new URLSearchParams(
                        window.location.search,
                      ).get("token");
                      await api("/auth/verify", {
                        method: "POST",
                        body: JSON.stringify({ token }),
                      });
                      notify("Email verified");
                      if (me) await loadMe();
                      router.push("/login");
                    })
                  }
                >
                  Verify email address <Mail size={16} />
                </button>
              </>
            ) : view === "forgot-password" ? (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  action(async () => {
                    const result = await api<{ message: string }>(
                      "/auth/forgot-password",
                      {
                        method: "POST",
                        body: JSON.stringify({ email: memberEmail }),
                      },
                    );
                    notify(result.message);
                  });
                }}
              >
                <label>
                  Email address
                  <input
                    required
                    type="email"
                    value={memberEmail}
                    onChange={(e) => setMemberEmail(e.target.value)}
                  />
                </label>
                <button className="btn primary wide" disabled={busy}>
                  Send reset link
                </button>
                <Link href="/login" className="small-link">
                  Back to sign in
                </Link>
              </form>
            ) : (
              <form onSubmit={handleSubmit(signIn)}>
                {view === "register" && (
                  <>
                    <label>
                      Full name
                      <input
                        {...register("name")}
                        required
                        placeholder="Alex Morgan"
                      />
                    </label>
                    <label>
                      Organization
                      <input
                        {...register("organization")}
                        required
                        placeholder="Acme, Inc."
                      />
                    </label>
                  </>
                )}
                <label>
                  Work email
                  <input
                    {...register("email")}
                    type="email"
                    placeholder="you@company.com"
                  />
                  {errors.email && (
                    <small className="error-text">{errors.email.message}</small>
                  )}
                </label>
                <label>
                  Password
                  <input
                    {...register("password")}
                    type="password"
                    placeholder="At least 12 characters"
                  />
                  {errors.password && (
                    <small className="error-text">
                      {errors.password.message}
                    </small>
                  )}
                </label>
                {view === "login" && (
                  <Link className="small-link" href="/forgot-password">
                    Forgot your password?
                  </Link>
                )}
                <button className="btn primary wide" disabled={busy}>
                  {busy ? <LoaderCircle className="spin" size={16} /> : null}
                  {view === "register" ? "Create account" : "Sign in"}
                  <ArrowRight size={16} />
                </button>
                <p className="auth-switch">
                  {view === "register"
                    ? "Already have an account?"
                    : "New to KnowledgeForge?"}{" "}
                  <Link href={view === "register" ? "/login" : "/register"}>
                    {view === "register" ? "Sign in" : "Create an account"}
                  </Link>
                </p>
              </form>
            )}
            <div className="auth-divider">OR EXPLORE FIRST</div>
            <button className="btn wide" onClick={demo} disabled={busy}>
              Open seeded demo workspace <ArrowUpRight size={15} />
            </button>
            <p className="fineprint">
              Demo content is synthetic. Please don’t upload sensitive
              information to the shared demo account.
            </p>
          </section>
        </div>
      ) : (
        <main className="landing">
          <div className="hero" id="capabilities">
            <div className="eyebrow">
              <span className="live-dot" /> THE INTELLIGENCE BEHIND YOUR TEAM
            </div>
            <h1>
              Less searching.
              <br />
              More <span className="serif">knowing.</span>
            </h1>
            <p>
              Your knowledge is everywhere. Your answers shouldn’t be.
              <br />
              Connect your documents. Ask better questions. Move forward with
              confidence.
            </p>
            <div className="hero-actions">
              <button
                className="btn primary large"
                onClick={demo}
                disabled={busy}
              >
                {busy ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Sparkles size={17} />
                )}
                Explore demo workspace
                <ArrowRight size={17} />
              </button>
              <Link className="btn large" href="/register">
                Create your workspace
              </Link>
            </div>
            <span className="fineprint">
              Real document retrieval. Verifiable sources. No fabricated
              answers.
            </span>
          </div>
          <div className="landing-preview">
            <div className="preview-top">
              <Logo />
              <span className="status ready">
                <span className="live-dot" />
                Knowledge, connected
              </span>
            </div>
            <div className="preview-content">
              <div>
                <span className="eyebrow">
                  ONE HOME FOR WHAT YOUR TEAM KNOWS
                </span>
                <h2>
                  From scattered files
                  <br />
                  to shared understanding.
                </h2>
                <p className="muted">
                  Search across knowledge. Surface the right context.
                  <br />
                  Keep every answer connected to its source.
                </p>
                <div className="preview-features">
                  <span>
                    <CheckCircle2 size={16} />
                    PDF, Word, Markdown & text
                  </span>
                  <span>
                    <CheckCircle2 size={16} />
                    Permission-aware retrieval
                  </span>
                  <span>
                    <CheckCircle2 size={16} />
                    Sources you can inspect
                  </span>
                </div>
              </div>
              <div className="knowledge-orbit">
                <div className="orbit-line" />
                <span className="orbit-file one">
                  <FileText />
                  Company handbook.pdf
                </span>
                <span className="orbit-file two">
                  <FileText />
                  Engineering playbook.md
                </span>
                <div className="orbit-core">
                  <Layers size={37} />
                </div>
                <span className="orbit-file three">
                  <FileText />
                  Product strategy.docx
                </span>
                <span className="orbit-label">
                  <Sparkles size={14} />
                  Clarity, from your content
                </span>
              </div>
            </div>
          </div>
          <div className="trust-strip" id="trust">
            <span>
              <Lock size={18} />
              Tenant-isolated workspaces
            </span>
            <span>
              <BookOpen size={18} />
              Source-grounded answers
            </span>
            <span>
              <ShieldCheck size={18} />
              Server-enforced permissions
            </span>
            <span>
              <Database size={18} />
              Your documents, your context
            </span>
          </div>
          <footer>
            KNOWLEDGEFORGE AI{" "}
            <span>A thoughtful home for organizational knowledge.</span>
            <Link href="/login">
              Enter your workspace <ArrowUpRight size={14} />
            </Link>
          </footer>
        </main>
      )}
      {notice && (
        <div className="toast" role="status">
          <CheckCircle2 size={17} />
          {notice}
        </div>
      )}
    </div>
  );
}
