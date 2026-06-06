import { useState } from "react";
import api from "./services/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState("");
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const uploadFile = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    setUploadStatus("Uploading...");

    try {
      const response = await api.post("/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setUploadStatus(
        `Uploaded: ${response.data.filename} (${response.data.chunks} chunks)`
      );
    } catch (error) {
      console.error(error);
      setUploadStatus("Upload failed");
    }
  };

  const sendMessage = async () => {
    if (!question.trim()) return;

    const userQuestion = question;
    setMessages((prev) => [...prev, { role: "user", content: userQuestion }]);
    setQuestion("");
    setLoading(true);

    try {
      const response = await api.post("/chat", {
        question: userQuestion,
        session_id: sessionId,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: response.data.answer },
      ]);

      // store the session id from backend so future messages stay in the same conversation
      if (response.data.session_id) {
        setSessionId(response.data.session_id);
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
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-6 text-center">
          Enterprise AI System
        </h1>

        {/* Upload Section */}
        <div className="bg-white p-4 rounded-lg border mb-6">
          <h2 className="text-xl font-semibold mb-3">Upload PDF</h2>
          <div className="flex gap-3">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
            />
            <button
              onClick={uploadFile}
              className="bg-green-600 text-white px-4 py-2 rounded"
            >
              Upload
            </button>
          </div>
          {uploadStatus && <p className="mt-3">{uploadStatus}</p>}
        </div>

        {/* Chat Window */}
        <div className="bg-white border rounded-lg p-4 h-[500px] overflow-y-auto mb-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "flex justify-end mb-3"
                  : "flex justify-start mb-3"
              }
            >
              <div
                className={
                  message.role === "user"
                    ? "bg-blue-500 text-white p-3 rounded-lg max-w-[70%]"
                    : "bg-gray-200 text-black p-3 rounded-lg max-w-[70%]"
                }
              >
                {message.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="bg-gray-200 p-3 rounded-lg">AI is thinking...</div>
          )}
        </div>

        {/* Chat Input */}
        <div className="flex gap-2">
          <input
            className="border rounded-lg p-3 flex-1"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask questions about uploaded documents..."
            onKeyDown={(e) => {
              if (e.key === "Enter") sendMessage();
            }}
          />
          <button
            className="bg-blue-500 text-white px-6 rounded-lg"
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
