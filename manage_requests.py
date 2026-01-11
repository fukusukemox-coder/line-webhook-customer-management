#!/usr/bin/env python3.11
"""
リクエスト管理ツール
生成された動画を確認し、LINEで配信する
"""

import os
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

WORK_DIR = "/home/ubuntu/zoom_automation"
REQUESTS_DIR = os.path.join(WORK_DIR, "requests")


def list_requests():
    """リクエスト一覧を表示"""
    requests = []
    
    for file in Path(REQUESTS_DIR).glob("request_*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            data["file"] = str(file)
            requests.append(data)
    
    # タイムスタンプでソート
    requests.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    if not requests:
        print("リクエストがありません。")
        return []
    
    print("\n=== 生成済みリクエスト一覧 ===\n")
    
    for i, req in enumerate(requests, 1):
        status = req.get("status", "unknown")
        status_icon = "✓" if status == "completed" else "⏳"
        
        print(f"[{i}] {status_icon} {req.get('customer_name', 'Unknown')}")
        print(f"    ユーザーID: {req.get('user_id', 'Unknown')}")
        print(f"    タイムスタンプ: {req.get('timestamp', 'Unknown')}")
        print(f"    ステータス: {status}")
        
        if status == "completed":
            output_video = req.get("output_video", "")
            if output_video and os.path.exists(output_video):
                file_size = os.path.getsize(output_video) / (1024 * 1024)
                print(f"    動画: {os.path.basename(output_video)} ({file_size:.1f}MB)")
            else:
                print(f"    動画: ファイルが見つかりません")
        
        print()
    
    return requests


def show_request_detail(request_index: int, requests: list):
    """リクエスト詳細を表示"""
    if request_index < 1 or request_index > len(requests):
        print("無効なインデックスです。")
        return None
    
    req = requests[request_index - 1]
    
    print("\n=== リクエスト詳細 ===\n")
    print(f"顧客名: {req.get('customer_name', 'Unknown')}")
    print(f"ユーザーID: {req.get('user_id', 'Unknown')}")
    print(f"タイムスタンプ: {req.get('timestamp', 'Unknown')}")
    print(f"ステータス: {req.get('status', 'unknown')}")
    
    if req.get("status") == "completed":
        print(f"完了日時: {req.get('completed_at', 'Unknown')}")
        print(f"動画パス: {req.get('output_video', 'Unknown')}")
    
    print(f"\n動画素材:")
    for i, video in enumerate(req.get("videos", []), 1):
        print(f"  {i}. {video}")
    
    print()
    
    return req


def send_to_line(user_id: str, video_path: str):
    """LINEに動画を送信"""
    try:
        # 動画をアップロード
        print(f"動画をアップロード中...")
        result = subprocess.run([
            "manus-upload-file", video_path
        ], capture_output=True, text=True, check=True)
        
        video_url = result.stdout.strip()
        print(f"✓ アップロード完了: {video_url}")
        
        # LINEにメッセージ送信
        print(f"LINEに送信中...")
        
        # テキストメッセージ
        text_message = {
            "type": "text",
            "text": "Zoom背景動画が完成しました!動画をご確認ください。"
        }
        
        subprocess.run([
            "manus-mcp-cli", "tool", "call", "push_text_message",
            "--server", "line",
            "--input", json.dumps({
                "userId": user_id,
                "message": text_message
            })
        ], check=True)
        
        print(f"✓ LINEに送信完了")
        return True
        
    except Exception as e:
        print(f"✗ 送信エラー: {e}")
        return False


def main():
    """メイン処理"""
    print("=== Zoom背景動画 リクエスト管理 ===")
    
    # リクエスト一覧を表示
    requests = list_requests()
    
    if not requests:
        return
    
    # インタラクティブモード
    while True:
        print("\n操作を選択してください:")
        print("  [番号] リクエスト詳細を表示")
        print("  s [番号] LINEに送信")
        print("  r リスト更新")
        print("  q 終了")
        
        choice = input("\n> ").strip()
        
        if choice == "q":
            print("終了します。")
            break
        
        elif choice == "r":
            requests = list_requests()
        
        elif choice.startswith("s "):
            try:
                index = int(choice.split()[1])
                req = requests[index - 1]
                
                if req.get("status") != "completed":
                    print("まだ生成が完了していません。")
                    continue
                
                output_video = req.get("output_video")
                if not output_video or not os.path.exists(output_video):
                    print("動画ファイルが見つかりません。")
                    continue
                
                # 確認
                print(f"\n以下の動画を送信します:")
                print(f"  顧客名: {req.get('customer_name')}")
                print(f"  ユーザーID: {req.get('user_id')}")
                print(f"  動画: {os.path.basename(output_video)}")
                
                confirm = input("\n送信しますか? (y/n): ").strip().lower()
                
                if confirm == "y":
                    if send_to_line(req.get("user_id"), output_video):
                        # ステータスを更新
                        with open(req["file"], 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        data["status"] = "sent"
                        data["sent_at"] = datetime.now().isoformat()
                        
                        with open(req["file"], 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        print("✓ 送信完了。ステータスを更新しました。")
                        requests = list_requests()
                else:
                    print("送信をキャンセルしました。")
            
            except (ValueError, IndexError):
                print("無効な番号です。")
        
        elif choice.isdigit():
            index = int(choice)
            show_request_detail(index, requests)
        
        else:
            print("無効な操作です。")


if __name__ == "__main__":
    main()
