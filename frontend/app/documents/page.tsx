"use client";

import { useState } from "react";
import { Upload, Send, FileText, MessageSquare } from "lucide-react";
import { toast } from "sonner";

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<Array<{ role: string; content: string }>>([]);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/documents/upload", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.status === "complete") {
        toast.success(`Indexed ${data.chunks} chunks from ${data.pages} pages`);
        setChat([...chat, { role: "system", content: data.message }]);
      } else {
        toast.error(data.message);
      }
    } catch {
      toast.error("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleAsk = async () => {
    if (!question.trim()) return;
    setLoading(true);
    setChat([...chat, { role: "user", content: question }]);

    const formData = new FormData();
    formData.append("question", question);

    try {
      const res = await fetch("http://localhost:8000/documents/query", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.status === "complete") {
        setChat((prev) => [...prev, { role: "assistant", content: data.answer }]);
        toast.success("Answer generated");
      } else {
        toast.error(data.message);
      }
    } catch {
      toast.error("Query failed");
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Document Analysis</h1>

        {/* Upload Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 mb-6 border">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload PDF
          </h2>
          <div className="flex gap-4">
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="flex-1 border rounded-lg p-2"
            />
            <button
              onClick={handleUpload}
              disabled={uploading || !file}
              className="px-6 py-2 bg-sky-600 text-white rounded-lg disabled:opacity-50"
            >
              {uploading ? "Processing..." : "Upload"}
            </button>
          </div>
        </div>

        {/* Chat Section */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 border">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Ask Questions
          </h2>

          <div className="h-96 overflow-y-auto mb-4 space-y-4">
            {chat.map((msg, i) => (
              <div
                key={i}
                className={`p-4 rounded-lg ${
                  msg.role === "user"
                    ? "bg-sky-100 dark:bg-sky-900/30 ml-8"
                    : "bg-gray-100 dark:bg-gray-700 mr-8"
                }`}
              >
                <p className="text-sm font-medium mb-1">
                  {msg.role === "user" ? "You" : "Assistant"}
                </p>
                <p className="text-gray-700 dark:text-gray-300">{msg.content}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-4">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask about the document..."
              className="flex-1 border rounded-lg p-3"
              onKeyPress={(e) => e.key === "Enter" && handleAsk()}
            />
            <button
              onClick={handleAsk}
              disabled={loading}
              className="px-6 py-2 bg-sky-600 text-white rounded-lg disabled:opacity-50 flex items-center gap-2"
            >
              <Send className="h-4 w-4" />
              Ask
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}