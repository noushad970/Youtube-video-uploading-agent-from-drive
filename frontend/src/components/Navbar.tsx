import React from "react";
import {
  LayoutDashboard,
  Video,
  History,
  Settings as SettingsIcon,
  ShieldCheck,
  Terminal,
  Play,
  Pause,
  UploadCloud,
  Youtube,
} from "lucide-react";
import { AgentStatus, AuthStatus } from "../types";

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  status: AgentStatus | null;
  auth: AuthStatus | null;
  onToggleAgent: () => void;
  onUploadNow: () => void;
  isUploading: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  status,
  auth,
  onToggleAgent,
  onUploadNow,
  isUploading,
}) => {
  const tabs = [
    { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
    { id: "videos", label: "Videos", icon: Video },
    { id: "uploads", label: "Upload History", icon: History },
    { id: "settings", label: "Settings", icon: SettingsIcon },
    { id: "account", label: "Google Account", icon: ShieldCheck },
    { id: "logs", label: "Logs", icon: Terminal },
  ];

  return (
    <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 px-4 lg:px-8 py-3.5">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab("dashboard")}>
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center shadow-lg shadow-red-500/20">
            <Youtube className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">YouTube AI Agent</span>
              <span className="text-[10px] uppercase tracking-wider font-semibold bg-red-500/10 text-red-400 border border-red-500/20 px-1.5 py-0.5 rounded">
                v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">Autonomous Google Drive to YouTube Pipeline</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center space-x-1 bg-slate-900/90 p-1 rounded-xl border border-slate-800">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-red-600/15 text-red-400 border border-red-500/30 shadow-sm"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Global Action Buttons */}
        <div className="flex items-center space-x-3">
          {/* Upload Now Button */}
          <button
            onClick={onUploadNow}
            disabled={isUploading}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all duration-200 shadow-md ${
              isUploading
                ? "bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700"
                : "bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white shadow-red-600/20 hover:shadow-red-600/40 active:scale-[0.98]"
            }`}
          >
            <UploadCloud className={`h-4 w-4 ${isUploading ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">{isUploading ? "Uploading..." : "Upload Now"}</span>
          </button>

          {/* Start / Pause Agent Toggle */}
          <button
            onClick={onToggleAgent}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-sm font-semibold border transition-all duration-200 ${
              status?.is_running
                ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/30 hover:bg-emerald-900/40"
                : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800 hover:text-white"
            }`}
          >
            {status?.is_running ? (
              <>
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="hidden sm:inline">Agent: Running</span>
                <Pause className="h-3.5 w-3.5 ml-1 text-emerald-400" />
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                <span className="hidden sm:inline">Agent: Paused</span>
                <Play className="h-3.5 w-3.5 ml-1 text-slate-400" />
              </>
            )}
          </button>

          {/* Account profile icon / pill */}
          <button
            onClick={() => setActiveTab("account")}
            className="flex items-center space-x-2 p-1.5 sm:px-3 sm:py-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition"
          >
            {auth?.is_authenticated && auth.picture ? (
              <img src={auth.picture} alt="Profile" className="h-6 w-6 rounded-full ring-1 ring-red-500/40" />
            ) : (
              <div className="h-6 w-6 rounded-full bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-300">
                {auth?.email ? auth.email[0].toUpperCase() : "G"}
              </div>
            )}
            <span className="text-xs font-medium text-slate-300 hidden xl:inline max-w-[120px] truncate">
              {auth?.email || "Connect Google"}
            </span>
          </button>
        </div>
      </div>

      {/* Mobile Navigation bar */}
      <div className="flex md:hidden items-center justify-around mt-3 pt-2 border-t border-slate-800/60 overflow-x-auto gap-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex flex-col items-center py-1 px-2.5 rounded-lg text-[11px] font-medium transition ${
                isActive ? "text-red-400 bg-red-500/10" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Icon className="h-4 w-4 mb-0.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
};
