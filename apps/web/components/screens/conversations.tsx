"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import { api, date } from "@/lib/api";
import {
  ArrowRight,
  ArrowUpRight,
  MessageSquare,
  Plus,
  Trash2,
} from "lucide-react";
import { Empty, PageHeading } from "../shared/ui";
export default function ConversationsScreen({
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
}: ScreenContracts["conversations"]) {
  return (
    <>
      <PageHeading
        eyebrow="KEEP THE CONTEXT"
        title="Your conversations"
        description="Pick up a thought right where you left it."
        action={
          <button className="btn primary" onClick={newChat}>
            <Plus size={16} />
            New conversation
          </button>
        }
      />
      <section className="panel conversation-list">
        {convs.map((c) => (
          <div className="conversation-row" key={c.id}>
            <span className="conversation-icon">
              <MessageSquare size={18} />
            </span>
            <button onClick={() => openConversation(c)}>
              <strong>{c.title}</strong>
              <small>{date(c.created_at)}</small>
            </button>
            <button
              className="icon-btn"
              aria-label={"Delete conversation " + c.title}
              onClick={() =>
                setConfirm({
                  label: "Permanently delete this conversation?",
                  run: async () => {
                    await api(base + "/conversations/" + c.id, {
                      method: "DELETE",
                    });
                    if (conversation === c.id) newChat();
                    await refresh();
                  },
                })
              }
            >
              <Trash2 size={16} />
            </button>
            <button
              className="icon-btn"
              aria-label="Open conversation"
              onClick={() => openConversation(c)}
            >
              <ArrowUpRight size={16} />
            </button>
          </div>
        ))}
        {!convs.length && (
          <Empty
            icon={MessageSquare}
            title="The beginning of a good conversation"
            description="Ask your first question. Your conversations will be saved here."
            action={
              <button className="btn primary" onClick={newChat}>
                Start a conversation <ArrowRight size={15} />
              </button>
            }
          />
        )}
      </section>
    </>
  );
}
