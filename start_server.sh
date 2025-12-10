#!/bin/bash

# 環境変数を設定
export LINE_CHANNEL_SECRET="c0592a135aaa73fbc8f36bf2a76f6f71"
export LINE_CHANNEL_ACCESS_TOKEN="AULsczQVL/F8nyp54SVCzyWJU/hT/ZjKzc1lTwtm/+HqabI5MhCTUpG4NJjAATL1J8d+a9+lGhwhr01HrFk9qLlQJVgrJ4rdqDPCOfadHQBEeFVWN276XTM5dODmn/KA02WfpACLFVCYs20vdZZnuwdB04t89/1O/w1cDnyilFU="
export PORT=5000

# 仮想環境をアクティベート
cd /home/ubuntu/line_webhook
source venv/bin/activate

# サーバーを起動
python webhook_server.py
