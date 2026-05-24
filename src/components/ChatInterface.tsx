import { useState, type FormEvent } from 'react';
import { useAskAboutFileMutation, useAskAboutDocumentMutation } from '../services/claudeApi';
import type { ProcessedDocument } from '../utils/fileProcessor';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface Props {
  file: File | null;
  document: ProcessedDocument | null;
  onDocumentProcessed: (doc: ProcessedDocument) => void;
}

export function ChatInterface({ file, document, onDocumentProcessed }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const [askAboutFile, { isLoading: isProcessing }] = useAskAboutFileMutation();
  const [askAboutDocument, { isLoading: isAsking }] = useAskAboutDocumentMutation();

  const isLoading = isProcessing || isAsking;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || !file || isLoading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: question }]);

    try {
      let result;

      if (!document) {
        // First question: file hasn't been processed yet — RTK proxy reads + processes + sends
        result = await askAboutFile({ file, question }).unwrap();
        // After first processing, cache the document for follow-up questions
        const { readFileAsText, processFileContent } = await import('../utils/fileProcessor');
        const content = await readFileAsText(file);
        const processed = processFileContent({ name: file.name, content, type: file.type, size: file.size });
        onDocumentProcessed(processed);
      } else {
        // Follow-up: document already processed, send directly
        result = await askAboutDocument({ document, question }).unwrap();
      }

      setMessages((prev) => [...prev, { role: 'assistant', content: result.answer }]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : (err as { error?: string }).error ?? 'Lỗi không xác định';
      setMessages((prev) => [...prev, { role: 'assistant', content: `⚠️ Lỗi: ${msg}` }]);
    }
  }

  if (!file) {
    return (
      <div className="chat-placeholder">
        <span>Hãy tải lên một tài liệu để bắt đầu đặt câu hỏi.</span>
      </div>
    );
  }

  return (
    <div className="chat-wrapper">
      {document && (
        <div className="doc-meta">
          <span className="meta-item">📄 {document.metadata.fileName}</span>
          <span className="meta-item">🔢 {document.metadata.wordCount.toLocaleString()} từ</span>
          <span className="meta-item">🧩 {document.metadata.totalChunks} đoạn</span>
        </div>
      )}

      <div className="messages">
        {messages.length === 0 && (
          <p className="chat-hint">Hỏi bất kỳ điều gì về tài liệu của bạn.</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message message--${msg.role}`}>
            <span className="message-label">{msg.role === 'user' ? 'Bạn' : 'Claude'}</span>
            <p className="message-content">{msg.content}</p>
          </div>
        ))}
        {isLoading && (
          <div className="message message--assistant">
            <span className="message-label">Claude</span>
            <p className="message-content typing">
              {isProcessing ? 'Đang xử lý tài liệu...' : 'Đang trả lời...'}
            </p>
          </div>
        )}
      </div>

      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          className="chat-input"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Nhập câu hỏi về tài liệu..."
          disabled={isLoading}
        />
        <button className="chat-send" type="submit" disabled={isLoading || !input.trim()}>
          Gửi
        </button>
      </form>
    </div>
  );
}
