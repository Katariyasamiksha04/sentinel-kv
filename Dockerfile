FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

COPY . .

EXPOSE 6379

CMD ["python", "-c", "from sentinelkv.core.store import KeyValueStore; from sentinelkv.network.server import SentinelServer; s = KeyValueStore(max_capacity=50000); srv = SentinelServer(s, host='0.0.0.0', port=6379); print('SentinelKV Server running on port 6379...'); srv.start(); import time; [time.sleep(1) for _ in iter(int, 1)]"]
