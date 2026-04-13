import React from 'react';

interface FileUploaderProps {
  label: string;
  accept: string;
  multiple?: boolean;
  files: string[];
}

const FileUploader: React.FC<FileUploaderProps> = ({ label, accept, multiple = true, files }) => {
  return (
    <div className="field-group">
      <label>{label}</label>
      <div className="file-uploader">
        <div className="file-uploader-icon">📁</div>
        <div className="file-uploader-text">
          Kéo thả file vào đây hoặc <strong>nhấn để chọn</strong>
        </div>
        <div className="file-uploader-subtext">
          {multiple ? 'Chấp nhận nhiều file' : 'Chọn 1 file'} ({accept})
        </div>
      </div>
      {files.length > 0 && (
        <div className="file-list">
          {files.map((f, i) => (
            <div className="file-chip" key={i}>
              📄 {f}
              <span className="file-chip-remove">×</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUploader;
