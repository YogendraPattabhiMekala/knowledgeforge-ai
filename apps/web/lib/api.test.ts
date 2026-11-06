import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { bytes, api, setCsrf } from "./api";
afterEach(() => {
  vi.unstubAllGlobals();
  setCsrf("");
});
describe("client contract", () => {
  it("formats storage without fake precision", () => {
    expect(bytes(100)).toBe("100 B");
    expect(bytes(1024)).toBe("1.0 KB");
    expect(bytes(1048576)).toBe("1.0 MB");
  });
  it("sends CSRF on same-origin requests", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ ok: true }) });
    vi.stubGlobal("fetch", fetch);
    setCsrf("token");
    await api("/test", { method: "POST", body: "{}" });
    expect(fetch.mock.calls[0][1].headers["X-CSRF-Token"]).toBe("token");
    expect(fetch.mock.calls[0][0]).toBe("/api/test");
  });
  it("surfaces API error details", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ detail: "Not permitted" }),
      }),
    );
    await expect(api("/test")).rejects.toThrow("Not permitted");
  });
  it("does not set a multipart content type boundary", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetch);
    await api("/test", { method: "POST", body: new FormData() });
    expect(fetch.mock.calls[0][1].headers["Content-Type"]).toBeUndefined();
  });
  it("renders accessible API error content", () => {
    render(
      React.createElement("div", { role: "alert" }, "Provider unavailable"),
    );
    expect(screen.getByRole("alert").textContent).toBe("Provider unavailable");
  });
});
