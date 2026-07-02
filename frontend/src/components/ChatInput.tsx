import { useState } from "react";
import type { KeyboardEvent } from "react";
import { SendHorizontal, Square } from "lucide-react";

type ChatInputProps = {
  onSendMessage: (msg: string) => void;
  loading: boolean;
  onCancel?: () => void;
};

export default function ChatInput({ onSendMessage, loading, onCancel }: ChatInputProps) {
  const [question, setQuestion] = useState("");

  const handleSend = () => {
    if (!question.trim() || loading) return;
    onSendMessage(question);
    setQuestion("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-2 flex gap-2 items-end glowing-border mt-4 w-full">
      <textarea
        className="w-full bg-transparent text-white placeholder-gray-400 p-3 resize-none outline-none max-h-32 min-h-[50px] leading-relaxed"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Message the Enterprise AI..."
        onKeyDown={handleKeyDown}
        disabled={loading}
        rows={1}
      />
      {loading ? (
        <button
          className="p-3 bg-red-500/20 hover:bg-red-500/40 text-red-400 rounded-xl transition-all duration-200 mb-1 mr-1 group"
          onClick={onCancel}
          title="Stop generating"
        >
          <Square size={18} className="group-hover:scale-110 transition-transform" />
        </button>
      ) : (
        <button
          className="p-3 bg-blue-500/20 hover:bg-blue-500/40 text-blue-400 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed mb-1 mr-1"
          onClick={handleSend}
          disabled={!question.trim()}
        >
          <SendHorizontal size={20} />
        </button>
      )}
    </div>
  );
}
