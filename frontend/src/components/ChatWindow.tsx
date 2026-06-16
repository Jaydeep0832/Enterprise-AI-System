import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, User, FileText, ThumbsUp, ThumbsDown, MessageSquare, X } from "lucide-react";
import api from "../services/api";

export type Message = {
  role: "user" | "assistant" | "system";
  content: string;
  sources?: any[];
  route?: string;
  execution_trace?: any[];
};

type ChatWindowProps = {
  messages: Message[];
  loading: boolean;
  sessionId: string | null;
};

export default function ChatWindow({ messages, loading, sessionId }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const [feedbackGiven, setFeedbackGiven] = useState<Record<number, number>>({});
  const [showCommentFor, setShowCommentFor] = useState<number | null>(null);
  const [comment, setComment] = useState("");

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const submitFeedback = async (messageIndex: number, rating: number, feedbackComment?: string) => {
    if (!sessionId) return;

    try {
      await api.post("/feedback", {
        session_id: sessionId,
        message_index: messageIndex,
        rating,
        comment: feedbackComment || null,
      });
      setFeedbackGiven(prev => ({ ...prev, [messageIndex]: rating }));
      setShowCommentFor(null);
      setComment("");
    } catch (err) {
      console.error("Feedback error:", err);
    }
  };

  const handleThumbsDown = (index: number) => {
    setShowCommentFor(index);
  };

  // Count assistant messages for proper indexing
  let assistantIndex = -1;

  return (
    <div className="flex-1 overflow-y-auto pr-4 space-y-6">
      <AnimatePresence>
        {messages.filter(m => m.role !== 'system').map((message, index) => {
          if (message.role === "assistant") assistantIndex++;
          const currentAssistantIndex = assistantIndex;

          return (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-4 max-w-[85%] ${
                message.role === "user" ? "ml-auto flex-row-reverse" : "mr-auto"
              }`}
            >
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                message.role === "user" ? "bg-blue-600 text-white" : "bg-slate-700 text-emerald-400"
              }`}>
                {message.role === "user" ? <User size={16} /> : <Bot size={16} />}
              </div>
              
              <div className="flex flex-col gap-2">
                <div className={`p-4 rounded-2xl ${
                  message.role === "user" 
                    ? "bg-blue-600/20 border border-blue-500/30 text-white rounded-tr-sm" 
                    : "glass-panel rounded-tl-sm text-gray-200"
                }`}>
                  <div className="whitespace-pre-wrap leading-relaxed text-[15px]">
                    {message.content}
                  </div>
                </div>

                {/* Route badge */}
                {message.role === "assistant" && message.route && (
                  <div className="flex gap-2 items-center">
                    <span className="text-[10px] bg-slate-800/80 border border-slate-700/50 text-slate-500 px-2 py-0.5 rounded-full">
                      via {message.route}
                    </span>
                    {message.execution_trace && message.execution_trace.length > 0 && (
                      <span className="text-[10px] text-slate-600">
                        {message.execution_trace.reduce((sum: number, t: any) => sum + (t.duration_ms || 0), 0).toFixed(0)}ms total
                      </span>
                    )}
                  </div>
                )}

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-1">
                    {message.sources.map((src: any, i: number) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs bg-slate-800 border border-slate-700 text-gray-400 px-2.5 py-1 rounded-full cursor-help hover:text-gray-200 hover:border-slate-500 transition-colors" title={src.content}>
                        <FileText size={12} />
                        <span className="truncate max-w-[150px]">{src.filename}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Feedback buttons */}
                {message.role === "assistant" && (
                  <div className="flex items-center gap-1 mt-1">
                    {feedbackGiven[currentAssistantIndex] ? (
                      <span className="text-[10px] text-slate-500 flex items-center gap-1">
                        {feedbackGiven[currentAssistantIndex] === 1 ? (
                          <><ThumbsUp size={10} className="text-emerald-500" /> Thanks for the feedback!</>
                        ) : (
                          <><ThumbsDown size={10} className="text-red-400" /> Feedback recorded</>
                        )}
                      </span>
                    ) : (
                      <>
                        <button
                          onClick={() => submitFeedback(currentAssistantIndex, 1)}
                          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-600 hover:text-emerald-400 transition-colors"
                          title="Good response"
                        >
                          <ThumbsUp size={13} />
                        </button>
                        <button
                          onClick={() => handleThumbsDown(currentAssistantIndex)}
                          className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-600 hover:text-red-400 transition-colors"
                          title="Bad response"
                        >
                          <ThumbsDown size={13} />
                        </button>
                      </>
                    )}

                    {/* Comment modal for negative feedback */}
                    {showCommentFor === currentAssistantIndex && (
                      <div className="flex items-center gap-2 ml-2 bg-slate-800/80 border border-slate-700/50 rounded-xl px-3 py-1.5 animate-in">
                        <MessageSquare size={12} className="text-slate-500 flex-shrink-0" />
                        <input
                          type="text"
                          value={comment}
                          onChange={(e) => setComment(e.target.value)}
                          placeholder="What went wrong? (optional)"
                          className="bg-transparent text-xs text-white placeholder-slate-500 outline-none w-48"
                          autoFocus
                          onKeyDown={(e) => {
                            if (e.key === "Enter") submitFeedback(currentAssistantIndex, -1, comment);
                          }}
                        />
                        <button
                          onClick={() => submitFeedback(currentAssistantIndex, -1, comment)}
                          className="text-xs text-red-400 hover:text-red-300 font-medium"
                        >
                          Send
                        </button>
                        <button
                          onClick={() => { setShowCommentFor(null); setComment(""); }}
                          className="text-slate-600 hover:text-slate-400"
                        >
                          <X size={12} />
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </motion.div>
          );
        })}
        {loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-4 mr-auto max-w-[85%]"
          >
            <div className="w-8 h-8 rounded-full bg-slate-700 text-emerald-400 flex items-center justify-center">
              <Bot size={16} />
            </div>
            <div className="glass-panel p-4 rounded-2xl rounded-tl-sm flex items-center gap-2">
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" />
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s'}} />
              <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s'}} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
