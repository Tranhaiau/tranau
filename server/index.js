import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import Anthropic from '@anthropic-ai/sdk';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: '20mb' }));

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

app.post('/api/chat', async (req, res) => {
  const { document, question } = req.body;

  if (!document || !question) {
    return res.status(400).json({ error: 'Thiếu document hoặc câu hỏi' });
  }

  try {
    const context = document.chunks
      .map((chunk, i) => `[Đoạn ${i + 1}/${document.metadata.totalChunks}]\n${chunk}`)
      .join('\n\n---\n\n');

    const message = await anthropic.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 2048,
      system:
        'Bạn là trợ lý phân tích tài liệu. Hãy trả lời câu hỏi dựa trên nội dung tài liệu được cung cấp. Nếu thông tin không có trong tài liệu, hãy nói rõ điều đó. Trả lời bằng ngôn ngữ của câu hỏi.',
      messages: [
        {
          role: 'user',
          content: `Tài liệu: "${document.metadata.fileName}" (${document.metadata.wordCount} từ, ${document.metadata.totalChunks} đoạn)\n\n${context}\n\n---\n\nCâu hỏi: ${question}`,
        },
      ],
    });

    const answer = message.content.find((b) => b.type === 'text')?.text ?? '';

    res.json({
      answer,
      model: message.model,
      usage: message.usage,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Lỗi không xác định';
    res.status(500).json({ error: message });
  }
});

app.get('/api/health', (_req, res) => res.json({ status: 'ok' }));

const port = process.env.PORT ?? 3001;
app.listen(port, () => console.log(`Proxy server listening on port ${port}`));
