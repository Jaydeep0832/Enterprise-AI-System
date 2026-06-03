import { useEffect, useState } from "react";
import api from "./services/api";

type Message = {
  role: "user" | "assistant";
  content: string;
};

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const response = await api.get("/history");

        setMessages(
          response.data.messages || []
        );
      } catch (error) {
        console.log(
          "History load failed",
          error
        );
      }
    };

    loadHistory();
  }, []);

  const sendMessage = async () => {
    if (!query.trim()) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: query,
      },
    ]);

    setLoading(true);

    try {
      const response = await api.post(
        "/chat",
        {
          query,
        }
      );

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: response.data.answer,
        },
      ]);

      setQuery("");
    } catch (error: any) {
      console.log(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error?.message ||
            "Error contacting backend",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">

        <h1 className="text-3xl font-bold mb-6 text-center">
          Enterprise AI Assistant
        </h1>

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
            <div className="flex justify-start">
              <div className="bg-gray-200 p-3 rounded-lg">
                AI is thinking...
              </div>
            </div>
          )}

        </div>

        <div className="flex gap-2">

          <input
            className="border rounded-lg p-3 flex-1"
            value={query}
            onChange={(e) =>
              setQuery(e.target.value)
            }
            placeholder="Ask something..."
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                sendMessage();
              }
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

