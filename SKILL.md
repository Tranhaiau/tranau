---
name: rtk-proxy-claude
description: Ứng dụng phân tích tài liệu với Claude — RTK Query đóng vai trò proxy xử lý file (đọc → trích xuất text → chia đoạn) trước khi gửi đến Claude API qua Express server. Dùng khi cần upload tài liệu văn bản (.txt, .md, .csv, .json, .html, .xml) và đặt câu hỏi về nội dung.
---

# RTK Proxy — Phân tích tài liệu với Claude

## Tổng quan

Ứng dụng web cho phép người dùng tải lên một tài liệu văn bản và đặt câu hỏi
về nội dung của nó. Điểm đặc trưng của dự án là **RTK Query đóng vai trò lớp
proxy phía client**: file thô được tiền xử lý (đọc, trích xuất text, chia
đoạn) ngay trong `queryFn` trước khi dữ liệu có cấu trúc được chuyển tiếp đến
Express proxy server, rồi từ đó gọi Claude API.

## Pipeline xử lý

```
File upload → RTK Query proxy → Text extraction + chunking → Express proxy → Claude API
```

1. **Upload** (`src/components/FileUpload.tsx`): kéo thả hoặc chọn file,
   kiểm tra loại file và giới hạn dung lượng 10 MB.
2. **RTK Query proxy** (`src/services/claudeApi.ts`): mutation
   `askAboutFile` chặn file thô, kiểm tra loại file, đọc nội dung, gọi bộ
   xử lý rồi mới forward đến server.
3. **Tiền xử lý** (`src/utils/fileProcessor.ts`): trích xuất text (parse
   JSON, strip thẻ HTML/XML), chia đoạn ~2000 ký tự với overlap 200 ký tự,
   ưu tiên cắt tại ranh giới đoạn văn hoặc câu; sinh metadata (số từ, số
   đoạn, thời điểm xử lý).
4. **Express proxy** (`server/index.js`): endpoint `POST /api/chat` nhận
   `{ document, question }`, ghép các đoạn thành context và gọi Claude
   (model `claude-sonnet-4-6`, `max_tokens: 2048`) với system prompt trợ lý
   phân tích tài liệu. API key chỉ tồn tại phía server.
5. **Hiển thị** (`src/components/ChatInterface.tsx`): render hội thoại,
   metadata tài liệu và trạng thái đang xử lý / đang trả lời.

## Cấu trúc thư mục

| Đường dẫn | Vai trò |
|---|---|
| `src/App.tsx` | Bố cục chính: upload → chat, quản lý file và document đã xử lý |
| `src/app/store.ts` | Redux store, đăng ký reducer + middleware của `claudeApi` |
| `src/services/claudeApi.ts` | API slice RTK Query — lớp proxy client, 2 mutation |
| `src/utils/fileProcessor.ts` | Đọc file, trích xuất text, chunking, metadata |
| `src/components/FileUpload.tsx` | Drop-zone upload, validate loại file và dung lượng |
| `src/components/ChatInterface.tsx` | Giao diện hỏi đáp, cache document cho câu hỏi tiếp theo |
| `server/index.js` | Express proxy: `/api/chat`, `/api/health`, gọi Anthropic SDK |
| `vite.config.ts` | Dev server cổng 5173, proxy `/api` → `http://localhost:3001` |

## API

### `POST /api/chat`

Request body:

```json
{
  "document": {
    "chunks": ["..."],
    "metadata": {
      "fileName": "bao-cao.md",
      "fileType": "text/markdown",
      "totalChunks": 3,
      "wordCount": 1200,
      "charCount": 7800,
      "processedAt": "2026-07-02T00:00:00.000Z"
    }
  },
  "question": "Tài liệu nói về điều gì?"
}
```

Response:

```json
{
  "answer": "...",
  "model": "claude-sonnet-4-6",
  "usage": { "input_tokens": 123, "output_tokens": 456 }
}
```

Lỗi: `400` khi thiếu `document`/`question`, `500` kèm `{ "error": "..." }`
khi gọi Claude thất bại.

### `GET /api/health`

Trả về `{ "status": "ok" }` — dùng kiểm tra server đang chạy.

### RTK Query mutations

- `useAskAboutFileMutation({ file, question })` — mức cao: nhận `File` thô,
  tự validate + đọc + xử lý rồi gửi. Dùng cho câu hỏi đầu tiên.
- `useAskAboutDocumentMutation({ document, question })` — mức thấp: nhận
  `ProcessedDocument` đã xử lý sẵn. Dùng cho các câu hỏi tiếp theo (tránh
  xử lý lại file).

## Loại file hỗ trợ

`.txt` · `.md` · `.csv` · `.json` · `.html` · `.xml` (các MIME type
`text/plain`, `text/markdown`, `text/csv`, `text/html`, `application/json`,
`application/xml`, `text/xml`). Giới hạn 10 MB. File nhị phân (PDF, DOCX,
ảnh) **chưa** được hỗ trợ.

## Tham số xử lý

| Tham số | Giá trị | Nơi định nghĩa |
|---|---|---|
| Kích thước chunk | 2000 ký tự | `CHUNK_SIZE` — `src/utils/fileProcessor.ts` |
| Overlap giữa các chunk | 200 ký tự | `CHUNK_OVERLAP` — `src/utils/fileProcessor.ts` |
| Giới hạn file | 10 MB | `FileUpload.tsx` |
| Giới hạn body server | 20 MB | `server/index.js` |
| Model | `claude-sonnet-4-6` | `server/index.js` |
| Max tokens trả lời | 2048 | `server/index.js` |

## Cài đặt & chạy

```bash
# 1. Cài dependencies
npm install

# 2. Cấu hình API key
cp .env.example .env
# rồi điền ANTHROPIC_API_KEY vào .env

# 3. Chạy đồng thời client (5173) + server (3001)
npm run dev
```

Script khác: `npm run dev:client`, `npm run dev:server`,
`npm run build` (tsc + vite build), `npm run preview`.

## Lưu ý & giới hạn hiện tại

- **API key** đọc từ biến môi trường `ANTHROPIC_API_KEY` phía server; không
  bao giờ đưa key vào code client. File `.env` đã nằm trong `.gitignore`.
- Toàn bộ chunks được ghép lại và gửi trong **một** request — tài liệu rất
  dài có thể vượt giới hạn context; chưa có bước chọn lọc chunk liên quan
  (retrieval).
- Server chưa có rate limiting và xác thực người dùng — chỉ phù hợp chạy
  local/dev.
- Hội thoại không có nhớ ngữ cảnh giữa các câu hỏi: mỗi câu hỏi là một
  request độc lập kèm toàn bộ tài liệu.

## Hướng phát triển tiếp theo

- Hỗ trợ PDF/DOCX (trích xuất text phía server).
- Chọn lọc chunk theo độ liên quan với câu hỏi thay vì gửi toàn bộ.
- Streaming câu trả lời (SSE) để hiển thị dần thay vì chờ trọn vẹn.
- Gửi kèm lịch sử hội thoại để hỏi nối tiếp có ngữ cảnh.
- Prompt caching cho phần context tài liệu khi hỏi nhiều câu trên cùng file.
