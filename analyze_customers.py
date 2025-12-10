#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
from datetime import datetime, timedelta
import subprocess

def analyze_reply_status():
    """返信漏れを分析"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return None
    
    try:
        df = pd.read_csv(csv_file)
        
        # 返信が必要なメッセージを抽出
        needs_reply = df[df['返信ステータス'] == '要返信']
        
        if len(needs_reply) > 0:
            print("\n=== 返信漏れ検知 ===")
            print(f"返信が必要なメッセージ数: {len(needs_reply)}")
            print("\n詳細:")
            for idx, row in needs_reply.iterrows():
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {row['メッセージ内容'][:50]}")
            
            return needs_reply
        else:
            print("\n返信漏れはありません！")
            return None
    
    except Exception as e:
        print(f"分析エラー: {e}")
        return None

def analyze_monetization_opportunities():
    """マネタイズ機会を分析"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return None
    
    try:
        df = pd.read_csv(csv_file)
        
        # マネタイズ機会が高いメッセージを抽出
        high_opportunities = df[df['マネタイズ機会'] == '高']
        medium_opportunities = df[df['マネタイズ機会'] == '中']
        
        print("\n=== マネタイズ機会分析 ===")
        print(f"高優先度: {len(high_opportunities)}件")
        print(f"中優先度: {len(medium_opportunities)}件")
        
        if len(high_opportunities) > 0:
            print("\n【高優先度】:")
            for idx, row in high_opportunities.iterrows():
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {row['メッセージ内容'][:50]}")
        
        if len(medium_opportunities) > 0:
            print("\n【中優先度】:")
            for idx, row in medium_opportunities.head(5).iterrows():
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {row['メッセージ内容'][:50]}")
        
        return high_opportunities, medium_opportunities
    
    except Exception as e:
        print(f"分析エラー: {e}")
        return None, None

def generate_customer_summary():
    """顧客サマリーを生成"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return None
    
    try:
        df = pd.read_csv(csv_file)
        
        # ユーザー別の統計
        user_stats = df.groupby('ユーザー名').agg({
            'メッセージ内容': 'count',
            'タイムスタンプ': 'max'
        }).rename(columns={
            'メッセージ内容': 'メッセージ数',
            'タイムスタンプ': '最終メッセージ'
        }).sort_values('メッセージ数', ascending=False)
        
        print("\n=== 顧客別サマリー ===")
        print(user_stats)
        
        # マネタイズ機会別の統計
        monetization_stats = df['マネタイズ機会'].value_counts()
        print("\n=== マネタイズ機会別統計 ===")
        print(monetization_stats)
        
        # 返信ステータス別の統計
        reply_stats = df['返信ステータス'].value_counts()
        print("\n=== 返信ステータス別統計 ===")
        print(reply_stats)
        
        return user_stats
    
    except Exception as e:
        print(f"サマリー生成エラー: {e}")
        return None

def export_to_google_sheets():
    """Google Sheetsにエクスポート"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("\nCSVファイルが見つかりません")
        return None
    
    try:
        # Google Driveにアップロード
        print("\n=== Google Driveにアップロード中 ===")
        
        # ファイル名を変更してアップロード
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_filename = f'LINE顧客管理_{timestamp}.csv'
        
        # ファイルをコピー
        subprocess.run(['cp', csv_file, f'/home/ubuntu/line_webhook/{new_filename}'])
        
        # rcloneでアップロード
        result = subprocess.run(
            ['rclone', 'copy', f'/home/ubuntu/line_webhook/{new_filename}', 
             'manus_google_drive:', '--config', '/home/ubuntu/.gdrive-rclone.ini'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✓ Google Driveにアップロード成功: {new_filename}")
            
            # 共有リンクを取得
            link_result = subprocess.run(
                ['rclone', 'link', f'manus_google_drive:{new_filename}', 
                 '--config', '/home/ubuntu/.gdrive-rclone.ini'],
                capture_output=True,
                text=True
            )
            
            if link_result.returncode == 0:
                link = link_result.stdout.strip()
                print(f"✓ 共有リンク: {link}")
                return link
            else:
                print("共有リンクの取得に失敗しました")
                return True
        else:
            print(f"アップロードエラー: {result.stderr}")
            return None
    
    except Exception as e:
        print(f"エクスポートエラー: {e}")
        return None

def generate_recommendations():
    """おすすめアクションを生成"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        return
    
    try:
        df = pd.read_csv(csv_file)
        
        print("\n=== おすすめアクション ===")
        
        # 1. 返信漏れ
        needs_reply = df[df['返信ステータス'] == '要返信']
        if len(needs_reply) > 0:
            print(f"\n1. 【緊急】{len(needs_reply)}件の返信漏れがあります")
            print("   → 優先的に返信してください")
        
        # 2. 高優先度マネタイズ機会
        high_opportunities = df[df['マネタイズ機会'] == '高']
        if len(high_opportunities) > 0:
            print(f"\n2. 【重要】{len(high_opportunities)}件の高優先度マネタイズ機会があります")
            print("   → 見積もりや提案を送ることをおすすめします")
        
        # 3. 長期間連絡がない顧客
        df['タイムスタンプ'] = pd.to_datetime(df['タイムスタンプ'])
        user_last_message = df.groupby('ユーザー名')['タイムスタンプ'].max()
        inactive_users = user_last_message[user_last_message < datetime.now() - timedelta(days=30)]
        
        if len(inactive_users) > 0:
            print(f"\n3. 【フォローアップ】{len(inactive_users)}名の顧客が30日以上連絡なし")
            print("   → フォローアップメッセージを送ることをおすすめします")
        
        # 4. 新規フォロワー
        new_followers = df[df['メッセージタイプ'] == 'follow']
        if len(new_followers) > 0:
            print(f"\n4. 【ウェルカム】{len(new_followers)}名の新規フォロワー")
            print("   → ウェルカムメッセージを送ることをおすすめします")
    
    except Exception as e:
        print(f"推奨アクション生成エラー: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("LINE顧客管理システム - 分析レポート")
    print("=" * 60)
    
    # 各種分析を実行
    analyze_reply_status()
    analyze_monetization_opportunities()
    generate_customer_summary()
    generate_recommendations()
    
    # Google Sheetsにエクスポート
    link = export_to_google_sheets()
    
    print("\n" + "=" * 60)
    print("分析完了")
    print("=" * 60)
