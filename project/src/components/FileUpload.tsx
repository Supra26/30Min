import React, { useState, useCallback } from 'react';
import { Upload, FileText, X } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onRemoveFile: () => void;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  selectedFile,
  onRemoveFile,
}) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0] && files[0].type === 'application/pdf') {
      onFileSelect(files[0]);
    }
  }, [onFileSelect]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      onFileSelect(files[0]);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {!selectedFile ? (
        <div
          className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 backdrop-blur-xl ${
            dragActive
              ? 'border-[#7B61FF] bg-[#7B61FF]/10 scale-105 shadow-[0_0_20px_rgba(123,97,255,0.3)]'
              : 'border-[#2B3A55] hover:border-[#7B61FF]/50 hover:bg-[#0B0F1A]/60 hover:shadow-[0_0_15px_rgba(123,97,255,0.2)]'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <div className="flex flex-col items-center space-y-4">
            <div className="w-16 h-16 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-2xl flex items-center justify-center shadow-lg">
              <Upload className="w-8 h-8 text-white" />
            </div>
            <div>
              <h3 className="text-xl font-semibold text-white mb-2">
                Upload Your PDF
              </h3>
              <p className="text-[#BFC9D9] mb-4">
                Drag and drop your PDF here, or click to browse
              </p>
              <label className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-[#7B61FF] to-[#5ED3F3] text-white rounded-xl font-medium cursor-pointer hover:shadow-[0_0_15px_rgba(123,97,255,0.4)] transition-all duration-200 transform hover:scale-105">
                Choose File
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[#0B0F1A]/80 backdrop-blur-xl rounded-2xl p-6 shadow-2xl border border-[#2B3A55]">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-br from-[#7B61FF] to-[#5ED3F3] rounded-xl flex items-center justify-center shadow-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{selectedFile.name}</h3>
                <p className="text-sm text-[#BFC9D9]">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={onRemoveFile}
              className="w-8 h-8 bg-[#2B3A55] rounded-full flex items-center justify-center hover:bg-[#2B3A55]/80 hover:text-white transition-colors text-[#BFC9D9]"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};