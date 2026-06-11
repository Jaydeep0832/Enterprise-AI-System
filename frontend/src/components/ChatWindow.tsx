import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Bot, User, FileText } from "lucide-react";

export type Message = {
  role: "user" | "assistant" | "system";
  content: string;
  sources?: any[];
};

type ChatWindowProps = {
  messages: Message[];
  loading: boolean;
};

export default function ChatWindow({ messages, loading }: ChatWindowProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  return (
    <div className="flex-1 overflow-y-auto pr-4 space-y-6">
      <AnimatePresence>
        {messages.filter(m => m.role !== 'system').map((message, index) => (
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

              {message.sources && message.sources.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-1">
                  {message.sources.map((src, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs bg-slate-800 border border-slate-700 text-gray-400 px-2.5 py-1 rounded-full cursor-help hover:text-gray-200 hover:border-slate-500 transition-colors" title={src.content}>
                      <FileText size={12} />
                      <span className="truncate max-w-[150px]">{src.filename}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        ))}
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
