import { useState, useEffect } from "react";
import {
  UploadCloud, MessageSquare, Plus, File, Trash2,
  BarChart3, Network, Home, FlaskConical,
} from "lucide-react";
import api from "../services/api";

type Document = {
  filename: string;
  chunk_count: number;
};

type SidebarProps = {
  currentSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: () => void;
  sessions: string[];
  currentPage: string;
  onNavigate: (path: string) => void;
};

export default function Sidebar({
  currentSessionId, onSelectSession, onNewSession, sessions,
  currentPage, onNavigate,
}: SidebarProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);

  const fetchDocs = async () => {
    try {
      const res = await api.get("/documents");
      setDocuments(res.data.documents || []);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploading(true);

    try {
      await api.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      fetchDocs();
    } catch (err) {
      console.error(err);
      alert("Upload failed");
    } finally {
      setUploading(false);
      if (e.target) e.target.value = "";
    }
  };

  const handleDelete = async (filename: string) => {
    try {
      await api.delete(`/documents/${filename}`);
      fetchDocs();
    } catch (err) {
      console.error(err);
    }
  };

  const navItems = [
    { path: "/", icon: <Home size={16} />, label: "Chat" },
    { path: "/dashboard", icon: <BarChart3 size={16} />, label: "Dashboard" },
    { path: "/evaluation", icon: <FlaskConical size={16} />, label: "Evaluation" },
    { path: "/knowledge-graph", icon: <Network size={16} />, label: "Knowledge Graph" },
  ];

  return (
    <div className="w-72 bg-slate-900 border-r border-slate-800 flex flex-col h-full text-slate-300">
      <div className="p-4">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white p-3 rounded-xl transition-colors font-medium shadow-lg shadow-blue-900/20"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      {/* Navigation */}
      <div className="px-3 mb-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-1">
          Navigation
        </h3>
        <div className="space-y-0.5">
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => onNavigate(item.path)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left transition-all ${
                currentPage === item.path
                  ? "bg-blue-600/15 text-blue-400 border border-blue-500/20"
                  : "hover:bg-slate-800/50 hover:text-slate-200 text-slate-400"
              }`}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar p-3 space-y-6">
        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-1">
            Recent Chats
          </h3>
          <div className="space-y-1">
            {sessions.length === 0 && (
              <p className="text-sm text-slate-600 px-1 italic">No recent chats</p>
            )}
            {sessions.map((id) => (
              <button
                key={id}
                onClick={() => onSelectSession(id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-left transition-colors ${
                  currentSessionId === id
                    ? "bg-slate-800 text-blue-400"
                    : "hover:bg-slate-800/50 hover:text-slate-200"
                }`}
              >
                <MessageSquare size={16} />
                <span className="truncate">{id.split("-")[0]}...</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3 px-1 flex justify-between items-center">
            Knowledge Base
            <label className="cursor-pointer text-blue-400 hover:text-blue-300">
              <UploadCloud size={16} />
              <input type="file" className="hidden" accept=".pdf,.txt,.md,.docx" onChange={handleUpload} disabled={uploading} />
            </label>
          </h3>
          
          {uploading && <div className="text-xs text-blue-400 mb-2 px-1 animate-pulse">Uploading document...</div>}
          
          <div className="space-y-1">
            {documents.length === 0 && !uploading && (
              <p className="text-sm text-slate-600 px-1 italic">No documents uploaded</p>
            )}
            {documents.map((doc) => (
              <div key={doc.filename} className="group flex items-center justify-between px-3 py-2 rounded-lg text-sm bg-slate-800/30 border border-slate-700/50">
                <div className="flex items-center gap-2 overflow-hidden">
                  <File size={14} className="text-slate-400 flex-shrink-0" />
                  <span className="truncate" title={doc.filename}>{doc.filename}</span>
                </div>
                <button onClick={() => handleDelete(doc.filename)} className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 transition-opacity">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
