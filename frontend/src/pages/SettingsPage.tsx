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

      {/* 3. Ollama AI Metadata Configuration */}
      <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-6">
        <div className="flex items-center space-x-2">
          <Cpu className="h-5 w-5 text-purple-400" />
          <h2 className="text-base font-bold text-white">Local AI Metadata Generation (Ollama)</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="text-xs font-semibold text-slate-400 block mb-1.5">Ollama Model Name</label>
            <input
              type="text"
              value={formData.ollama_model ?? "qwen3:8b"}
              onChange={(e) => setFormData({ ...formData, ollama_model: e.target.value })}
              placeholder="e.g. qwen3:8b, llama3.2, mistral"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 focus:outline-none focus:border-red-500 font-mono"
            />
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div>
              <div className="text-sm font-medium text-slate-200">Fallback if AI Unavailable</div>
              <p className="text-xs text-slate-400">Use filename & default template if Ollama is down</p>
            </div>
            <input
              type="checkbox"
              checked={formData.fallback_if_ai_unavailable ?? true}
              onChange={(e) => setFormData({ ...formData, fallback_if_ai_unavailable: e.target.checked })}
              className="h-5 w-5 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
            />
          </div>
        </div>

        {/* AI Features Toggles */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_title ?? true}
              onChange={(e) => setFormData({ ...formData, generate_title: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
            />
            <span className="text-sm font-medium text-slate-200">Generate Title</span>
          </label>

          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_description ?? true}
              onChange={(e) => setFormData({ ...formData, generate_description: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
            />
            <span className="text-sm font-medium text-slate-200">Generate Description</span>
          </label>

          <label className="flex items-center space-x-3 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={formData.generate_tags ?? true}
              onChange={(e) => setFormData({ ...formData, generate_tags: e.target.checked })}
              className="h-4 w-4 rounded border-slate-700 text-red-600 focus:ring-red-500 accent-red-600"
            />
            <span className="text-sm font-medium text-slate-200">Generate Tags</span>
          </label>
        </div>
      </div>
    </form>
  );
};
