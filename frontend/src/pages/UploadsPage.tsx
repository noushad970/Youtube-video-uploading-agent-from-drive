import React, { useState } from "react";
import {
  History,
  Search,
  RefreshCw,
  ExternalLink,
  Tag,
  AlertCircle,
  FileText,
  CheckCircle2,
  Calendar,
} from "lucide-react";
import { UploadRecord } from "../types";
import { StatusBadge } from "../components/StatusBadge";

interface UploadsPageProps {
  uploads: UploadRecord[];
  total: number;
  isLoading: boolean;
  onRefresh: () => void;
}

export const UploadsPage: React.FC<UploadsPageProps> = ({
  uploads,
  total,
  isLoading,
  onRefresh,
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedUpload, setSelectedUpload] = useState<UploadRecord | null>(null);

  const filteredUploads = uploads.filter((u) => {
    const matchesSearch =
      u.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (u.file_name && u.file_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (u.youtube_video_id && u.youtube_video_id.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesStatus = statusFilter === "all" ? true : u.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const formatDate = (dateStr?: string | null) => {
    if (!dateStr) return "N/A";
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString() + " " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <History className="h-6 w-6 text-red-500" />
            Upload History
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Complete audit trail of all automated and manual video uploads to YouTube. Total:{" "}
            <span className="text-slate-200 font-semibold">{total}</span>
          </p>
        </div>

        <button
          onClick={onRefresh}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-sm font-medium transition self-start md:self-auto"
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh History</span>
        </button>
      </div>

      {/* Toolbar */}
      <div className="glass-panel rounded-2xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by title, filename, or YouTube ID..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-red-500/50"
          />
        </div>

        <div className="flex items-center space-x-2">
          {["all", "uploaded", "failed", "uploading"].map((f) => (
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

      {/* Uploads Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        {filteredUploads.length === 0 ? (
          <div className="text-center py-16 text-slate-500 space-y-2">
            <History className="h-10 w-10 mx-auto text-slate-600 opacity-60" />
            <p className="text-sm font-medium">No upload records found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400 bg-slate-900/80 border-b border-slate-800">
                <tr>
                  <th className="py-3.5 px-4">YouTube Title & File</th>
                  <th className="py-3.5 px-4">YouTube ID</th>
                  <th className="py-3.5 px-4">Privacy</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filteredUploads.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-100 truncate max-w-xs sm:max-w-md">
                        {u.title}
                      </div>
                      <div className="text-xs text-slate-400 truncate">{u.file_name}</div>
                    </td>
                    <td className="py-3.5 px-4">
                      {u.youtube_video_id ? (
                        <a
                          href={`https://youtu.be/${u.youtube_video_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center text-xs font-mono text-blue-400 hover:text-blue-300 hover:underline"
                        >
                          {u.youtube_video_id}
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      ) : (
                        <span className="text-xs text-slate-500">N/A</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={u.privacy_status} />
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={u.status} />
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400 font-mono">
                      {formatDate(u.uploaded_at || u.created_at)}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedUpload(u)}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Details Modal */}
      {selectedUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fadeIn">
          <div className="glass-panel max-w-2xl w-full rounded-3xl p-6 border border-slate-700 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <FileText className="h-5 w-5 text-red-500" />
                Upload Metadata Inspector
              </h3>
              <button
                onClick={() => setSelectedUpload(null)}
                className="text-slate-400 hover:text-white text-sm px-2 py-1 rounded-lg hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
              <div>
                <label className="text-xs text-slate-400 font-semibold uppercase">Generated Title</label>
                <div className="mt-1 p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 text-sm font-medium">
                  {selectedUpload.title}
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold uppercase">Description</label>
                <div className="mt-1 p-3 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 text-xs font-mono whitespace-pre-wrap">
                  {selectedUpload.description || "No description provided."}
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold uppercase">Tags</label>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {selectedUpload.tags && selectedUpload.tags.length > 0 ? (
                    selectedUpload.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-center gap-1"
                      >
                        <Tag className="h-3 w-3 text-red-400" />
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">No tags generated</span>
                  )}
                </div>
              </div>

              {selectedUpload.error_message && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-400">
                  <div className="font-semibold flex items-center gap-1.5 mb-1">
                    <AlertCircle className="h-4 w-4" />
                    Error Trace
                  </div>
                  <pre className="whitespace-pre-wrap font-mono">{selectedUpload.error_message}</pre>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedUpload(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-semibold transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
