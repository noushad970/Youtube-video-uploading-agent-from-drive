import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "./components/Navbar";
import { DashboardPage } from "./pages/DashboardPage";
import { VideosPage } from "./pages/VideosPage";
import { UploadsPage } from "./pages/UploadsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { GoogleAccountPage } from "./pages/GoogleAccountPage";
import { LogsPage } from "./pages/LogsPage";
import { apiClient } from "./services/api";
import {
  AgentStatus,
  AuthStatus,
  DriveFolder,
  VideoItem,
  UploadRecord,
  AgentSettings,
  LogEntry,
} from "./types";
import { AlertCircle, CheckCircle2, X } from "lucide-react";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState("dashboard");

  // Global state
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [auth, setAuth] = useState<AuthStatus | null>(null);
  const [settings, setSettings] = useState<AgentSettings | null>(null);
  const [folders, setFolders] = useState<DriveFolder[]>([]);
  const [videos, setVideos] = useState<VideoItem[]>([]);
  const [videoStats, setVideoStats] = useState({ total: 0, uploaded: 0, remaining: 0 });
  const [uploads, setUploads] = useState<UploadRecord[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  // Loading & operational states
  const [isUploading, setIsUploading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [isLoadingVideos, setIsLoadingVideos] = useState(false);
  const [isLoadingUploads, setIsLoadingUploads] = useState(false);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);

  // Toast notifications
  const [toast, setToast] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);

  const showToast = (type: "success" | "error" | "info", message: string) => {
    setToast({ type, message });
    const duration = type === "error" ? 8000 : 5000;
    setTimeout(() => {
      setToast((current) => (current?.message === message ? null : current));
    }, duration);
  };

  // Fetch Core Status
  const fetchStatusAndAuth = useCallback(async () => {
    try {
      const [statusRes, authRes] = await Promise.allSettled([
        apiClient.getAgentStatus(),
        apiClient.getAuthStatus(),
      ]);
      if (statusRes.status === "fulfilled") {
        setStatus(statusRes.value);
      }
      if (authRes.status === "fulfilled") {
        setAuth(authRes.value);
      }
    } catch (e) {
      console.error("Status check failed", e);
    }
  }, []);

  // Fetch Videos
  const fetchVideos = useCallback(async () => {
    setIsLoadingVideos(true);
    try {
      const res = await apiClient.getVideos({ limit: 200 });
      setVideos(res.videos);
      setVideoStats({
        total: res.total,
        uploaded: res.uploaded_count,
        remaining: res.remaining_count,
      });
    } catch (e) {
      console.error("Fetch videos failed", e);
    } finally {
      setIsLoadingVideos(false);
    }
  }, []);

  // Fetch Uploads
  const fetchUploads = useCallback(async () => {
    setIsLoadingUploads(true);
    try {
      const res = await apiClient.getUploads({ limit: 100 });
      setUploads(res.items);
    } catch (e) {
      console.error("Fetch uploads failed", e);
    } finally {
      setIsLoadingUploads(false);
    }
  }, []);

  // Fetch Settings & Folders
  const fetchSettingsAndFolders = useCallback(async () => {
    try {
      const [settingsRes, foldersRes] = await Promise.allSettled([
        apiClient.getSettings(),
        apiClient.getDriveFolders(),
      ]);
      if (settingsRes.status === "fulfilled") {
        setSettings(settingsRes.value);
      }
      if (foldersRes.status === "fulfilled") {
        setFolders(foldersRes.value);
      }
    } catch (e) {
      console.error("Settings load failed", e);
    }
  }, []);

  // Fetch Logs
  const fetchLogs = useCallback(async () => {
    setIsLoadingLogs(true);
    try {
      const res = await apiClient.getLogs({ limit: 150 });
      setLogs(res.logs);
    } catch (e) {
      console.error("Fetch logs failed", e);
    } finally {
      setIsLoadingLogs(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    fetchStatusAndAuth();
    fetchVideos();
    fetchUploads();
    fetchSettingsAndFolders();
    fetchLogs();

    // Check for auth redirect in URL
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("auth") === "success") {
      showToast("success", "Google account connected successfully!");
      window.history.replaceState({}, document.title, window.location.pathname);
      fetchStatusAndAuth();
    } else if (urlParams.get("error")) {
      showToast("error", `Authentication error: ${urlParams.get("error")}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [fetchStatusAndAuth, fetchVideos, fetchUploads, fetchSettingsAndFolders, fetchLogs]);

  // Periodic poll for status & logs
  useEffect(() => {
    const interval = setInterval(() => {
      fetchStatusAndAuth();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchStatusAndAuth]);

  // Actions
  const handleToggleAgent = async () => {
    try {
      if (status?.is_running) {
        await apiClient.stopAgent();
        showToast("info", "Agent paused.");
      } else {
        await apiClient.startAgent();
        showToast("success", "Agent enabled! Automatic uploads scheduled.");
      }
      fetchStatusAndAuth();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Failed to toggle agent state.");
    }
  };

  const handleUploadNow = async () => {
    setIsUploading(true);
    showToast("info", "Autonomous upload sequence started...");
    try {
      const res = await apiClient.uploadNow();
      if (res.success) {
        showToast("success", `Uploaded successfully! YouTube ID: ${res.youtube_video_id}`);
      } else {
        showToast("error", res.message || "Upload run completed with errors.");
      }
      fetchStatusAndAuth();
      fetchVideos();
      fetchUploads();
      fetchLogs();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Upload execution failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSyncFolder = async () => {
    setIsSyncing(true);
    try {
      const res = await apiClient.syncVideos();
      showToast("success", `Synced ${res.count} videos from "${res.folder_name}".`);
      fetchVideos();
      fetchStatusAndAuth();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Sync failed. Check Drive folder access.");
    } finally {
      setIsSyncing(false);
    }
  };

  const handleResetVideo = async (videoId: number) => {
    try {
      await apiClient.resetVideo(videoId);
      showToast("success", "Video status reset to Available.");
      fetchVideos();
      fetchStatusAndAuth();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Failed to reset video.");
    }
  };

  const handleManualUploadSpecific = async (video: VideoItem) => {
    setIsUploading(true);
    showToast("info", `Uploading "${video.file_name}" to YouTube...`);
    try {
      await apiClient.manualUpload({ video_id: video.id });
      showToast("success", `Video "${video.file_name}" uploaded successfully!`);
      fetchVideos();
      fetchUploads();
      fetchStatusAndAuth();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Upload failed.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleConnectGoogle = async () => {
    try {
      const { authorization_url } = await apiClient.getAuthUrl(false);
      window.location.href = authorization_url;
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Could not generate Google Auth URL. Check .env config.");
    }
  };

  const handleDisconnectGoogle = async () => {
    if (!window.confirm("Are you sure you want to disconnect your Google Account?")) return;
    try {
      await apiClient.disconnectGoogle();
      showToast("info", "Google Account disconnected.");
      fetchStatusAndAuth();
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Disconnect failed.");
    }
  };

  const handleSaveSettings = async (newSettings: Partial<AgentSettings>) => {
    try {
      const updated = await apiClient.updateSettings(newSettings);
      setSettings(updated);
      fetchStatusAndAuth();
      showToast("success", "Settings updated.");
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Failed to save settings.");
    }
  };

  const handleSelectFolder = async (folderId: string, folderName?: string) => {
    try {
      await apiClient.selectFolder(folderId, folderName);
      fetchStatusAndAuth();
      fetchVideos();
      showToast("success", `Selected Drive folder "${folderName || folderId}".`);
    } catch (e: any) {
      showToast("error", e.response?.data?.detail || "Failed to select folder.");
    }
  };

  const handleClearLogs = async () => {
    if (!window.confirm("Clear all system log entries?")) return;
    try {
      await apiClient.clearLogs();
      setLogs([]);
      showToast("info", "Logs cleared.");
    } catch (e: any) {
      showToast("error", "Failed to clear logs.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Center-Bottom Notice / Error Debug Popup */}
      {toast && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[99999] w-full max-w-lg px-4 pointer-events-auto">
          <div
            className={`flex items-start justify-between space-x-3 px-5 py-4 rounded-2xl shadow-2xl border backdrop-blur-xl text-sm font-medium transition-all duration-300 ${
              toast.type === "success"
                ? "bg-emerald-950/95 text-emerald-200 border-emerald-500/60 shadow-emerald-950/60 glow-emerald"
                : toast.type === "error"
                ? "bg-rose-950/95 text-rose-200 border-rose-500/60 shadow-rose-950/60 glow-red"
                : "bg-slate-900/95 text-slate-100 border-slate-700 shadow-slate-950/60 glow-blue"
            }`}
          >
            <div className="flex items-start space-x-3 overflow-hidden flex-1">
              {toast.type === "success" ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
              ) : toast.type === "error" ? (
                <AlertCircle className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
              ) : (
                <AlertCircle className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
              )}
              <div className="flex-1 text-sm leading-snug break-words">
                <span className="font-semibold block text-xs tracking-wide uppercase opacity-80 mb-0.5">
                  {toast.type === "error" ? "Notice / Debug Error" : toast.type === "success" ? "Success" : "Notification"}
                </span>
                <span className="text-slate-100 font-normal">{toast.message}</span>
              </div>
            </div>
            <button
              onClick={() => setToast(null)}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition shrink-0 ml-2"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Navigation Header */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        status={status}
        auth={auth}
        onToggleAgent={handleToggleAgent}
        onUploadNow={handleUploadNow}
        isUploading={isUploading}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === "dashboard" && (
          <DashboardPage
            status={status}
            auth={auth}
            recentUploads={uploads}
            onUploadNow={handleUploadNow}
            onSyncFolder={handleSyncFolder}
            onToggleAgent={handleToggleAgent}
            isUploading={isUploading}
            isSyncing={isSyncing}
            setActiveTab={setActiveTab}
          />
        )}

        {activeTab === "videos" && (
          <VideosPage
            videos={videos}
            total={videoStats.total}
            uploadedCount={videoStats.uploaded}
            remainingCount={videoStats.remaining}
            isLoading={isLoadingVideos}
            selectedFolderName={status?.selected_folder_name}
            onRefresh={fetchVideos}
            onSync={handleSyncFolder}
            onResetVideo={handleResetVideo}
            onManualUpload={handleManualUploadSpecific}
          />
        )}

        {activeTab === "uploads" && (
          <UploadsPage
            uploads={uploads}
            total={uploads.length}
            isLoading={isLoadingUploads}
            onRefresh={fetchUploads}
          />
        )}

        {activeTab === "settings" && (
          <SettingsPage
            settings={settings}
            folders={folders}
            selectedFolderId={status?.selected_folder_id}
            onSaveSettings={handleSaveSettings}
            onSelectFolder={handleSelectFolder}
            onRefreshFolders={fetchSettingsAndFolders}
            isLoading={false}
          />
        )}

        {activeTab === "account" && (
          <GoogleAccountPage
            auth={auth}
            onConnectGoogle={handleConnectGoogle}
            onDisconnectGoogle={handleDisconnectGoogle}
          />
        )}

        {activeTab === "logs" && (
          <LogsPage
            logs={logs}
            total={logs.length}
            isLoading={isLoadingLogs}
            onRefresh={fetchLogs}
            onClearLogs={handleClearLogs}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/60 py-6 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>YouTube AI Upload Agent • Autonomous Drive-to-YouTube Delivery</div>
          <div className="flex items-center space-x-4">
            <span className="text-slate-400 font-mono">FastAPI • React • Ollama</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
export default App;
