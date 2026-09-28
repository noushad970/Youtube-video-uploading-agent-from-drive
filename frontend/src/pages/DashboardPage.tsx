import React from "react";
import {
  Video,
  CheckCircle2,
  Clock,
  AlertCircle,
  HardDrive,
  Youtube,
  Cpu,
  Calendar,
  Sparkles,
  ArrowUpRight,
  RefreshCw,
  FolderSync,
} from "lucide-react";
import { AgentStatus, AuthStatus, UploadRecord } from "../types";
import { StatsCard } from "../components/StatsCard";
import { StatusBadge } from "../components/StatusBadge";

interface DashboardPageProps {
  status: AgentStatus | null;
  auth: AuthStatus | null;
  recentUploads: UploadRecord[];
  onUploadNow: () => void;
  onSyncFolder: () => void;
  onToggleAgent: () => void;
  isUploading: boolean;
  isSyncing: boolean;
  setActiveTab: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  status,
  auth,
  recentUploads,
  onUploadNow,
  onSyncFolder,
  onToggleAgent,
  isUploading,
  isSyncing,
  setActiveTab,
}) => {
  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return "Never";
    try {
      const d = new Date(dateStr);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) + ", " + d.toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Top Banner / Hero */}
      <div className="relative overflow-hidden rounded-3xl p-6 sm:p-8 bg-gradient-to-r from-red-950/40 via-slate-900/60 to-slate-900 border border-red-500/20 shadow-xl">
        <div className="absolute right-0 top-0 translate-x-8 -translate-y-8 w-96 h-96 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Automated Content Delivery</span>
            </div>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
              YouTube AI Upload Agent
            </h1>
            <p className="mt-2 text-slate-300 text-sm sm:text-base leading-relaxed">
              Monitoring Google Drive folder <span className="font-semibold text-white">"{status?.selected_folder_name || "None Selected"}"</span>.
              Randomly selects unuploaded videos, generates AI metadata & 16:9 thumbnails using{" "}
              <span className="text-amber-400 font-medium">
                {status?.ai_provider === "gemini" ? "Google Gemini AI (2.5 Flash-Lite & Imagen 3)" : "Ollama AI"}
              </span>
              , and uploads to YouTube safely.
            </p>
          </div>

          {/* Quick Action Matrix */}
          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onUploadNow}
              disabled={isUploading}
              className="flex items-center space-x-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold text-sm shadow-lg shadow-red-600/25 active:scale-95 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${isUploading ? "animate-spin" : ""}`} />
              <span>{isUploading ? "Uploading Video..." : "Upload One Now"}</span>
            </button>

            <button
              onClick={onSyncFolder}
              disabled={isSyncing}
              className="flex items-center space-x-2 px-4 py-3 rounded-2xl bg-slate-800/80 hover:bg-slate-700/80 text-slate-200 border border-slate-700 font-medium text-sm transition-all"
            >
              <FolderSync className={`h-4 w-4 ${isSyncing ? "animate-spin" : ""}`} />
              <span>Sync Drive</span>
            </button>
          </div>
        </div>
      </div>

      {/* Overview Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <StatsCard
          title="Total Videos"
          value={status?.total_videos ?? 0}
          subtitle={`In Drive folder: ${status?.selected_folder_name || "Unset"}`}
          icon={Video}
          color="blue"
        />
        <StatsCard
          title="Uploaded"
          value={status?.uploaded_videos ?? 0}
          subtitle="Successfully on YouTube"
          icon={CheckCircle2}
          color="emerald"
        />
        <StatsCard
          title="Remaining"
          value={status?.remaining_videos ?? 0}
          subtitle="Ready for next run"
          icon={Clock}
          color="amber"
        />
        <StatsCard
          title="Agent State"
          value={status?.is_running ? "Active" : "Paused"}
          subtitle={status?.is_running ? "Scheduled & running" : "Manual mode only"}
          icon={Calendar}
          color={status?.is_running ? "emerald" : "purple"}
        />
      </div>

      {/* Services Health Matrix & Schedule Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Services Status Grid */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-red-400" />
              Connected Integrations & Status
            </h2>
            <button
              onClick={() => setActiveTab("settings")}
              className="text-xs text-red-400 hover:text-red-300 font-medium flex items-center gap-1"
            >
              Configure Settings <ArrowUpRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Google Account */}
            <div className="glass-card rounded-xl p-4 flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-red-500/10 text-red-400">
                  <Youtube className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Google OAuth</h4>
                  <p className="text-xs text-slate-400 truncate max-w-[150px]">
                    {auth?.email || "No account linked"}
                  </p>
                </div>
              </div>
              <StatusBadge status={auth?.is_authenticated ? "connected" : "disconnected"} />
            </div>

            {/* Google Drive */}
            <div className="glass-card rounded-xl p-4 flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400">
                  <HardDrive className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Google Drive</h4>
                  <p className="text-xs text-slate-400 truncate max-w-[150px]">
                    {status?.selected_folder_name || "Select folder"}
                  </p>
                </div>
              </div>
              <StatusBadge status={status?.drive_connected ? "connected" : "disconnected"} />
            </div>

            {/* YouTube Channel */}
            <div className="glass-card rounded-xl p-4 flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400">
                  <Youtube className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">YouTube Upload API</h4>
                  <p className="text-xs text-slate-400">Data API v3</p>
                </div>
              </div>
              <StatusBadge status={status?.youtube_connected ? "connected" : "disconnected"} />
            </div>

            {/* AI Provider */}
            <div className="glass-card rounded-xl p-4 flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div
                  className={`p-2.5 rounded-lg ${
                    status?.ai_provider === "gemini" ? "bg-amber-500/10 text-amber-400" : "bg-purple-500/10 text-purple-400"
                  }`}
                >
                  <Cpu className="h-5 w-5" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">
                    {status?.ai_provider === "gemini" ? "Google Gemini AI" : "Local Ollama LLM"}
                  </h4>
                  <p className="text-xs text-slate-400">
                    {status?.ai_provider === "gemini"
                      ? "Gemini 2.5 Flash-Lite & Imagen 3"
                      : "Metadata generation"}
                  </p>
                </div>
              </div>
              <StatusBadge
                status={
                  status?.ai_connected ||
                  (status?.ai_provider === "gemini" ? status?.gemini_ready : status?.ollama_connected)
                    ? "connected"
                    : "disconnected"
                }
              />
            </div>
          </div>
        </div>

        {/* Schedule & Execution Card */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Clock className="h-4 w-4 text-emerald-400" />
              Schedule & Run Status
            </h2>

            <div className="space-y-4 text-sm">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-slate-400">Last Upload</span>
                <span className="font-semibold text-slate-200">{formatDate(status?.last_upload_at)}</span>
              </div>

              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-slate-400">Next Scheduled Run</span>
                <span className="font-semibold text-emerald-400">
                  {status?.is_running ? formatDate(status?.next_scheduled_run) : "Paused"}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-slate-400">Last Execution</span>
                <span className="font-medium text-slate-300 capitalize">{status?.last_run_status || "None"}</span>
              </div>

              {status?.last_run_error && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400 flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                  <span className="truncate">{status.last_run_error}</span>
                </div>
              )}
            </div>
          </div>

          <div className="pt-6">
            <button
              onClick={onToggleAgent}
              className={`w-full py-2.5 rounded-xl font-semibold text-sm transition ${
                status?.is_running
                  ? "bg-slate-800 hover:bg-slate-700 text-slate-300"
                  : "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20"
              }`}
            >
              {status?.is_running ? "Pause Scheduled Agent" : "Enable Automatic Schedule"}
            </button>
          </div>
        </div>
      </div>

      {/* Recent Uploads Table */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            Recent Upload Activity
          </h2>
          <button
            onClick={() => setActiveTab("uploads")}
            className="text-xs text-slate-400 hover:text-white transition flex items-center gap-1"
          >
            View All History <ArrowUpRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {recentUploads.length === 0 ? (
          <div className="text-center py-10 text-slate-500 text-sm">
            No videos uploaded yet. Click "Upload One Now" or start the schedule to begin!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400 bg-slate-900/60 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Title / Video</th>
                  <th className="py-3 px-4">YouTube ID</th>
                  <th className="py-3 px-4">Privacy</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Uploaded At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentUploads.slice(0, 5).map((upload) => (
                  <tr key={upload.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-white truncate max-w-xs sm:max-w-md">
                        {upload.title}
                      </div>
                      <div className="text-xs text-slate-400 truncate">{upload.file_name}</div>
                    </td>
                    <td className="py-3 px-4">
                      {upload.youtube_video_id ? (
                        <a
                          href={`https://youtu.be/${upload.youtube_video_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center text-xs text-blue-400 hover:text-blue-300 font-mono hover:underline"
                        >
                          {upload.youtube_video_id}
                          <ArrowUpRight className="h-3 w-3 ml-0.5" />
                        </a>
                      ) : (
                        <span className="text-xs text-slate-500">N/A</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={upload.privacy_status} />
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={upload.status} />
                    </td>
                    <td className="py-3 px-4 text-right text-xs text-slate-400">
                      {formatDate(upload.uploaded_at || upload.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
