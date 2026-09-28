import React, { useState, useEffect } from "react";
import {
  Settings as SettingsIcon,
  HardDrive,
  Cpu,
  Shield,
  Save,
  Clock,
  RotateCw,
  FolderSync,
  Sparkles,
  CheckCircle2,
} from "lucide-react";
import { AgentSettings, DriveFolder } from "../types";

interface SettingsPageProps {
  settings: AgentSettings | null;
  folders: DriveFolder[];
  selectedFolderId?: string | null;
  onSaveSettings: (settings: Partial<AgentSettings>) => Promise<void>;
  onSelectFolder: (folderId: string, folderName?: string) => Promise<void>;
  onRefreshFolders: () => void;
  isLoading: boolean;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({
  settings,
  folders,
  selectedFolderId,
  onSaveSettings,
  onSelectFolder,
  onRefreshFolders,
  isLoading,
}) => {
  const [formData, setFormData] = useState<Partial<AgentSettings>>({});
  const [activeFolder, setActiveFolder] = useState(selectedFolderId || "");
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  useEffect(() => {
    if (selectedFolderId) {
      setActiveFolder(selectedFolderId);
    }
  }, [selectedFolderId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await onSaveSettings(formData);
    if (activeFolder && activeFolder !== selectedFolderId) {
      const selected = folders.find((f) => f.folder_id === activeFolder);
      await onSelectFolder(activeFolder, selected?.folder_name);
    }
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const categories = [
    { id: "20", label: "Gaming" },
    { id: "1", label: "Film & Animation" },
    { id: "2", label: "Autos & Vehicles" },
    { id: "10", label: "Music" },
    { id: "17", label: "Sports" },
    { id: "22", label: "People & Blogs" },
    { id: "23", label: "Comedy" },
    { id: "24", label: "Entertainment" },
    { id: "26", label: "Howto & Style" },
    { id: "27", label: "Education" },
    { id: "28", label: "Science & Technology" },
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-8 animate-fadeIn max-w-4xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-red-500" />
            Agent Configuration
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Configure automated scheduler intervals, privacy statuses, Drive folders, and Ollama AI settings.
          </p>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold text-sm shadow-lg shadow-red-600/20 active:scale-95 transition"
        >
          {isSaved ? <CheckCircle2 className="h-4 w-4 text-white" /> : <Save className="h-4 w-4" />}
          <span>{isSaved ? "Saved Successfully!" : "Save Settings"}</span>
        </button>
      </div>

      {/* 1. Google Drive Monitoring Section */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <HardDrive className="h-5 w-5 text-blue-400" />
            <h2 className="text-base font-bold text-white">Google Drive Source Folder</h2>
          </div>
          <button
            type="button"
            onClick={onRefreshFolders}
            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
          >
            <FolderSync className="h-3.5 w-3.5" /> Refresh Folders
          </button>
        </div>

        {folders.length === 0 && (
          <div className="p-3.5 rounded-xl bg-slate-900/90 border border-amber-500/30 text-xs text-amber-300 flex items-center justify-between">
            <span>
              <strong>No Drive folders found:</strong> Make sure your Google Account is connected with Google Drive permissions.
            </span>
            <button
              type="button"
              onClick={onRefreshFolders}
              className="ml-3 px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-medium transition"
            >
              Fetch / Refresh
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Select Drive Folder</label>
            <select
              value={activeFolder}
              onChange={(e) => setActiveFolder(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500"
            >
              <option value="">-- Choose a Google Drive Folder --</option>
              {folders.map((f) => (
                <option key={f.folder_id} value={f.folder_id}>
                  {f.folder_name} ({f.folder_id.slice(0, 8)}...)
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Or Enter Custom Folder ID</label>
            <input
              type="text"
              value={activeFolder}
              onChange={(e) => setActiveFolder(e.target.value)}
              placeholder="e.g. 1A2b3C4d5E6F..."
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500 font-mono"
            />
          </div>
        </div>
      </div>

      {/* 2. Upload & Privacy Settings */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <div className="flex items-center space-x-2">
          <Shield className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-white">YouTube Defaults & Schedule</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Interval */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5 flex items-center gap-1">
              <Clock className="h-3.5 w-3.5 text-emerald-400" />
              Upload Interval (Minutes)
            </label>
            <input
              type="number"
              min={5}
              max={10080}
              value={formData.interval_minutes ?? 360}
              onChange={(e) => setFormData({ ...formData, interval_minutes: parseInt(e.target.value) || 360 })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500"
            />
            <p className="text-[11px] text-slate-500 mt-1">Presets: 60 (1h), 360 (6h), 720 (12h), 1440 (Daily)</p>
          </div>

          {/* Privacy Status */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Privacy Status</label>
            <select
              value={formData.privacy_status ?? "private"}
              onChange={(e) => setFormData({ ...formData, privacy_status: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500"
            >
              <option value="private">Private (Recommended)</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>

          {/* YouTube Category */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">YouTube Category</label>
            <select
              value={formData.category_id ?? "20"}
              onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500"
            >
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label} (ID: {c.id})
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Max Retries */}
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Max Upload Retries</label>
            <input
              type="number"
              min={1}
              max={10}
              value={formData.max_retries ?? 3}
              onChange={(e) => setFormData({ ...formData, max_retries: parseInt(e.target.value) || 3 })}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500"
            />
          </div>

          {/* Delete local file */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div>
              <div className="text-sm font-medium text-slate-200">Delete Temporary File</div>
              <p className="text-xs text-slate-400">Remove local video after upload completes</p>
            </div>
            <input
              type="checkbox"
              checked={formData.delete_after_upload ?? true}
              onChange={(e) => setFormData({ ...formData, delete_after_upload: e.target.checked })}
              className="h-5 w-5 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
            />
          </div>
        </div>
      </div>

      {/* 3. AI Metadata Engine Configuration */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-purple-400" />
            <h2 className="text-base font-bold text-white">AI Content Generation (Gemini / Ollama)</h2>
          </div>
          <span className="text-xs px-2.5 py-1 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 font-medium">
            Title • Description • Tags • Thumbnail
          </span>
        </div>

        {/* Provider Selection */}
        <div>
          <label className="text-xs font-semibold text-slate-400 block mb-2">Select Primary AI Provider</label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <button
              type="button"
              onClick={() => setFormData({ ...formData, ai_provider: "gemini" })}
              className={`p-4 rounded-xl border text-left transition flex items-start space-x-3 ${
                (formData.ai_provider ?? "gemini") === "gemini"
                  ? "bg-purple-950/40 border-purple-500/60 shadow-lg shadow-purple-950/40 text-white"
                  : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              <Sparkles className={`h-5 w-5 mt-0.5 shrink-0 ${
                (formData.ai_provider ?? "gemini") === "gemini" ? "text-purple-400" : "text-slate-500"
              }`} />
              <div>
                <div className="text-sm font-bold flex items-center gap-2">
                  Google Gemini (Cloud AI)
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-semibold uppercase">
                    Recommended
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Fast, ultra-smart metadata & Imagen 3 thumbnails. No local GPU required.
                </p>
              </div>
            </button>

            <button
              type="button"
              onClick={() => setFormData({ ...formData, ai_provider: "ollama" })}
              className={`p-4 rounded-xl border text-left transition flex items-start space-x-3 ${
                formData.ai_provider === "ollama"
                  ? "bg-purple-950/40 border-purple-500/60 shadow-lg shadow-purple-950/40 text-white"
                  : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700"
              }`}
            >
              <Cpu className={`h-5 w-5 mt-0.5 shrink-0 ${
                formData.ai_provider === "ollama" ? "text-purple-400" : "text-slate-500"
              }`} />
              <div>
                <div className="text-sm font-bold">Ollama (Local LLM)</div>
                <p className="text-xs text-slate-400 mt-1">
                  Runs local models (e.g. Qwen, Llama) on your machine.
                </p>
              </div>
            </button>
          </div>
        </div>

        {/* Gemini Settings */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-4">
          <div className="flex items-center space-x-2 text-sm font-semibold text-slate-200">
            <Sparkles className="h-4 w-4 text-amber-400" />
            <span>Google Gemini Settings</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1.5">Google Gemini API Key</label>
              <input
                type="password"
                value={formData.gemini_api_key ?? ""}
                onChange={(e) => setFormData({ ...formData, gemini_api_key: e.target.value })}
                placeholder="AIzaSy..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-amber-500 font-mono"
              />
              <p className="text-[11px] text-slate-500 mt-1">Free key available at <a href="https://aistudio.google.com" target="_blank" rel="noreferrer" className="text-amber-400 hover:underline">aistudio.google.com</a></p>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1.5">Gemini Text Model</label>
              <select
                value={formData.gemini_model ?? "gemini-2.5-flash-lite"}
                onChange={(e) => setFormData({ ...formData, gemini_model: e.target.value })}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
              >
                <option value="gemini-2.5-flash-lite">gemini-2.5-flash-lite (Default - Ultra Fast & Efficient)</option>
                <option value="gemini-2.5-flash">gemini-2.5-flash (High Performance)</option>
                <option value="gemini-2.5-pro">gemini-2.5-pro (Advanced Reasoning)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Local Ollama Settings (Optional fallback / alternative) */}
        {(formData.ai_provider === "ollama" || !formData.gemini_api_key) && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="text-xs font-semibold text-slate-400 block mb-1.5">Local Ollama Model Name</label>
              <input
                type="text"
                value={formData.ollama_model ?? "qwen3:8b"}
                onChange={(e) => setFormData({ ...formData, ollama_model: e.target.value })}
                placeholder="e.g. qwen3:8b, llama3.2"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
              />
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div>
                <div className="text-sm font-medium text-slate-200">Fallback if AI Unavailable</div>
                <p className="text-xs text-slate-400">Use formatted title if offline</p>
              </div>
              <input
                type="checkbox"
                checked={formData.fallback_if_ai_unavailable ?? true}
                onChange={(e) => setFormData({ ...formData, fallback_if_ai_unavailable: e.target.checked })}
                className="h-5 w-5 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
              />
            </div>
          </div>
        )}

        {/* Feature Toggles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_title ?? true}
              onChange={(e) => setFormData({ ...formData, generate_title: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-purple-600 focus:ring-purple-500 accent-purple-600"
            />
            <span className="text-xs font-semibold text-slate-200">Generate Title</span>
          </label>

          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_description ?? true}
              onChange={(e) => setFormData({ ...formData, generate_description: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-purple-600 focus:ring-purple-500 accent-purple-600"
            />
            <span className="text-xs font-semibold text-slate-200">Generate Description</span>
          </label>

          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_tags ?? true}
              onChange={(e) => setFormData({ ...formData, generate_tags: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-purple-600 focus:ring-purple-500 accent-purple-600"
            />
            <span className="text-xs font-semibold text-slate-200">Generate Tags</span>
          </label>

          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_thumbnail ?? true}
              onChange={(e) => setFormData({ ...formData, generate_thumbnail: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-amber-500 focus:ring-amber-400 accent-amber-500"
            />
            <span className="text-xs font-semibold text-slate-200">Generate Thumbnail</span>
          </label>
        </div>
      </div>
    </form>
  );
};
