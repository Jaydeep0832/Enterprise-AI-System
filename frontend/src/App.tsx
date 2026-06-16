import { useState, useEffect } from "react";
import { BrowserRouter, Routes, Route, useNavigate, useLocation } from "react-router-dom";
import api, { getUser, logout } from "./services/api";
import Sidebar from "./components/Sidebar";
import ChatWindow from "./components/ChatWindow";
import type { Message } from "./components/ChatWindow";
import ChatInput from "./components/ChatInput";
import DashboardPage from "./components/DashboardPage";
import KnowledgeGraphPage from "./components/KnowledgeGraphPage";
import EvaluationPage from "./components/EvaluationPage";
import AuthPage from "./components/AuthPage";
import { Sparkles, LogOut, User } from "lucide-react";

function AppContent() {
  const [sessions, setSessions] = useState<string[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [username, setUsername] = useState<string | null>(getUser());
  const location = useLocation();
  const navigate = useNavigate();

  const isChatPage = location.pathname === "/" || location.pathname === "/chat";
  const isDashboard = location.pathname === "/dashboard";
  const isKG = location.pathname === "/knowledge-graph";
  const isEval = location.pathname === "/evaluation";

  // Load sessions from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("enterprise_ai_sessions");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        setSessions(parsed);
        if (parsed.length > 0 && isChatPage) {
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
    if (!isChatPage) navigate("/");
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
        sources: response.data.sources || [],
        route: response.data.route || "",
        execution_trace: response.data.execution_trace || [],
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

  const handleLogin = (user: string) => {
    setUsername(user);
  };

  const handleLogout = () => {
    logout();
    setUsername(null);
  };

  return (
    <div className="flex h-screen bg-slate-900 text-slate-200 overflow-hidden font-sans">
      <Sidebar 
        currentSessionId={currentSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        sessions={sessions}
        currentPage={location.pathname}
        onNavigate={(path) => navigate(path)}
      />
      
      <div className="flex-1 flex flex-col relative">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 flex items-center px-6 justify-between shrink-0 glass-panel z-10">
          <div className="flex items-center gap-2 text-emerald-400">
            <Sparkles size={20} />
            <h1 className="font-semibold tracking-wide">Enterprise AI</h1>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-xs font-medium bg-slate-800 px-3 py-1 rounded-full text-slate-400">
              {isDashboard ? "Dashboard" :
               isKG ? "Knowledge Graph" :
               isEval ? "Evaluation" :
               currentSessionId ? `Session: ${currentSessionId.split("-")[0]}` : 'New Conversation'}
            </div>
            {username ? (
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <User size={12} />
                  {username}
                </span>
                <button
                  onClick={handleLogout}
                  className="text-slate-500 hover:text-red-400 transition-colors"
                  title="Logout"
                >
                  <LogOut size={14} />
                </button>
              </div>
            ) : (
              <button
                onClick={() => navigate("/auth")}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Page Content */}
        <Routes>
          <Route path="/auth" element={<AuthPage onLogin={handleLogin} />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/knowledge-graph" element={<KnowledgeGraphPage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
          <Route path="*" element={
            <div className="flex-1 overflow-hidden relative flex flex-col p-6">
              <div className="absolute inset-0 bg-gradient-to-b from-slate-900/50 to-slate-900 pointer-events-none -z-10" />
              
              {messages.length === 0 ? (
                <div className="flex-1 flex flex-col items-center justify-center opacity-50">
                  <Sparkles size={48} className="mb-4 text-slate-600" />
                  <h2 className="text-xl font-medium text-slate-400">How can I assist you today?</h2>
                  <p className="text-slate-500 mt-2 max-w-md text-center text-sm">Upload documents in the sidebar or ask a question to begin a new conversation.</p>
                </div>
              ) : (
                <ChatWindow messages={messages} loading={loading} sessionId={currentSessionId} />
              )}

              <div className="shrink-0 max-w-4xl mx-auto w-full pt-4">
                <ChatInput onSendMessage={sendMessage} loading={loading} />
                <div className="text-center mt-2 text-[10px] text-slate-500">
                  AI can make mistakes. Consider verifying critical information.
                </div>
              </div>
            </div>
          } />
        </Routes>
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
