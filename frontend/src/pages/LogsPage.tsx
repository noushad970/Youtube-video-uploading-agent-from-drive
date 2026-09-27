import React, { useState, useEffect } from "react";
import {
  Terminal,
  Search,
  RefreshCw,
  Trash2,
  AlertCircle,
  Info,
  AlertTriangle,
  Play,
  Pause,
} from "lucide-react";
import { LogEntry } from "../types";

interface LogsPageProps {
  logs: LogEntry[];
  total: number;
  isLoading: boolean;
  onRefresh: () => void;
  onClearLogs: () => void;
}

export const LogsPage: React.FC<LogsPageProps> = ({
  logs,
  total,
  isLoading,
  onRefresh,
  onClearLogs,
}) => {
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    let timer: any;
    if (autoRefresh) {
      timer = setInterval(() => {
        onRefresh();
      }, 4000);
    }
    return () => clearInterval(timer);
  }, [autoRefresh, onRefresh]);

  const filteredLogs = logs.filter((log) => {
    const matchesLevel = levelFilter === "ALL" ? true : log.level === levelFilter;
    const matchesSearch =
      log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (log.details && log.details.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesLevel && matchesSearch;
  });

  const formatTime = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0");
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Terminal className="h-6 w-6 text-red-500" />
            System & Agent Execution Logs
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time streaming logs from the autonomous upload pipeline, Ollama LLM, and YouTube API.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
              autoRefresh
                ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/30"
                : "bg-slate-900 text-slate-400 border-slate-800"
            }`}
          >
            {autoRefresh ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
            <span>Auto Refresh: {autoRefresh ? "ON" : "OFF"}</span>
          </button>

          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh Logs"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>

          <button
            onClick={onClearLogs}
            className="p-2 rounded-xl bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 border border-slate-700 hover:border-rose-500/30 transition"
            title="Clear Logs"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Toolbar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search log messages or stack traces..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-red-500/50"
          />
        </div>

        <div className="flex items-center space-x-1.5">
          {["ALL", "INFO", "WARNING", "ERROR"].map((lvl) => (
            <button
              key={lvl}
              onClick={() => setLevelFilter(lvl)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                levelFilter === lvl
                  ? "bg-red-500/15 text-red-400 border border-red-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>
      </div>

      {/* Logs Terminal Console */}
      <div className="rounded-2xl bg-slate-950 border border-slate-800/80 p-4 font-mono text-xs shadow-2xl overflow-hidden">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-slate-900 text-slate-500 text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
            <span className="ml-2 font-sans font-semibold text-slate-400">agent.log stream</span>
          </div>
          <div>Total entries: {filteredLogs.length}</div>
        </div>

        <div className="space-y-1.5 max-h-[600px] overflow-y-auto pr-2">
          {filteredLogs.length === 0 ? (
            <div className="text-center py-16 text-slate-600 font-sans">
              No logs captured yet. Execute an action or upload to view output.
            </div>
          ) : (
            filteredLogs.map((log) => {
              const isError = log.level === "ERROR";
              const isWarn = log.level === "WARNING";
              const colorClass = isError
                ? "text-rose-400 bg-rose-950/20"
                : isWarn
                ? "text-amber-400 bg-amber-950/20"
                : "text-slate-300";

              return (
                <div
                  key={log.id}
                  className={`p-2 rounded-lg transition hover:bg-slate-900/60 ${colorClass}`}
                >
                  <div className="flex items-start space-x-3">
                    <span className="text-slate-600 shrink-0">{formatTime(log.created_at)}</span>
                    <span
                      className={`px-1.5 py-0.2 rounded text-[10px] font-bold uppercase shrink-0 ${
                        isError
                          ? "bg-rose-500/20 text-rose-400"
                          : isWarn
                          ? "bg-amber-500/20 text-amber-400"
                          : "bg-blue-500/20 text-blue-400"
                      }`}
                    >
                      {log.level}
                    </span>
                    <span className="break-all flex-1">{log.message}</span>
                  </div>

                  {log.details && (
                    <div className="mt-1.5 ml-14 p-2 rounded bg-slate-900/80 border border-slate-800 text-[11px] text-slate-400 whitespace-pre-wrap">
                      {log.details}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
