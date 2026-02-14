import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

app.post('/api/claude/chat', async (req, res) => {
  try {
    const { message, model } = req.body;
    const apiKey = process.env.VITE_CLAUDE_API_KEY || process.env.CLAUDE_API_KEY;

    console.log('📨 Claude API 요청:', { messageLength: message.length, model });

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01'
      },
      body: JSON.stringify({
        model: model || 'claude-opus-4-20250514',
        max_tokens: 4096,
        stream: true,
        messages: [{ role: 'user', content: message }]
      })
    });

    if (!response.ok) {
      const error = await response.text();
      console.error('Claude API 오류:', response.status, error);
      return res.status(response.status).json({ error });
    }

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const reader = response.body;
    reader.on('data', (chunk) => {
      res.write(chunk);
    });

    reader.on('end', () => {
      res.end();
    });

    reader.on('error', (error) => {
      console.error('스트림 오류:', error);
      res.end();
    });

  } catch (error) {
    console.error('프록시 서버 오류:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Claude 프록시 서버가 http://127.0.0.1:${PORT} 에서 실행 중입니다.`);
});
