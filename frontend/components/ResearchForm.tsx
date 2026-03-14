"use client";

import { useState } from "react";
import { Loader2, Search, Sparkles } from "lucide-react";
import { ResearchRequest } from "@/types";

interface ResearchFormProps {
  onSubmit: (request: ResearchRequest) => void;
  isLoading: boolean;
}

export default function ResearchForm({ onSubmit, isLoading }: ResearchFormProps) {
  const [query, setQuery] = useState("");
  const [workflow, setWorkflow] = useState<"sequential" | "group_chat" | "iterative">("group_chat");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || isLoading) return;

    onSubmit({
      query: query.trim(),
      workflow,
      max_iterations: 3,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="query" className="block text-sm font-medium mb-2">
          Research Query
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., recent advances in federated learning"
            className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent dark:bg-gray-800"
            disabled={isLoading}
          />
        </div>
      </div>

      <div>
        <label htmlFor="workflow" className="block text-sm font-medium mb-2">
          Workflow Type
        </label>
        <select
          id="workflow"
          value={workflow}
          onChange={(e) => setWorkflow(e.target.value as any)}
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-sky-500 focus:border-transparent dark:bg-gray-800"
          disabled={isLoading}
        >
          <option value="group_chat">Group Chat (Recommended)</option>
          <option value="sequential">Sequential</option>
          <option value="iterative">Iterative (Highest Quality)</option>
        </select>
      </div>

      <button
        type="submit"
        disabled={isLoading || !query.trim()}
        className="w-full bg-gradient-to-r from-sky-600 to-sky-700 hover:from-sky-700 hover:to-sky-800 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="h-5 w-5 animate-spin" />
            Researching...
          </>
        ) : (
          <>
            <Sparkles className="h-5 w-5" />
            Start Research
          </>
        )}
      </button>
    </form>
  );
}