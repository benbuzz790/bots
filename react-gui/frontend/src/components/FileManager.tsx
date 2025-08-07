import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Upload, Download, Trash2, File, AlertCircle, CheckCircle, X, FolderOpen } from 'lucide-react';

interface BotFileMetadata {
  filename: string;
  sizeBytes: number;
  createdAt: string;
  modifiedAt: string;
  checksum: string;
  botName?: string;
  botVersion?: string;
}

interface BotFileInfo {
  metadata: BotFileMetadata;
  isValid: boolean;
  validationErrors: string[];
  preview?: string;
}

interface FileUploadResponse {
  success: boolean;
  message: string;
  fileInfo?: BotFileInfo;
  warnings: string[];
}

interface FileListResponse {
  files: BotFileInfo[];
  totalCount: number;
  totalSizeBytes: number;
}

interface FileDeleteResponse {
  success: boolean;
  message: string;
  deletedFilename?: string;
}

interface FileManagerProps {
  onBotLoad?: (botId: string, filename: string) => void;
  onClose?: () => void;
  className?: string;
}

const FileManager: React.FC<FileManagerProps> = ({ onBotLoad, onClose, className = '' }) => {
  // Input validation
  if (onBotLoad && typeof onBotLoad !== 'function') {
    throw new Error('onBotLoad must be a function');
  }
  if (onClose && typeof onClose !== 'function') {
    throw new Error('onClose must be a function');
  }
  if (typeof className !== 'string') {
    throw new Error('className must be a string');
  }

  const [files, setFiles] = useState<BotFileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<BotFileInfo | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load files on mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/files/list');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data: FileListResponse = await response.json();
      
      // Validate response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      if (!Array.isArray(data.files)) {
        throw new Error('Files must be an array');
      }

      setFiles(data.files);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load files';
      setError(errorMessage);
      console.error('Error loading files:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleFileUpload = useCallback(async (file: File) => {
    // Input validation
    if (!(file instanceof File)) {
      throw new Error('file must be a File instance');
    }
    if (!file.name.endsWith('.bot')) {
      setError('File must have .bot extension');
      return;
    }
    if (file.size === 0) {
      setError('File cannot be empty');
      return;
    }
    if (file.size > 50_000_000) {
      setError('File too large (max 50MB)');
      return;
    }

    setUploadProgress(0);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('overwrite', 'false');

      const response = await fetch('/api/files/upload', {
        method: 'POST',
        body: formData,
      });

      const data: FileUploadResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`);
      }

      // Validate response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      if (typeof data.success !== 'boolean') {
        throw new Error('Response must have success boolean');
      }

      if (data.success) {
        await loadFiles(); // Refresh file list
        setUploadProgress(100);
        
        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
          console.warn('Upload warnings:', data.warnings);
        }
        
        setTimeout(() => setUploadProgress(null), 2000);
      } else {
        throw new Error(data.message || 'Upload failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setUploadProgress(null);
      console.error('Upload error:', err);
    }
  }, [loadFiles]);

  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      handleFileUpload(file);
    }
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [handleFileUpload]);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  }, []);

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);

    const files = Array.from(event.dataTransfer.files);
    const botFile = files.find(file => file.name.endsWith('.bot'));
    
    if (botFile) {
      handleFileUpload(botFile);
    } else {
      setError('Please drop a .bot file');
    }
  }, [handleFileUpload]);

  const handleDownload = useCallback(async (filename: string) => {
    // Input validation
    if (typeof filename !== 'string' || !filename.trim()) {
      throw new Error('filename must be a non-empty string');
    }

    try {
      const response = await fetch(`/api/files/download/${encodeURIComponent(filename)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // Create download link
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Download failed';
      setError(errorMessage);
      console.error('Download error:', err);
    }
  }, []);

  const handleDelete = useCallback(async (filename: string) => {
    // Input validation
    if (typeof filename !== 'string' || !filename.trim()) {
      throw new Error('filename must be a non-empty string');
    }

    try {
      const response = await fetch(`/api/files/delete/${encodeURIComponent(filename)}?confirm=true`, {
        method: 'DELETE',
      });

      const data: FileDeleteResponse = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`);
      }

      // Validate response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      if (typeof data.success !== 'boolean') {
        throw new Error('Response must have success boolean');
      }

      if (data.success) {
        await loadFiles(); // Refresh file list
        setDeleteConfirm(null);
      } else {
        throw new Error(data.message || 'Delete failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Delete failed';
      setError(errorMessage);
      console.error('Delete error:', err);
    }
  }, [loadFiles]);

  const handleLoadBot = useCallback(async (filename: string) => {
    // Input validation
    if (typeof filename !== 'string' || !filename.trim()) {
      throw new Error('filename must be a non-empty string');
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/files/load-bot/${encodeURIComponent(filename)}`, {
        method: 'POST',
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP ${response.status}`);
      }

      // Validate response
      if (!data || typeof data !== 'object') {
        throw new Error('Invalid response format');
      }
      if (typeof data.success !== 'boolean') {
        throw new Error('Response must have success boolean');
      }
      if (!data.bot_id || typeof data.bot_id !== 'string') {
        throw new Error('Response must have bot_id string');
      }

      if (data.success && onBotLoad) {
        onBotLoad(data.bot_id, filename);
        if (onClose) {
          onClose();
        }
      } else {
        throw new Error(data.message || 'Bot loading failed');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Bot loading failed';
      setError(errorMessage);
      console.error('Bot loading error:', err);
    } finally {
      setLoading(false);
    }
  }, [onBotLoad, onClose]);

  const formatFileSize = useCallback((bytes: number): string => {
    if (typeof bytes !== 'number' || bytes < 0) {
      return '0 B';
    }
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  }, []);

  const formatDate = useCallback((dateString: string): string => {
    if (typeof dateString !== 'string') {
      return 'Invalid date';
    }
    
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid date';
    }
  }, []);

  return (
    <div className={`bg-white rounded-lg shadow-lg ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold">Bot File Manager</h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded"
            aria-label="Close file manager"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* Upload Area */}
      <div
        className={`m-4 p-6 border-2 border-dashed rounded-lg transition-colors ${
          dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="text-center">
          <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600 mb-2">
            Drag & drop a .bot file here, or{' '}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              browse files
            </button>
          </p>
          <p className="text-xs text-gray-500">Max file size: 50MB</p>
        </div>
        
        <input
          ref={fileInputRef}
          type="file"
          accept=".bot"
          onChange={handleFileSelect}
          className="hidden"
        />
      </div>

      {/* Upload Progress */}
      {uploadProgress !== null && (
        <div className="mx-4 mb-4">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm text-gray-600">Uploading...</span>
            <span className="text-sm font-medium">{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <span className="text-sm text-red-800">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto p-1 hover:bg-red-100 rounded"
            >
              <X className="w-3 h-3 text-red-600" />
            </button>
          </div>
        </div>
      )}

      {/* File List */}
      <div className="max-h-96 overflow-y-auto">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-2" />
            <p className="text-sm text-gray-600">Loading files...</p>
          </div>
        ) : files.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <File className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No bot files found</p>
          </div>
        ) : (
          <div className="divide-y">
            {files.map((fileInfo) => (
              <div key={fileInfo.metadata.filename} className="p-4 hover:bg-gray-50">
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => setSelectedFile(selectedFile?.metadata.filename === fileInfo.metadata.filename ? null : fileInfo)}
                  title="Click to toggle preview"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <span className="font-medium text-sm truncate">
                        {fileInfo.metadata.filename}
                      </span>
                      {fileInfo.isValid ? (
                        <CheckCircle className="w-4 h-4 text-green-600 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
                      )}
                    </div>
                    
                    <div className="text-xs text-gray-500 space-y-1">
                      <div>
                        {formatFileSize(fileInfo.metadata.sizeBytes)} • {formatDate(fileInfo.metadata.modifiedAt)}
                      </div>
                      {!fileInfo.isValid && fileInfo.validationErrors.length > 0 && (
                        <div className="text-red-600">
                          Errors: {fileInfo.validationErrors.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1 ml-4">
                    <button
                      onClick={() => handleLoadBot(fileInfo.metadata.filename)}
                      disabled={!fileInfo.isValid || loading}
                      className="p-2 text-blue-600 hover:bg-blue-50 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Load bot"
                    >
                      <FolderOpen className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => handleDownload(fileInfo.metadata.filename)}
                      className="p-2 text-gray-600 hover:bg-gray-100 rounded"
                      title="Download file"
                    >
                      <Download className="w-4 h-4" />
                    </button>
                    
                    <button
                      onClick={() => setDeleteConfirm(fileInfo.metadata.filename)}
                      className="p-2 text-red-600 hover:bg-red-50 rounded"
                      title="Delete file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* File Preview */}
                {selectedFile?.metadata.filename === fileInfo.metadata.filename && fileInfo.preview && (
                  <div className="mt-3 p-3 bg-gray-50 rounded text-xs font-mono text-gray-700 max-h-32 overflow-y-auto">
                    {fileInfo.preview}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-2">Confirm Deletion</h3>
            <p className="text-gray-600 mb-4">
              Are you sure you want to delete <strong>{deleteConfirm}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileManager;
