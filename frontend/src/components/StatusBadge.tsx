import React from "react";

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = "" }) => {
  const norm = status?.toLowerCase() || "unknown";

  let styles = "bg-slate-800 text-slate-400 border-slate-700";
  let dotColor = "bg-slate-400";
  let label = status;

  switch (norm) {
    case "available":
      styles = "bg-blue-950/40 text-blue-400 border-blue-500/30";
      dotColor = "bg-blue-400";
      label = "Available";
      break;
    case "downloading":
      styles = "bg-indigo-950/40 text-indigo-400 border-indigo-500/30 animate-pulse";
      dotColor = "bg-indigo-400";
      label = "Downloading";
      break;
    case "processing":
      styles = "bg-purple-950/40 text-purple-400 border-purple-500/30 animate-pulse";
      dotColor = "bg-purple-400";
      label = "AI Processing";
      break;
    case "uploading":
      styles = "bg-amber-950/40 text-amber-400 border-amber-500/30 animate-pulse";
      dotColor = "bg-amber-400";
      label = "Uploading";
      break;
    case "uploaded":
      styles = "bg-emerald-950/40 text-emerald-400 border-emerald-500/30";
      dotColor = "bg-emerald-400";
      label = "Uploaded";
      break;
    case "failed":
      styles = "bg-rose-950/40 text-rose-400 border-rose-500/30";
      dotColor = "bg-rose-400";
      label = "Failed";
      break;
    case "connected":
      styles = "bg-emerald-950/40 text-emerald-400 border-emerald-500/30";
      dotColor = "bg-emerald-400";
      label = "Connected";
      break;
    case "disconnected":
    case "not connected":
      styles = "bg-slate-800/80 text-slate-400 border-slate-700";
      dotColor = "bg-slate-500";
      label = "Disconnected";
      break;
    case "private":
      styles = "bg-slate-800 text-slate-300 border-slate-700";
      dotColor = "bg-slate-400";
      label = "Private";
      break;
    case "unlisted":
      styles = "bg-amber-950/30 text-amber-300 border-amber-500/30";
      dotColor = "bg-amber-400";
      label = "Unlisted";
      break;
    case "public":
      styles = "bg-emerald-950/30 text-emerald-300 border-emerald-500/30";
      dotColor = "bg-emerald-400";
      label = "Public";
      break;
    default:
      break;
  }

  return (
    <span
      className={`inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles} ${className}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />
      <span>{label}</span>
    </span>
  );
};
