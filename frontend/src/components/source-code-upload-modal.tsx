"use client";

import React, { useState } from "react";
import { Upload, X, FileCode, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { uploadCodeForAnalysis } from "../lib/api";

interface SourceCodeUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (sessionId: string) => void;
}

export const SourceCodeUploadModal: React.FC<SourceCodeUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setSelectedFile(e.target.files[0]);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const res = await uploadCodeForAnalysis(selectedFile);
      setSuccessMessage(`Successfully ingested & executed ${res.filename}!`);
      setTimeout(() => {
        onUploadSuccess(res.session_id);
        onClose();
        setSelectedFile(null);
        setSuccessMessage(null);
      }, 1000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-bg-surface border-2 border-border-strong shadow-truth w-full max-w-lg overflow-hidden relative text-text-primary">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-strong bg-bg-surface">
          <div className="flex items-center gap-2">
            <FileCode size={20} className="text-text-primary" />
            <h3 className="font-display font-bold text-sm uppercase tracking-wider">
              Upload Python Agent Workflow
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-text-secondary hover:text-text-primary border border-border-subtle hover:bg-bg-canvas transition-colors"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">
          <p className="text-xs text-text-secondary font-sans leading-relaxed">
            Upload any Python agent workflow (`.py`). TraceMind will automatically execute your file in a real sandbox, reconstruct its causal execution graph, surface runtime errors, and generate exact 1-line git-diff typo fixes.
          </p>

          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-border-strong hover:border-text-primary bg-bg-canvas p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-2"
          >
            <input
              type="file"
              accept=".py,.txt,.json"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload-input"
            />
            <label htmlFor="file-upload-input" className="cursor-pointer flex flex-col items-center">
              <Upload size={28} className="text-text-secondary mb-2" />
              <span className="font-display font-bold text-xs uppercase tracking-wider text-text-primary">
                {selectedFile ? selectedFile.name : "Choose or drag a Python file"}
              </span>
              <span className="text-[11px] text-text-secondary font-mono mt-1">
                {selectedFile ? `${(selectedFile.size / 1024).toFixed(1)} KB` : "Supports .py, failing_agent.py, working_agent.py"}
              </span>
            </label>
          </div>

          {error && (
            <div className="p-3 border border-color-root-cause bg-red-950/20 text-color-root-cause text-xs font-mono flex items-center gap-2">
              <AlertCircle size={16} className="shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="p-3 border border-[#10B981] bg-emerald-950/20 text-[#10B981] text-xs font-mono flex items-center gap-2">
              <CheckCircle2 size={16} className="shrink-0" />
              <span>{successMessage}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-border-strong bg-bg-canvas">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-border-subtle hover:bg-bg-surface font-display font-bold text-xs uppercase transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleUpload}
            disabled={!selectedFile || isUploading}
            className="px-5 py-2 bg-text-primary text-bg-surface font-display font-bold text-xs uppercase border border-border-strong shadow-[2px_2px_0px_0px_#171717] hover:translate-y-[1px] hover:translate-x-[1px] hover:shadow-none transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isUploading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                <span>Executing Sandbox...</span>
              </>
            ) : (
              <>
                <Upload size={14} />
                <span>Analyze File</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
