## Simple AI Agent (CLI)

Agent này chạy trên terminal, dùng API tương thích OpenAI và hỗ trợ tool-calling cơ bản:

- `get_time`: lấy thời gian UTC
- `calculate`: tính toán biểu thức số học an toàn
- `save_note` / `list_notes`: lưu và đọc ghi chú cục bộ

### 1) Yêu cầu

- Python 3.10+
- API key cho endpoint chat-completions tương thích OpenAI

### 2) Cấu hình nhanh

```bash
export LLM_API_KEY="YOUR_API_KEY"
# optional:
export LLM_MODEL="gpt-4o-mini"
export LLM_API_URL="https://api.openai.com/v1/chat/completions"
```

### 3) Chạy agent

```bash
python3 ai_agent/agent.py
```

### 4) Ví dụ câu lệnh

- `What time is it in UTC?`
- `Calculate: (15 + 5) * 3`
- `Remember this note: call supplier at 9am tomorrow`
- `List my notes`

### 5) Thoát

- Gõ `/exit` hoặc `Ctrl+C`

### Ghi chú thiết kế

- Agent giữ lịch sử hội thoại trong phiên chạy hiện tại.
- Ghi chú được lưu vào file `ai_agent/notes.json`.
- Hàm tính toán giới hạn AST để tránh thực thi mã tùy ý.
