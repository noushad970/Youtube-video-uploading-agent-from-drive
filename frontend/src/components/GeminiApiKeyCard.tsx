import React, { useState, useEffect, useRef } from "react";
import {
  Key,
  Sparkles,
  ExternalLink,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Save,
  RefreshCw,
  HelpCircle,
  ChevronDown,
  ChevronUp,
  Check,
  Copy,
  Zap,
} from "lucide-react";
import { apiClient } from "../services/api";

interface GeminiApiKeyCardProps {
  apiKey?: string | null;
  onSaveKey: (newKey: string) => Promise<void>;
  compact?: boolean;
  className?: string;
  defaultOpenGuide?: boolean;
}

export const GeminiApiKeyCard: React.FC<GeminiApiKeyCardProps> = ({
  apiKey = "",
  onSaveKey,
  compact = false,
  className = "",
  defaultOpenGuide = false,
}) => {
  const [inputValue, setInputValue] = useState<string>(apiKey || "");
  const [showKey, setShowKey] = useState<boolean>(false);
  const [saveStatus, setSaveStatus] = useState<"idle" | "typing" | "saving" | "saved" | "error">("idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verifyResult, setVerifyResult] = useState<{ valid: boolean; message: string; model: string } | null>(null);
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(defaultOpenGuide || !apiKey);
  const [hasCopiedUrl, setHasCopiedUrl] = useState<boolean>(false);

  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isInitialMount = useRef<boolean>(true);

  // Sync external apiKey change into local input if not currently user typing
  useEffect(() => {
    if (apiKey !== undefined && apiKey !== null) {
      if (saveStatus !== "typing" && saveStatus !== "saving") {
        setInputValue(apiKey);
      }
    }
  }, [apiKey]);

  // Handle auto-save with 700ms debounce
  useEffect(() => {
    // Avoid auto-saving on initial component mount
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }

    // If input matches saved apiKey, no need to auto-save
    if (inputValue === (apiKey || "")) {
      return;
    }

    setSaveStatus("typing");
    setStatusMessage("Unsaved changes...");

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    debounceTimerRef.current = setTimeout(async () => {
      await executeSave(inputValue, true);
    }, 750);

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [inputValue]);

  const executeSave = async (keyToSave: string, isAuto: boolean = false) => {
    try {
      setSaveStatus("saving");
      setStatusMessage(isAuto ? "Auto-saving..." : "Saving key...");
      await onSaveKey(keyToSave.trim());
      setSaveStatus("saved");
      setStatusMessage(isAuto ? "Auto-saved successfully ✓" : "Saved successfully ✓");

      // Automatically verify key if string is provided
      if (keyToSave.trim().length > 10) {
        runVerification(keyToSave.trim());
      } else if (!keyToSave.trim()) {
        setVerifyResult(null);
      }

      setTimeout(() => {
        setSaveStatus((prev) => (prev === "saved" ? "idle" : prev));
      }, 3500);
    } catch (err: any) {
      setSaveStatus("error");
      setStatusMessage(err?.message || "Failed to save key");
    }
  };

  const runVerification = async (keyToTest?: string) => {
    const key = (keyToTest !== undefined ? keyToTest : inputValue).trim();
    if (!key) {
      setVerifyResult({
        valid: false,
        message: "Please enter your Gemini API key before testing.",
        model: "gemini-3.5-flash-lite",
      });
      return;
    }

    setIsVerifying(true);
    try {
      const res = await apiClient.verifyGeminiKey({
        api_key: key,
        model: "gemini-3.5-flash-lite",
      });
      setVerifyResult(res);
    } catch (e: any) {
      setVerifyResult({
        valid: false,
        message: e?.response?.data?.message || e?.message || "Network error verifying key.",
        model: "gemini-3.5-flash-lite",
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleCopyAiStudioUrl = () => {
    navigator.clipboard.writeText("https://aistudio.google.com/api-keys");
    setHasCopiedUrl(true);
    setTimeout(() => setHasCopiedUrl(false), 2000);
  };

  const isKeyConfigured = Boolean(inputValue && inputValue.trim().length > 10);

  return (
    <div
      className={`relative overflow-hidden rounded-2xl border transition-all duration-300 ${
        isKeyConfigured
          ? "bg-gradient-to-br from-slate-900/95 via-slate-900/80 to-purple-950/20 border-purple-500/30 shadow-lg shadow-purple-950/20"
          : "bg-gradient-to-br from-slate-900/95 via-amber-950/10 to-slate-900/90 border-amber-500/40 shadow-xl shadow-amber-950/20"
      } p-5 sm:p-6 ${className}`}
    >
      {/* Background ambient glow */}
      <div className="absolute -right-16 -top-16 w-52 h-52 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2.5 rounded-xl border ${
            isKeyConfigured
              ? "bg-purple-500/15 border-purple-500/30 text-purple-400"
              : "bg-amber-500/20 border-amber-500/40 text-amber-300"
          }`}>
            {isKeyConfigured ? <Key className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5 animate-pulse" />}
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-bold text-white tracking-wide">
                Google Gemini API Key
              </h3>
              {isKeyConfigured ? (
                <span className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-300">
                  BYOK • Active
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider font-bold bg-amber-500/25 border border-amber-500/50 text-amber-300 animate-pulse">
                  ⚠️ API Key Required First
                </span>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Power automated title, rich description, 25 SEO tags & 16:9 thumbnail generation.
            </p>
          </div>
        </div>

        {/* Action button to open Google AI Studio */}
        <div className="flex items-center gap-2">
          <a
            href="https://aistudio.google.com/api-keys"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-md shadow-purple-600/20 active:scale-95 transition"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Get Free Gemini Key</span>
            <ExternalLink className="h-3 w-3 ml-0.5 opacity-80" />
          </a>

          <button
            type="button"
            onClick={() => setIsGuideOpen(!isGuideOpen)}
            className="px-2.5 py-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-slate-300 text-xs font-medium flex items-center gap-1 transition"
            title="Toggle How to Use Guide"
          >
            <HelpCircle className="h-3.5 w-3.5 text-purple-400" />
            <span className="hidden sm:inline">How to use</span>
            {isGuideOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
          </button>
        </div>
      </div>

      {/* Prominent Warning Banner when no key is provided */}
      {!isKeyConfigured && (
        <div className="mb-4 p-4 rounded-xl bg-gradient-to-r from-amber-950/80 via-red-950/60 to-amber-950/80 border-2 border-amber-500/70 text-amber-200 shadow-lg shadow-amber-950/30 animate-fadeIn">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30 shrink-0 mt-0.5">
              <AlertTriangle className="h-5 w-5 text-amber-400 animate-pulse" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h4 className="text-sm font-bold text-white tracking-wide">
                  ⚠️ WARNING: You must give your Gemini API key first!
                </h4>
                <span className="text-[10px] px-2 py-0.5 rounded font-extrabold uppercase bg-red-500/20 text-red-300 border border-red-500/40">
                  Required First
                </span>
              </div>
              <p className="text-xs text-amber-200/90 mt-1 leading-relaxed">
                Video uploading and AI metadata generation are <strong>currently disabled</strong> until you provide your Gemini API key. Please create your free key in Google AI Studio, paste it below, and the app will auto-save it immediately!
              </p>
              <div className="mt-2.5 flex flex-wrap items-center gap-2">
                <a
                  href="https://aistudio.google.com/api-keys"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold transition shadow"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                  <span>Create Free API Key (Google AI Studio) ↗</span>
                </a>
                <span className="text-[11px] text-amber-300/80 italic">
                  * 100% free with zero API costs
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Gemini API Input & Auto-Save controls */}
      <div className="space-y-3">
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <span>Your Gemini API Key</span>
              {!isKeyConfigured ? (
                <span className="text-[10px] text-amber-400 font-bold bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/30">
                  ⚠️ REQUIRED FIRST
                </span>
              ) : (
                <span className="text-[10px] text-slate-500 font-normal">(Auto-saves on typing)</span>
              )}
            </label>

            {/* Auto-save status feedback */}
            <div className="flex items-center text-[11px] font-medium space-x-1.5">
              {saveStatus === "typing" && (
                <span className="text-amber-400 flex items-center gap-1 animate-pulse">
                  <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                  Auto-saving soon...
                </span>
              )}
              {saveStatus === "saving" && (
                <span className="text-blue-400 flex items-center gap-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  Saving...
                </span>
              )}
              {saveStatus === "saved" && (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  {statusMessage || "Auto-saved successfully ✓"}
                </span>
              )}
              {saveStatus === "error" && (
                <span className="text-rose-400 flex items-center gap-1">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {statusMessage || "Error saving"}
                </span>
              )}
              {saveStatus === "idle" && isKeyConfigured && (
                <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                  <Check className="h-3 w-3 text-emerald-400" />
                  Key saved in app
                </span>
              )}
            </div>
          </div>

          <div className="relative flex items-center">
            <input
              type={showKey ? "text" : "password"}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={
                !isKeyConfigured
                  ? "⚠️ Warning: Paste your Gemini API key first to enable uploads (e.g. AIzaSy...)"
                  : "Paste your Gemini API key here (e.g. AIzaSy...)"
              }
              className={`w-full pl-3.5 pr-28 py-2.5 rounded-xl bg-slate-950/90 border text-sm text-slate-100 placeholder-slate-500 font-mono transition focus:outline-none ${
                isKeyConfigured
                  ? "border-slate-700/80 focus:border-purple-500 focus:ring-1 focus:ring-purple-500/50"
                  : "border-amber-500 ring-2 ring-amber-500/20 focus:border-amber-400 focus:ring-amber-500/40"
              }`}
            />

            {/* Inline Input Controls */}
            <div className="absolute right-2 flex items-center space-x-1">
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
                title={showKey ? "Hide API key" : "Show API key"}
              >
                {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>

              <button
                type="button"
                onClick={() => executeSave(inputValue, false)}
                disabled={saveStatus === "saving"}
                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-semibold active:scale-95 transition disabled:opacity-50"
                title="Save immediately"
              >
                <Save className="h-3 w-3 text-purple-400" />
                <span>Save</span>
              </button>

              <button
                type="button"
                onClick={() => runVerification()}
                disabled={isVerifying || !inputValue.trim()}
                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 border border-purple-500/40 text-purple-200 text-xs font-semibold active:scale-95 transition disabled:opacity-40"
                title="Test with Gemini 3.5"
              >
                <Zap className={`h-3 w-3 text-amber-400 ${isVerifying ? "animate-spin" : ""}`} />
                <span>{isVerifying ? "Testing..." : "Test"}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Verification Status Banner */}
        {verifyResult && (
          <div
            className={`p-3 rounded-xl border flex items-start space-x-2.5 text-xs animate-fadeIn ${
              verifyResult.valid
                ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-200"
                : "bg-rose-950/40 border-rose-500/40 text-rose-200"
            }`}
          >
            {verifyResult.valid ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-400 shrink-0 mt-0.5" />
            )}
            <div className="flex-1">
              <span className="font-semibold">{verifyResult.valid ? "Verified & Ready: " : "Verification Issue: "}</span>
              <span>{verifyResult.message}</span>
            </div>
          </div>
        )}

        {/* Missing key reminder banner if no key */}
        {!isKeyConfigured && (
          <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-xs text-amber-300 flex items-center justify-between gap-3">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-amber-400 shrink-0" />
              <span>
                <strong>Gemini API key is required</strong> to run automated video uploads with AI metadata and thumbnails.
              </span>
            </div>
            <a
              href="https://aistudio.google.com/api-keys"
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 font-semibold shrink-0 transition"
            >
              Get Free Key →
            </a>
          </div>
        )}
      </div>

      {/* "How to Use" Step-by-Step Guide (Expandable / Collapsible) */}
      {isGuideOpen && (
        <div className="mt-5 pt-4 border-t border-slate-800/80 animate-fadeIn space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-purple-400" />
              How to Use & Get Your Free Gemini API Key (Step-by-Step)
            </h4>
            <button
              type="button"
              onClick={handleCopyAiStudioUrl}
              className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition"
            >
              <Copy className="h-3 w-3" />
              <span>{hasCopiedUrl ? "Copied URL!" : "Copy Link"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            {/* Step 1 */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-purple-400">Step 1</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-300 font-mono">1 Click</span>
                </div>
                <h5 className="font-semibold text-slate-200 mb-1">Open Google AI Studio</h5>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Click the button below to visit Google's official API key manager.
                </p>
              </div>
              <a
                href="https://aistudio.google.com/api-keys"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-3 block text-center py-1.5 rounded-lg bg-slate-800 hover:bg-purple-900/40 text-purple-300 border border-slate-700/80 text-[11px] font-semibold transition"
              >
                aistudio.google.com/api-keys ↗
              </a>
            </div>

            {/* Step 2 */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-blue-400">Step 2</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 font-mono">Free</span>
                </div>
                <h5 className="font-semibold text-slate-200 mb-1">Click "Create API Key"</h5>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Sign in with any standard Google account. Click the blue <strong>"Create API key"</strong> button and select or create a project.
                </p>
              </div>
              <div className="mt-3 text-[10px] text-slate-500 italic">
                * Google provides a generous free tier with 0 subscription fees.
              </div>
            </div>

            {/* Step 3 */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-amber-400">Step 3</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300 font-mono">Copy</span>
                </div>
                <h5 className="font-semibold text-slate-200 mb-1">Copy Your Secret Key</h5>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Click the copy icon on the dialog to copy your key string. It will look like:
                </p>
              </div>
              <div className="mt-3 px-2 py-1 rounded bg-slate-900 text-amber-300/80 font-mono text-[10px] truncate border border-slate-800">
                AIzaSyDx9B...
              </div>
            </div>

            {/* Step 4 */}
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-bold text-emerald-400">Step 4</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 font-mono">Auto-Save</span>
                </div>
                <h5 className="font-semibold text-slate-200 mb-1">Paste & Start Uploading</h5>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  Paste the key into the input above. The app <strong>auto-saves</strong> immediately! You are ready to upload.
                </p>
              </div>
              <div className="mt-3 flex items-center gap-1 text-[11px] text-emerald-400 font-semibold">
                <Check className="h-3 w-3" />
                <span>Zero cost to server owner</span>
              </div>
            </div>
          </div>

          {/* Drive Video Title & Today's Upload Date Feature Notice */}
          <div className="p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs text-purple-200 flex items-start gap-3">
            <Sparkles className="h-4 w-4 text-purple-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-white">💡 Drive Video Title & Today's Upload Date Notice:</span>
              <p className="text-[11px] text-slate-300 leading-relaxed">
                All YouTube video details (AI-polished title, standard in-depth description, 18–25 SEO tags, and 16:9 thumbnail) are generated directly based on your <strong>Google Drive video title</strong>. The more detailed and descriptive your Drive title is, the more accurate and high-converting the generated title, description, and tags will be! The upload date is automatically set to <strong>today</strong>.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
