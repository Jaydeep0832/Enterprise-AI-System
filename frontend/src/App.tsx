import { useState, useEffect } from "react";
import api from "./services/api";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import type { Message } from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import { Sparkles } from "lucide-react";

function App() {
  const [sessions, setSessions] = useState<string[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  // Load sessions from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("enterprise_ai_sessions");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessions(parsed);
        if (parsed.length > 0) {
          handleSelectSession(parsed[0]);
        }
      } catch (e) {
        console.error("Failed to parse sessions", e);
      }
    }
  }, []);

  // Save sessions to localStorage when it changes
  useEffect(() => {
    localStorage.setItem("enterprise_ai_sessions", JSON.stringify(sessions));
  }, [sessions]);

  const handleSelectSession = async (id: string) => {
    setCurrentSessionId(id);
    setLoading(true);
    try {
      const res = await api.get(`/history/${id}`);
      setMessages(res.data.messages || []);
    } catch (e) {
      console.error(e);
      setMessages([]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    setCurrentSessionId(null);
    setMessages([]);
  };

  const sendMessage = async (question: string) => {
    const userMsg: Message = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await api.post("/chat", {
        question,
        session_id: currentSessionId,
      });

      const assistantMsg: Message = { 
        role: "assistant", 
        content: response.data.answer,
        sources: response.data.sources || []
      };
      
      setMessages((prev) => [...prev, assistantMsg]);

      if (response.data.session_id && response.data.session_id !== currentSessionId) {
        const newId = response.data.session_id;
        setCurrentSessionId(newId);
        setSessions((prev) => {
          if (!prev.includes(newId)) {
            return [newId, ...prev];
          }
          return prev;
        });
      }
    } catch (error: any) {
      console.error(error);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error contacting backend" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-200 overflow-hidden font-sans">
      <Sidebar 
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        sessions={sessions}
      />
      
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 flex items-center px-6 justify-between shrink-0 glass-panel z-10">
          <div className="flex items-center gap-2 text-emerald-400">
            <Sparkles size={20} />
            <h1 className="font-semibold tracking-wide">Enterprise AI</h1>
          </div>
          <div className="text-xs font-medium bg-slate-800 px-3 py-1 rounded-full text-slate-400">
            {currentSessionId ? `Session: ${currentSessionId.split("-")[0]}` : 'New Conversation'}
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden relative flex flex-col p-6">
          <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 to-slate-900 pointer-events-none -z-10" />
          
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center opacity-50">
              <Sparkles size={48} className="mb-4 text-slate-600" />
              <h2 className="text-xl font-medium text-slate-400">How can I assist you today?</h2>
              <p className="text-slate-500 mt-2 max-w-md text-center text-sm">Upload documents in the sidebar or ask a question to begin a new conversation.</p>
            </div>
          ) : (
            <ChatWindow messages={messages} loading={loading} />
          )}

          <div className="shrink-0 max-w-4xl mx-auto w-full pt-4">
            <ChatInput onSendMessage={sendMessage} loading={loading} />
            <div className="text-center mt-2 text-[10px] text-slate-500">
              AI can make mistakes. Consider verifying critical information.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
