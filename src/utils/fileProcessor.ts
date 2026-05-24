export interface RawFileContent {
  name: string;
  content: string;
  type: string;
  size: number;
}

export interface ProcessedDocument {
  chunks: string[];
  metadata: {
    fileName: string;
    fileType: string;
    totalChunks: number;
    wordCount: number;
    charCount: number;
    processedAt: string;
  };
}

const CHUNK_SIZE = 2000;
const CHUNK_OVERLAP = 200;

const SUPPORTED_TYPES = [
  'text/plain',
  'text/markdown',
  'text/csv',
  'text/html',
  'application/json',
  'application/xml',
  'text/xml',
];

export function isSupportedFileType(file: File): boolean {
  return (
    SUPPORTED_TYPES.includes(file.type) ||
    file.name.endsWith('.md') ||
    file.name.endsWith('.txt') ||
    file.name.endsWith('.csv') ||
    file.name.endsWith('.json')
  );
}

export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target?.result as string);
    reader.onerror = () => reject(new Error('Không thể đọc file'));
    reader.readAsText(file, 'UTF-8');
  });
}

function extractText(raw: RawFileContent): string {
  if (raw.type === 'application/json') {
    try {
      const parsed: unknown = JSON.parse(raw.content);
      return JSON.stringify(parsed, null, 2);
    } catch {
      return raw.content;
    }
  }

  if (raw.type === 'text/html' || raw.type === 'application/xml' || raw.type === 'text/xml') {
    return raw.content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
  }

  return raw.content;
}

function chunkText(text: string): string[] {
  if (text.length <= CHUNK_SIZE) return [text];

  const chunks: string[] = [];
  let start = 0;

  while (start < text.length) {
    let end = Math.min(start + CHUNK_SIZE, text.length);

    if (end < text.length) {
      const paragraphBreak = text.lastIndexOf('\n\n', end);
      if (paragraphBreak > start + CHUNK_SIZE / 2) {
        end = paragraphBreak;
      } else {
        const sentenceBreak = text.lastIndexOf('. ', end);
        if (sentenceBreak > start + CHUNK_SIZE / 2) {
          end = sentenceBreak + 1;
        }
      }
    }

    const chunk = text.slice(start, end).trim();
    if (chunk.length > 0) chunks.push(chunk);

    start = Math.max(start + 1, end - CHUNK_OVERLAP);
  }

  return chunks;
}

export function processFileContent(raw: RawFileContent): ProcessedDocument {
  const text = extractText(raw);
  const chunks = chunkText(text);
  const words = text.split(/\s+/).filter(Boolean);

  return {
    chunks,
    metadata: {
      fileName: raw.name,
      fileType: raw.type || 'text/plain',
      totalChunks: chunks.length,
      wordCount: words.length,
      charCount: text.length,
      processedAt: new Date().toISOString(),
    },
  };
}
