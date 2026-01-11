#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zoom背景動画生成ハンドラー
既存のwebhook_server.pyから呼び出される
"""

import os
import re
import subprocess
import json
from datetime import datetime

# 作業ディレクトリ
WORK_DIR = os.path.dirname(__file__)
PENDING_DIR = os.path.join(WORK_DIR, "zoom_pending")
OUTPUT_DIR = os.path.join(WORK_DIR, "zoom_output")
REQUESTS_DIR = os.path.join(WORK_DIR, "zoom_requests")

os.makedirs(PENDING_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REQUESTS_DIR, exist_ok=True)

# ペンディングリクエスト（メモリ内）
pending_requests = {}


def is_zoom_background_request(message_text):
    """Zoom背景リクエストかどうかを判定"""
    pattern = r'Zoom背景\s*(.+)'
    match = re.search(pattern, message_text, re.IGNORECASE)
    return match


def handle_zoom_text_message(user_id, message_text):
    """Zoom背景のテキストメッセージを処理"""
    match = is_zoom_background_request(message_text)
    
    if match:
        customer_name = match.group(1).strip()
        print(f"✓ Zoom背景リクエスト受信: {customer_name} (ユーザー: {user_id})")
        
        # ペンディングリクエストを作成
        pending_requests[user_id] = {
            "name": customer_name,
            "videos": [],
            "timestamp": datetime.now().isoformat()
        }
        
        return f"承知しました!「{customer_name}」様のZoom背景動画を作成します。\n動画素材を送信してください。(最大2本)"
    
    return None


def handle_zoom_video_message(user_id, video_path):
    """Zoom背景の動画メッセージを処理"""
    if user_id not in pending_requests:
        return None
    
    request = pending_requests[user_id]
    request["videos"].append(video_path)
    
    video_count = len(request["videos"])
    print(f"✓ 動画受信 ({video_count}/2): {os.path.basename(video_path)}")
    
    if video_count >= 2:
        # 2本揃ったので生成開始
        result = generate_zoom_background(user_id)
        return result
    else:
        return f"動画を受け取りました。({video_count}/2)\nもう1本送信してください。"


def generate_zoom_background(user_id):
    """Zoom背景動画を生成"""
    if user_id not in pending_requests:
        return {"success": False, "message": "リクエストが見つかりません。"}
    
    request = pending_requests[user_id]
    customer_name = request["name"]
    video_files = request["videos"]
    
    print(f"\n=== Zoom背景動画生成開始 ===")
    print(f"顧客名: {customer_name}")
    print(f"動画数: {len(video_files)}")
    
    try:
        # 動画生成スクリプトを実行
        cmd = [
            "python3",
            os.path.join(WORK_DIR, "zoom_bg_automation.py"),
            customer_name
        ] + video_files
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )
        
        print(result.stdout)
        
        # 生成された動画のパスを取得
        output_match = re.search(r'✓ 完成: (.+\.mp4)', result.stdout)
        if output_match:
            output_video = output_match.group(1)
            
            # リクエスト情報を保存
            request_file = save_request_info(user_id, customer_name, video_files, output_video)
            
            # ペンディングリクエストを削除
            del pending_requests[user_id]
            
            return {
                "success": True,
                "message": f"Zoom背景動画の作成が完了しました!\n\n管理者が確認後、配信いたします。\nしばらくお待ちください。",
                "video_path": output_video,
                "request_file": request_file
            }
        else:
            return {
                "success": False,
                "message": "動画生成に失敗しました。"
            }
    
    except subprocess.CalledProcessError as e:
        print(f"✗ エラー: {e.stderr}")
        return {
            "success": False,
            "message": f"動画生成中にエラーが発生しました。"
        }
    except Exception as e:
        print(f"✗ エラー: {e}")
        return {
            "success": False,
            "message": f"予期しないエラーが発生しました。"
        }


def save_request_info(user_id, customer_name, videos, output_video):
    """リクエスト情報をファイルに保存"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    request_file = os.path.join(REQUESTS_DIR, f"request_{user_id}_{timestamp}.json")
    
    data = {
        "user_id": user_id,
        "customer_name": customer_name,
        "videos": videos,
        "output_video": output_video,
        "timestamp": timestamp,
        "status": "completed",
        "completed_at": datetime.now().isoformat()
    }
    
    with open(request_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ リクエスト情報保存: {request_file}")
    
    return request_file


def download_line_video(message_id, channel_access_token):
    """LINEから動画をダウンロード"""
    import requests
    
    url = f'https://api-data.line.me/v2/bot/message/{message_id}/content'
    headers = {
        'Authorization': f'Bearer {channel_access_token}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            video_path = os.path.join(PENDING_DIR, f"{message_id}.mp4")
            with open(video_path, 'wb') as f:
                f.write(response.content)
            print(f"✓ 動画ダウンロード完了: {video_path}")
            return video_path
        else:
            print(f"✗ 動画ダウンロード失敗: {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ 動画ダウンロードエラー: {e}")
        return None
