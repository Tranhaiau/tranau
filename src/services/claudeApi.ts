import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import {
  isExcelFile,
  isSupportedFileType,
  processFileContent,
  readExcelAsText,
  readFileAsText,
  type ProcessedDocument,
} from '../utils/fileProcessor';

export interface ClaudeResponse {
  answer: string;
  model: string;
  usage: { input_tokens: number; output_tokens: number };
}

export interface AskRequest {
  file: File;
  question: string;
}

export interface ChatRequest {
  document: ProcessedDocument;
  question: string;
}

// RTK Query API slice — acts as the proxy layer between UI and Claude API.
// The queryFn below intercepts file uploads, runs preprocessing (read → extract
// text → chunk), then forwards the structured data to the Express proxy server.
export const claudeApi = createApi({
  reducerPath: 'claudeApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api' }),
  endpoints: (builder) => ({
    // High-level mutation: accepts a raw File + question, handles all processing
    askAboutFile: builder.mutation<ClaudeResponse, AskRequest>({
      queryFn: async ({ file, question }, _api, _extraOptions, baseQuery) => {
        if (!isSupportedFileType(file)) {
          return {
            error: {
              status: 'CUSTOM_ERROR',
              error: `Loại file không được hỗ trợ: ${file.type || file.name}`,
            },
          };
        }

        let content: string;
        try {
          content = isExcelFile(file)
            ? await readExcelAsText(file)
            : await readFileAsText(file);
        } catch {
          return {
            error: { status: 'CUSTOM_ERROR', error: 'Không thể đọc file' },
          };
        }

        // Proxy step: process raw file → structured document before sending to Claude
        const document = processFileContent({
          name: file.name,
          content,
          type: file.type,
          size: file.size,
        });

        const result = await baseQuery({
          url: '/chat',
          method: 'POST',
          body: { document, question } satisfies ChatRequest,
        });

        if (result.error) return { error: result.error };
        return { data: result.data as ClaudeResponse };
      },
    }),

    // Low-level mutation: accepts an already-processed document (for re-querying)
    askAboutDocument: builder.mutation<ClaudeResponse, ChatRequest>({
      query: (body) => ({
        url: '/chat',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const { useAskAboutFileMutation, useAskAboutDocumentMutation } = claudeApi;
