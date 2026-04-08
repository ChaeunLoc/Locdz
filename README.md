# Basic FastAPI API

Du an API co ban su dung FastAPI.

## Yeu cau

- Python 3.9+ (khuyen nghi 3.10 tro len)

## Cai dat

```bash
pip install -r requirements.txt
```

## Chay ung dung

```bash
uvicorn main:app --reload
```

Mac dinh API chay tai: `http://127.0.0.1:8000`

## Cac endpoint mau

- `GET /` -> Loi chao
- `GET /health` -> Kiem tra trang thai

## Tai lieu API tu dong

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
