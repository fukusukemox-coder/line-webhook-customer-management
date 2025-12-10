#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import hmac
import hashlib
import base64
from datetime import datetime
from flask import Flask, request, abort
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests

app = Flask(__name__)

# LINE設定
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')

# Google Sheets設定
SPREADSHEET_NAME = "LINE顧客管理システム"

# Google Sheets認証
def get_google_sheets_client():
    """Google Sheetsクライアントを取得"""
    # Google Drive APIの認証情報を使用
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # rcloneの設定ファイルから認証情報を取得
    # 代わりにOAuth2を使用する簡易的な方法
    try:
        # gspread-dataframeを使用する代わりに、直接APIを使用
        import subprocess
        result = subprocess.run(
            ['rclone', 'config', 'dump', 'manus_google_drive', '--config', '/home/ubuntu/.gdrive-rclone.ini'],
            capture_output=True,
            text=True
        )
        
        # 代替案: Google Sheets APIを直接使用
        # ここでは簡易的にCSVファイルとして保存し、後でGoogle Driveにアップロード
        return None
    except Exception as e:
        print(f"Google Sheets認証エラー: {e}")
        return None

def save_to_local_csv(data):
    """ローカルCSVファイルに保存"""
    import csv
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    # ファイルが存在しない場合はヘッダーを書き込む
    file_exists = os.path.isfile(csv_file)
    
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            # ヘッダー
            writer.writerow([
                'タイムスタンプ',
                'ユーザーID',
                'ユーザー名',
                'メッセージタイプ',
                'メッセージ内容',
                '返信ステータス',
                'マネタイズ機会',
                '備考'
            ])
        
        # データを書き込む
        writer.writerow(data)

def get_user_profile(user_id):
    """LINEユーザーのプロフィールを取得"""
    url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            profile = response.json()
            return profile.get('displayName', 'Unknown')
        else:
            return 'Unknown'
    except Exception as e:
        print(f"プロフィール取得エラー: {e}")
        return 'Unknown'

def analyze_monetization_opportunity(message_text):
    """メッセージからマネタイズ機会を分析"""
    keywords = {
        '高': ['見積', '予算', '料金', '価格', '費用', '依頼', '発注', '契約', '購入'],
        '中': ['興味', '詳しく', '教えて', '知りたい', '相談', '検討'],
        '低': ['ありがとう', 'よろしく', 'わかりました', 'OK']
    }
    
    message_lower = message_text.lower()
    
    for level, words in keywords.items():
        for word in words:
            if word in message_text:
                return level
    
    return '要確認'

def check_reply_needed(message_text):
    """返信が必要かどうかを判定"""
    question_keywords = ['?', '？', 'どう', 'いつ', 'どこ', 'なに', '教えて', '知りたい', 'できます', 'お願い']
    
    for keyword in question_keywords:
        if keyword in message_text:
            return '要返信'
    
    return '確認済み'

@app.route('/webhook', methods=['POST'])
def webhook():
    """LINEからのWebhookを受信"""
    
    # 署名検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    if CHANNEL_SECRET:
        hash_value = hmac.new(
            CHANNEL_SECRET.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        
        if signature != expected_signature:
            abort(400)
    
    # イベント処理
    try:
        events = json.loads(body)['events']
        
        for event in events:
            if event['type'] == 'message':
                # メッセージイベント
                user_id = event['source']['userId']
                message_type = event['message']['type']
                
                # ユーザープロフィール取得
                user_name = get_user_profile(user_id)
                
                # メッセージ内容
                message_content = ''
                if message_type == 'text':
                    message_content = event['message']['text']
                elif message_type == 'image':
                    message_content = '[画像]'
                elif message_type == 'video':
                    message_content = '[動画]'
                elif message_type == 'audio':
                    message_content = '[音声]'
                elif message_type == 'file':
                    message_content = '[ファイル]'
                elif message_type == 'location':
                    message_content = '[位置情報]'
                elif message_type == 'sticker':
                    message_content = '[スタンプ]'
                else:
                    message_content = f'[{message_type}]'
                
                # 返信ステータスとマネタイズ機会を分析
                reply_status = check_reply_needed(message_content) if message_type == 'text' else '確認済み'
                monetization = analyze_monetization_opportunity(message_content) if message_type == 'text' else '-'
                
                # タイムスタンプ
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                # データを保存
                data = [
                    timestamp,
                    user_id,
                    user_name,
                    message_type,
                    message_content,
                    reply_status,
                    monetization,
                    ''
                ]
                
                save_to_local_csv(data)
                
                print(f"メッセージ記録: {user_name} - {message_content}")
            
            elif event['type'] == 'follow':
                # フォローイベント
                user_id = event['source']['userId']
                user_name = get_user_profile(user_id)
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                data = [
                    timestamp,
                    user_id,
                    user_name,
                    'follow',
                    '[新規フォロー]',
                    '要返信',
                    '高',
                    '新規顧客'
                ]
                
                save_to_local_csv(data)
                print(f"新規フォロー: {user_name}")
            
            elif event['type'] == 'unfollow':
                # アンフォローイベント
                user_id = event['source']['userId']
                timestamp = datetime.fromtimestamp(event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                data = [
                    timestamp,
                    user_id,
                    'Unknown',
                    'unfollow',
                    '[ブロック/削除]',
                    '-',
                    '-',
                    '離脱顧客'
                ]
                
                save_to_local_csv(data)
                print(f"アンフォロー: {user_id}")
    
    except Exception as e:
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    return 'OK', 200

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return 'OK', 200

@app.route('/', methods=['GET'])
def index():
    """ルートパス"""
    return 'LINE Webhook Server is running!', 200

if __name__ == '__main__':
    # 環境変数の確認
    if not CHANNEL_ACCESS_TOKEN:
        print("警告: LINE_CHANNEL_ACCESS_TOKENが設定されていません")
    
    if not CHANNEL_SECRET:
        print("警告: LINE_CHANNEL_SECRETが設定されていません")
    
    # サーバー起動
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
