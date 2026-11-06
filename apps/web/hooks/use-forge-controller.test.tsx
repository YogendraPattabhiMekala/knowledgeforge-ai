// @vitest-environment jsdom
import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api } from "@/lib/api";
import type { Org } from "@/lib/types";
import useForgeController from "./use-forge-controller";

const navigation = vi.hoisted(() => ({ push: vi.fn() }));
vi.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
  useRouter: () => navigation,
}));
vi.mock("@/lib/api", () => ({ api: vi.fn(), setCsrf: vi.fn() }));
const first: Org = { id: "first", name: "First", role: "owner" };
const second: Org = { id: "second", name: "Second", role: "owner" };
let delayedPath = "";
let finish: (value: unknown) => void;

beforeEach(() => {
  vi.clearAllMocks();
  delayedPath = "";
  vi.mocked(api).mockImplementation((async (path: string) => {
    if (path === delayedPath)
      return new Promise<unknown>((resolve) => {
        finish = resolve;
      });
    if (path === "/auth/me")
      return {
        user: {
          id: "user",
          name: "Synthetic User",
          email: "synthetic@example.test",
          verified: false,
        },
        csrf: "synthetic",
        organizations: [first, second],
      };
    if (path.endsWith("/analytics")) return { documents: 0 };
    return [];
  }) as typeof api);
});
afterEach(cleanup);

test("late chat response cannot enter the newly selected organization", async () => {
  const { result } = renderHook(useForgeController);
  await waitFor(() => expect(result.current.org?.id).toBe(first.id));
  delayedPath = "/organizations/first/chat";
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.ask("Synthetic question");
  });
  await waitFor(() => expect(result.current.busy).toBe(true));
  act(() => result.current.setOrg(second));
  await act(async () => {
    finish({
      conversation_id: "old-conversation",
      content: "Old organization content",
      citations: [],
    });
    await pending;
  });
  expect(result.current.messages).toEqual([]);
  expect(result.current.conversation).toBeNull();
});

test("late document response cannot reopen a dialog after switching organization", async () => {
  const { result } = renderHook(useForgeController);
  await waitFor(() => expect(result.current.org?.id).toBe(first.id));
  delayedPath = "/organizations/first/documents/doc-first";
  let pending!: Promise<void>;
  act(() => {
    pending = result.current.openDoc({ id: "doc-first" } as Parameters<
      typeof result.current.openDoc
    >[0]);
  });
  await waitFor(() => expect(result.current.busy).toBe(true));
  act(() => result.current.setOrg(second));
  await act(async () => {
    finish({ id: "doc-first", name: "Old organization document" });
    await pending;
  });
  expect(result.current.selected).toBeNull();
  expect(result.current.modal).toBe("");
});

test("organization switch clears stale confirmation and upload workspace", async () => {
  const { result } = renderHook(useForgeController);
  await waitFor(() => expect(result.current.org?.id).toBe(first.id));
  act(() => {
    result.current.setUploadWorkspace("old-workspace");
    result.current.setConfirm({
      label: "Delete old document",
      run: async () => {},
    });
  });
  act(() => result.current.setOrg(second));
  expect(result.current.uploadWorkspace).toBe("");
  expect(result.current.confirm).toBeNull();
});
