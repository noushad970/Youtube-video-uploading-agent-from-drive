export interface AuthStatus {
  is_authenticated: boolean;
  email?: string | null;
  name?: string | null;
  picture?: string | null;
  token_expiry?: string | null;
  scopes?: string | null;
  has_drive_scope: boolean;
  has_youtube_scope: boolean;
}

export interface DriveFolder {
  id?: number;
  folder_id: string;
  folder_name: string;
  is_selected: boolean;
  created_at?: string;
}

export interface VideoItem {
  id: number;
  drive_file_id: string;
  file_name: string;
  mime_type: string;
  size: number;
  drive_folder_id?: string | null;
  status: "available" | "downloading" | "processing" | "uploading" | "uploaded" | "failed";
  local_path?: string | null;
  duration?: number | null;
  resolution?: string | null;
  fps?: string | null;
  codec?: string | null;
  created_at: string;
  updated_at: string;
  youtube_video_id?: string | null;
}

export interface VideoListResponse {
  total: number;
  uploaded_count: number;
  remaining_count: number;
  videos: VideoItem[];
}

export interface UploadRecord {
  id: number;
  video_id: number;
  youtube_video_id?: string | null;
  title: string;
  description?: string | null;
  tags?: string[] | null;
  category_id: string;
  privacy_status: "private" | "unlisted" | "public";
  status: "pending" | "uploading" | "uploaded" | "failed";
  retry_count: number;
  error_message?: string | null;
  uploaded_at?: string | null;
  created_at: string;
  updated_at: string;
  thumbnail_path?: string | null;
  file_name?: string | null;
  drive_file_id?: string | null;
}

export interface UploadListResponse {
  total: number;
  items: UploadRecord[];
}

export interface AgentSettings {
  id?: number;
  enabled: boolean;
  interval_minutes: number;
  privacy_status: string;
  category_id: string;
  generate_title: boolean;
  generate_description: boolean;
  generate_tags: boolean;
  generate_thumbnail?: boolean;
  ai_provider?: "gemini" | "ollama";
  gemini_api_key?: string;
  gemini_model?: string;
  gemini_image_model?: string;
  ollama_model: string;
  max_retries: number;
  delete_after_upload: boolean;
  fallback_if_ai_unavailable: boolean;
  updated_at?: string;
}

export interface AgentStatus {
  is_running: boolean;
  is_scheduler_running: boolean;
  is_job_active: boolean;
  google_connected: boolean;
  youtube_connected: boolean;
  drive_connected: boolean;
  ollama_connected: boolean;
  selected_folder_name?: string | null;
  selected_folder_id?: string | null;
  total_videos: number;
  uploaded_videos: number;
  remaining_videos: number;
  last_upload_at?: string | null;
  next_scheduled_run?: string | null;
  last_run_status?: string | null;
  last_run_error?: string | null;
}

export interface LogEntry {
  id: number;
  level: "INFO" | "WARNING" | "ERROR";
  message: string;
  details?: string | null;
  created_at: string;
}

export interface LogListResponse {
  total: number;
  logs: LogEntry[];
}

export interface YouTubeChannel {
  id: string;
  title: string;
  description?: string;
  custom_url?: string;
  published_at?: string;
  thumbnail_url?: string;
  subscriber_count?: string;
  video_count?: string;
  view_count?: string;
}
