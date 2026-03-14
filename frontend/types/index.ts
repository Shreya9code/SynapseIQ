export interface ResearchRequest {
  query: string;
  workflow: "sequential" | "group_chat" | "iterative";
  max_iterations?: number;
}

export interface ResearchResponse {
  status: "complete" | "error";
  report: string;
  workflow: string;
}

export interface AgentStatus {
  name: string;
  status: "idle" | "working" | "complete" | "error";
  message?: string;
}