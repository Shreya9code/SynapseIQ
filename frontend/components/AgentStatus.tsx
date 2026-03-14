"use client";

import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

interface AgentStatusProps {
  agents: Array<{
    name: string;
    status: "idle" | "working" | "complete" | "error";
    message?: string;
  }>;
}

export default function AgentStatus({ agents }: AgentStatusProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case "working":
        return <Loader2 className="h-5 w-5 animate-spin text-sky-500" />;
      case "complete":
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case "error":
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 space-y-3">
      <h3 className="font-semibold text-sm uppercase tracking-wide text-gray-600 dark:text-gray-400">
        Agent Status
      </h3>
      <div className="space-y-2">
        {agents.map((agent) => (
          <div
            key={agent.name}
            className="flex items-center gap-3 p-2 rounded-md bg-white dark:bg-gray-800 shadow-sm"
          >
            {getStatusIcon(agent.status)}
            <div className="flex-1">
              <div className="font-medium text-sm">{agent.name}</div>
              {agent.message && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {agent.message}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}