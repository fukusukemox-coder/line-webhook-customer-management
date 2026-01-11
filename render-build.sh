#!/usr/bin/env bash
# Render.com用のビルドスクリプト

set -o errexit

# Pythonパッケージをインストール
pip install -r requirements.txt

# ffmpegをインストール（Render環境）
apt-get update
apt-get install -y ffmpeg

echo "✓ ビルド完了"
