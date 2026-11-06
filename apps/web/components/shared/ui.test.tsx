import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Modal } from "./ui";
afterEach(cleanup);
describe("focus-managed dialogs", () => {
  it("keeps focus while typing across parent renders", () => {
    const { rerender } = render(
      <Modal title="Edit" close={() => {}}>
        <label>
          Name
          <input defaultValue="" />
        </label>
      </Modal>,
    );
    const input = screen.getByRole("textbox");
    input.focus();
    fireEvent.change(input, { target: { value: "Alex" } });
    rerender(
      <Modal title="Edit" close={() => {}}>
        <label>
          Name
          <input defaultValue="" />
        </label>
      </Modal>,
    );
    expect(document.activeElement).toBe(input);
  });
  it("only sends Escape to the topmost dialog", () => {
    const lower = vi.fn(),
      upper = vi.fn();
    render(
      <>
        <Modal title="Document" close={lower}>
          <button>Delete</button>
        </Modal>
        <Modal title="Confirm" close={upper}>
          <button>Confirm</button>
        </Modal>
      </>,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(upper).toHaveBeenCalledOnce();
    expect(lower).not.toHaveBeenCalled();
  });
});
