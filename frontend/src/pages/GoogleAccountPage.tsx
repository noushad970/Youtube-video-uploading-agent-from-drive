import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Youtube,
  HardDrive,
  LogOut,
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Key,
  Users,
  Eye,
  Video,
} from "lucide-react";
import { AuthStatus, YouTubeChannel } from "../types";
import { apiClient } from "../services/api";

interface GoogleAccountPageProps {
  auth: AuthStatus | null;
  onConnectGoogle: () => void;
  onDisconnectGoogle: () => void;
}

export const GoogleAccountPage: React.FC<GoogleAccountPageProps> = ({
  auth,
  onConnectGoogle,
  onDisconnectGoogle,
}) => {
  const [channel, setChannel] = useState<YouTubeChannel | null>(null);
  const [isLoadingChannel, setIsLoadingChannel] = useState(false);

  useEffect(() => {
    if (auth?.is_authenticated && auth.has_youtube_scope) {
      setIsLoadingChannel(true);
      apiClient
        .getChannel()
        .then((data) => setChannel(data))
        .catch(() => setChannel(null))
        .finally(() => setIsLoadingChannel(false));
    }
  }, [auth]);

  return (
    <div className="space-y-8 animate-fadeIn max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-red-500" />
          Google Account & Channel
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your connected Google credentials and view authorized YouTube Channel details.
        </p>
      </div>

      {/* Account Profile Card */}
      <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="flex items-center space-x-4">
            {auth?.picture ? (
              <img
                src={auth.picture}
                alt="Avatar"
                className="h-16 w-16 rounded-2xl ring-2 ring-red-500/30 object-cover"
              />
            ) : (
              <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-500 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-red-500/20">
                {auth?.email ? auth.email[0].toUpperCase() : "G"}
              </div>
            )}

            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white">{auth?.name || "Google User"}</h2>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${
                    auth?.is_authenticated
                      ? "bg-emerald-950/40 text-emerald-400 border-emerald-500/30"
                      : "bg-slate-800 text-slate-400 border-slate-700"
                  }`}
                >
                  {auth?.is_authenticated ? "Connected" : "Not Linked"}
                </span>
              </div>
              <p className="text-sm text-slate-400 font-mono mt-0.5">{auth?.email || "No account linked"}</p>
            </div>
          </div>

          <div>
            {auth?.is_authenticated ? (
              <button
                onClick={onDisconnectGoogle}
                className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-rose-950/40 text-rose-400 border border-rose-500/30 font-medium text-sm transition"
              >
                <LogOut className="h-4 w-4" />
                <span>Disconnect Account</span>
              </button>
            ) : (
              <button
                onClick={onConnectGoogle}
                className="flex items-center space-x-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-semibold text-sm shadow-lg shadow-red-600/30 transition active:scale-95"
              >
                <Youtube className="h-5 w-5" />
                <span>Connect Google Account</span>
              </button>
            )}
          </div>
        </div>

        {/* Granted Scopes Checklist */}
        <div className="pt-6 border-t border-slate-800/80">
          <h3 className="text-xs uppercase tracking-wider font-semibold text-slate-400 mb-3">
            Authorized Permissions (OAuth 2.0 Scopes)
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <HardDrive className="h-4 w-4 text-blue-400" />
                <span className="text-sm text-slate-200">Google Drive Read-only Access</span>
              </div>
              {auth?.has_drive_scope ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertCircle className="h-4 w-4 text-slate-600" />
              )}
            </div>

            <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center space-x-2.5">
                <Youtube className="h-4 w-4 text-red-400" />
                <span className="text-sm text-slate-200">YouTube Video Upload & Management</span>
              </div>
              {auth?.has_youtube_scope ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              ) : (
                <AlertCircle className="h-4 w-4 text-slate-600" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* YouTube Channel Metadata Box */}
      {channel && (
        <div className="glass-panel rounded-3xl p-6 sm:p-8 border border-slate-800 space-y-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 rounded-xl bg-red-600/10 text-red-500">
                <Youtube className="h-6 w-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-white">{channel.title}</h2>
                <p className="text-xs text-slate-400">{channel.custom_url || channel.id}</p>
              </div>
            </div>
            <a
              href={`https://youtube.com/channel/${channel.id}`}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-red-400 hover:text-red-300 font-medium flex items-center gap-1"
            >
              Open on YouTube <ExternalLink className="h-3.5 w-3.5" />
            </a>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center space-x-3">
              <Users className="h-5 w-5 text-blue-400" />
              <div>
                <div className="text-lg font-bold text-white">{channel.subscriber_count || "0"}</div>
                <div className="text-xs text-slate-400">Subscribers</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center space-x-3">
              <Video className="h-5 w-5 text-emerald-400" />
              <div>
                <div className="text-lg font-bold text-white">{channel.video_count || "0"}</div>
                <div className="text-xs text-slate-400">Published Videos</div>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center space-x-3">
              <Eye className="h-5 w-5 text-purple-400" />
              <div>
                <div className="text-lg font-bold text-white">{channel.view_count || "0"}</div>
                <div className="text-xs text-slate-400">Total Views</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Google Cloud Setup Info */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-3 text-sm text-slate-400">
        <h4 className="font-bold text-slate-200 flex items-center gap-2">
          <Key className="h-4 w-4 text-amber-400" />
          Google Cloud Setup Notes
        </h4>
        <p className="text-xs leading-relaxed">
          To enable OAuth authentication, create OAuth 2.0 Web Client credentials in your Google Cloud Console,
          enable <strong>Google Drive API</strong> and <strong>YouTube Data API v3</strong>, and set the Authorized Redirect URI to{" "}
          <code className="px-1.5 py-0.5 rounded bg-slate-900 font-mono text-slate-300">
            http://localhost:8000/api/auth/google/callback
          </code>
        </p>
      </div>
    </div>
  );
};
