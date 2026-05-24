import { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';
import type { ProcessedDocument } from './utils/fileProcessor';
import './index.css';

export default function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [processedDocument, setProcessedDocument] = useState<ProcessedDocument | null>(null);

  function handleFileSelect(file: File) {
    setSelectedFile(file);
    setProcessedDocument(null);
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>RTK Proxy — Phân tích tài liệu với Claude</h1>
        <p className="app-subtitle">
          Tải lên tài liệu · RTK Query xử lý nội dung · Claude trả lời câu hỏi
        </p>
      </header>

      <main className="app-main">
        <section className="app-section">
          <h2 className="section-title">1. Tải lên tài liệu</h2>
          <FileUpload onFileSelect={handleFileSelect} />
          {selectedFile && (
            <p className="file-selected">
              ✅ Đã chọn: <strong>{selectedFile.name}</strong> ({(selectedFile.size / 1024).toFixed(1)} KB)
            </p>
          )}
        </section>

        <section className="app-section">
          <h2 className="section-title">2. Đặt câu hỏi</h2>
          <ChatInterface
            file={selectedFile}
            document={processedDocument}
            onDocumentProcessed={setProcessedDocument}
          />
        </section>
      </main>

      <footer className="app-footer">
        <div className="pipeline">
          <span className="pipeline-step">File upload</span>
          <span className="pipeline-arrow">→</span>
          <span className="pipeline-step highlight">RTK Query proxy</span>
          <span className="pipeline-arrow">→</span>
          <span className="pipeline-step">Text extraction + chunking</span>
          <span className="pipeline-arrow">→</span>
          <span className="pipeline-step">Express proxy</span>
          <span className="pipeline-arrow">→</span>
          <span className="pipeline-step">Claude API</span>
        </div>
      </footer>
    </div>
  );
}
