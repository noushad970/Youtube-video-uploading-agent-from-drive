import React, { useState } from "react";
import {
  Video as VideoIcon,
  Search,
  RefreshCw,
  FolderSync,
  RotateCcw,
  UploadCloud,
  FileVideo,
  CheckCircle2,
  AlertTriangle,
  ArrowUpRight,
} from "lucide-react";
import { VideoItem } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface VideosPageProps {
  videos: VideoItem[];
  total: number;
  uploadedCount: number;
  remainingCount: number;
  isLoading: boolean;
  selectedFolderName?: string | null;
  onRefresh: () => void;
  onSync: () => void;
  onResetVideo: (videoId: number) => void;
  onManualUpload: (video: VideoItem) => void;
}

export const VideosPage: React.FC<VideosPageProps> = ({
  videos,
  total,
  uploadedCount,
  remainingCount,
  isLoading,
  selectedFolderName,
  onRefresh,
  onSync,
  onResetVideo,
  onManualUpload,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const filteredVideos = videos.filter((v) => {
    const matchesSearch = v.file_name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus =
      statusFilter === "all"
        ? true
        : statusFilter === "uploaded"
        ? v.status === "uploaded"
        : statusFilter === "available"
        ? v.status === "available"
        : statusFilter === "failed"
        ? v.status === "failed"
        : v.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const formatSize = (bytes: number) => {
    if (!bytes) return "0 MB";
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <VideoIcon className="h-6 w-6 text-red-500" />
            Video Catalog
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Drive Folder: <span className="text-white font-medium">"{selectedFolderName || "None Selected"}"</span> • Total:{" "}
            <span className="text-slate-200 font-semibold">{total}</span> • Uploaded:{" "}
            <span className="text-emerald-400 font-semibold">{uploadedCount}</span> • Remaining:{" "}
            <span className="text-amber-400 font-semibold">{remainingCount}</span>
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={onSync}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-medium transition"
          >
            <FolderSync className="h-4 w-4" />
            <span>Sync with Drive</span>
          </button>
          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh List"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by filename or title..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-red-500/50"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex flex-wrap items-center gap-1.5">
          {["all", "available", "uploaded", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition ${
                statusFilter === f
                  ? "bg-red-500/15 text-red-400 border border-red-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Videos List Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        {filteredVideos.length === 0 ? (
          <div className="text-center py-16 text-slate-500 space-y-2">
            <FileVideo className="h-10 w-10 mx-auto text-slate-600 opacity-60" />
            <p className="text-sm font-medium">No videos found matching criteria.</p>
            <p className="text-xs">Select a Drive folder in Settings or click "Sync with Drive".</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">Filename</th>
                  <th className="py-3.5 px-4">Size</th>
                  <th className="py-3.5 px-4">Resolution</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">YouTube ID</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredVideos.map((video) => (
                  <tr key={video.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 shrink-0">
                          <FileVideo className="h-4 w-4" />
                        </div>
                        <div className="truncate max-w-xs sm:max-w-md">
                          <div className="font-semibold text-slate-100 truncate">{video.file_name}</div>
                          <div className="text-[11px] font-mono text-slate-500 truncate">{video.drive_file_id}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 font-mono text-xs">{formatSize(video.size)}</td>
                    <td className="py-3.5 px-4">
                      {video.resolution ? (
                        <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-xs font-mono text-slate-400">
                          {video.resolution}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-600">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={video.status} />
                    </td>
                    <td className="py-3.5 px-4">
                      {video.youtube_video_id ? (
                        <a
                          href={`https://youtu.be/${video.youtube_video_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center text-xs font-mono text-blue-400 hover:text-blue-300 hover:underline"
                        >
                          {video.youtube_video_id}
                          <ArrowUpRight className="h-3 w-3 ml-0.5" />
                        </a>
                      ) : (
                        <span className="text-xs text-slate-600">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {video.status === "uploaded" ? (
                          <button
                            onClick={() => onResetVideo(video.id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
                            title="Reset upload status to allow re-upload"
                          >
                            <RotateCcw className="h-4 w-4" />
                          </button>
                        ) : (
                          <button
                            onClick={() => onManualUpload(video)}
                            className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-600/20 text-red-400 border border-red-500/30 hover:bg-red-600/30 transition"
                          >
                            <UploadCloud className="h-3.5 w-3.5" />
                            <span>Upload</span>
                          </button>
                        )}
                      </div>
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
