"use client";

import { useState, useEffect } from "react";
import ResearchForm from "@/components/ResearchForm";
import AgentStatus from "@/components/AgentStatus";
import ReportViewer from "@/components/ReportViewer";
import { startResearch, checkHealth } from "@/lib/api";
import { ResearchRequest, ResearchResponse, AgentStatus as AgentStatusType } from "@/types";
import { toast } from "sonner";
import { AlertCircle, Brain, Loader2 } from "lucide-react";

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [report, setReport] = useState<string | null>(null);
  const [agents, setAgents] = useState<AgentStatusType[]>([
    { name: "Searcher", status: "idle" },
    { name: "Summarizer", status: "idle" },
    { name: "Trend Analyzer", status: "idle" },
    { name: "Writer", status: "idle" },
    { name: "Validator", status: "idle" },
  ]);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    checkHealth().then(setBackendHealthy);
  }, []);

  const handleResearch = async (request: ResearchRequest) => {
    setIsLoading(true);
    setReport(null);

    setAgents((prev) =>
      prev.map((agent) => ({
        ...agent,
        status: agent.name === "Searcher" ? "working" : "idle",
      }))
    );

    try {
      const response: ResearchResponse = await startResearch(request);

      if (response.status === "error") {
        throw new Error(response.report);
      }

      setReport(response.report);
      toast.success("Research completed successfully!");

      setAgents((prev) =>
        prev.map((agent) => ({
          ...agent,
          status: "complete",
          message: "Task completed",
        }))
      );
    } catch (error: any) {
      toast.error(error.message || "Research failed");
      setAgents((prev) =>
        prev.map((agent) =>
          agent.name === "Searcher"
            ? { ...agent, status: "error", message: error.message }
            : agent
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center gap-3">
            <Brain className="h-8 w-8 text-sky-600" />
            <div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-sky-600 to-sky-700 bg-clip-text text-transparent">
                AI Research Assistant
              </h1>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Multi-agent research powered by AutoGen & Groq
              </p>
            </div>
          </div>
        </div>
      </header>

      {backendHealthy === false && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
            <div>
              <p className="font-medium text-red-800 dark:text-red-200">
                Backend Not Connected
              </p>
              <p className="text-sm text-red-600 dark:text-red-300">
                Make sure the backend is running on http://localhost:8000
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
              <h2 className="text-lg font-semibold mb-4">New Research</h2>
              <ResearchForm onSubmit={handleResearch} isLoading={isLoading} />
            </div>

            <AgentStatus agents={agents} />
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700 min-h-[600px]">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center h-full py-20">
                  <Loader2 className="h-12 w-12 animate-spin text-sky-600 mb-4" />
                  <p className="text-lg font-medium">Agents are researching...</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
                    This may take 1-2 minutes
                  </p>
                </div>
              ) : report ? (
                <ReportViewer report={report} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full py-20 text-gray-400">
                  <Brain className="h-16 w-16 mb-4 opacity-50" />
                  <p className="text-lg font-medium">Ready to Research</p>
                  <p className="text-sm mt-2">
                    Enter a query to start multi-agent research
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}