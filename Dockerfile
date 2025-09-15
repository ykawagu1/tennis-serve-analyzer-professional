# Python 3.10 をベースにする
FROM python:3.10-slim

# 作業ディレクトリ
WORKDIR /app

# ffmpeg や依存ライブラリをインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションをコピー
COPY . .

# 環境変数
ENV PYTHONUNBUFFERED=1

# Render が PORT を渡してくるのでデフォルト 5000 にしておく
EXPOSE 5000

# Flask を gunicorn で起動
CMD exec gunicorn -b 0.0.0.0:$PORT main:app