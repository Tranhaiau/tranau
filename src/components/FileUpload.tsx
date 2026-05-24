import { useRef, useState, type DragEvent, type ChangeEvent } from 'react';
import { isSupportedFileType } from '../utils/fileProcessor';

interface Props {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export function FileUpload({ onFileSelect, disabled }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFile(file: File) {
    setError(null);
    if (!isSupportedFileType(file)) {
      setError(`Loại file "${file.type || file.name}" không được hỗ trợ. Hãy dùng .xlsx, .xls, .txt, .md, .csv, .json, .html`);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File quá lớn. Giới hạn tối đa 10 MB.');
      return;
    }
    onFileSelect(file);
  }

  function onInputChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }

  return (
    <div className="upload-wrapper">
      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={() => !disabled && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
      >
        <span className="upload-icon">📄</span>
        <p className="upload-hint">
          Kéo thả file vào đây hoặc <strong>click để chọn</strong>
        </p>
        <p className="upload-types">Hỗ trợ: .xlsx · .xls · .txt · .md · .csv · .json · .html · .xml</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.txt,.md,.csv,.json,.html,.xml,text/*,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel"
        style={{ display: 'none' }}
        onChange={onInputChange}
        disabled={disabled}
      />
      {error && <p className="upload-error">{error}</p>}
    </div>
  );
}
