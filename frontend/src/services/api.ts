import axios from "axios";
import {
  AuthStatus,
  DriveFolder,
  VideoListResponse,
  UploadListResponse,
  AgentSettings,
  AgentStatus,
  LogListResponse,
  YouTubeChannel,
  VideoItem,
} from "../types";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export const apiClient = {
  // Auth
  getAuthUrl: async (redirect = false): Promise<{ authorization_url: string }> => {
    const res = await api.get(`/auth/google?redirect=${redirect}`);
    return res.data;
  },
  getAuthStatus: async (): Promise<AuthStatus> => {
    const res = await api.get("/auth/status");
    return res.data;
  },
  disconnectGoogle: async (): Promise<{ success: boolean; message: string }> => {
    const res = await api.post("/auth/disconnect");
    return res.data;
  },

  // Drive
  getDriveFolders: async (): Promise<DriveFolder[]> => {
    const res = await api.get("/drive/folders");
    return res.data;
  },
  getDriveVideos: async (folderId?: string): Promise<{ folder_id: string; total: number; videos: any[] }> => {
    const res = await api.get("/drive/videos", { params: { folder_id: folderId } });
    return res.data;
  },
  selectFolder: async (folderId: string, folderName?: string): Promise<DriveFolder> => {
    const res = await api.post("/drive/select-folder", {
      folder_id: folderId,
      folder_name: folderName,
    });
    return res.data;
  },

  // Videos
  getVideos: async (params?: {
    folder_id?: string;
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<VideoListResponse> => {
    const res = await api.get("/videos", { params });
    return res.data;
  },
  resetVideo: async (videoId: number): Promise<VideoItem> => {
    const res = await api.post(`/videos/${videoId}/reset`);
    return res.data;
  },
  syncVideos: async (): Promise<{ success: boolean; count: number; folder_name: string }> => {
    const res = await api.post("/videos/sync");
    return res.data;
  },

  // YouTube
  getChannel: async (): Promise<YouTubeChannel> => {
    const res = await api.get("/youtube/channel");
    return res.data;
  },
  manualUpload: async (payload: {
    video_id?: number;
    drive_file_id?: string;
    title?: string;
    description?: string;
    tags?: string[];
    privacy_status?: string;
    category_id?: string;
  }) => {
    const res = await api.post("/youtube/upload", payload);
    return res.data;
  },

  // Uploads History
  getUploads: async (params?: {
    status?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<UploadListResponse> => {
    const res = await api.get("/uploads", { params });
    return res.data;
  },

  // Settings
  getSettings: async (): Promise<AgentSettings> => {
    const res = await api.get("/settings");
    return res.data;
  },
  updateSettings: async (settings: Partial<AgentSettings>): Promise<AgentSettings> => {
    const res = await api.put("/settings", settings);
    return res.data;
  },

  // Agent Control
  getAgentStatus: async (): Promise<AgentStatus> => {
    const res = await api.get("/agent/status");
    return res.data;
  },
  startAgent: async (): Promise<{ success: boolean; message: string }> => {
    const res = await api.post("/agent/start");
    return res.data;
  },
  stopAgent: async (): Promise<{ success: boolean; message: string }> => {
    const res = await api.post("/agent/stop");
    return res.data;
  },
  uploadNow: async (): Promise<{
    success: boolean;
    message: string;
    drive_file_id?: string;
    file_name?: string;
    youtube_video_id?: string;
    title?: string;
    status?: string;
    error?: string;
  }> => {
    const res = await api.post("/agent/upload-now");
    return res.data;
  },

  // Logs
  getLogs: async (params?: {
    level?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }): Promise<LogListResponse> => {
    const res = await api.get("/logs", { params });
    return res.data;
  },
  clearLogs: async (): Promise<{ success: boolean; message: string }> => {
    const res = await api.delete("/logs");
    return res.data;
  },
};
