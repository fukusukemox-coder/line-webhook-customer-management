#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import pandas as pd
from datetime import datetime

def upload_csv_to_google_drive():
    """CSVファイルをGoogle Driveにアップロード"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return False
    
    # Google DriveにアップロードするファイルパスとGoogle Sheets形式に変換
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    remote_path = f'manus_google_drive:LINE顧客管理システム_{timestamp}.csv'
    
    try:
        # rcloneを使用してアップロード
        result = subprocess.run(
            ['rclone', 'copy', csv_file, 'manus_google_drive:', '--config', '/home/ubuntu/.gdrive-rclone.ini'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"Google Driveにアップロード成功: {remote_path}")
            
            # 共有リンクを取得
            link_result = subprocess.run(
                ['rclone', 'link', f'manus_google_drive:customer_data.csv', '--config', '/home/ubuntu/.gdrive-rclone.ini'],
                capture_output=True,
                text=True
            )
            
            if link_result.returncode == 0:
                print(f"共有リンク: {link_result.stdout.strip()}")
                return link_result.stdout.strip()
            else:
                print("共有リンクの取得に失敗しました")
                return True
        else:
            print(f"アップロードエラー: {result.stderr}")
            return False
    
    except Exception as e:
        print(f"エラー: {e}")
        return False

def generate_summary_report():
    """サマリーレポートを生成"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return
    
    try:
        df = pd.read_csv(csv_file)
        
        print("\n=== LINE顧客管理システム サマリー ===")
        print(f"総メッセージ数: {len(df)}")
        print(f"\n返信ステータス:")
        print(df['返信ステータス'].value_counts())
        print(f"\nマネタイズ機会:")
        print(df['マネタイズ機会'].value_counts())
        print(f"\nユーザー別メッセージ数:")
        print(df['ユーザー名'].value_counts().head(10))
        
    except Exception as e:
        print(f"レポート生成エラー: {e}")

if __name__ == '__main__':
    generate_summary_report()
    upload_csv_to_google_drive()
