#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_reply_status():
    """返信漏れを分析"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        print("CSVファイルが見つかりません")
        return None
    
    try:
        needs_reply = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['返信ステータス'] == '要返信':
                    needs_reply.append(row)
        
        if len(needs_reply) > 0:
            print("\n=== 返信漏れ検知 ===")
            print(f"返信が必要なメッセージ数: {len(needs_reply)}")
            print("\n詳細:")
            for row in needs_reply:
                content = row['メッセージ内容'][:50]
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {content}")
            
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
        return None, None
    
    try:
        high_opportunities = []
        medium_opportunities = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['マネタイズ機会'] == '高':
                    high_opportunities.append(row)
                elif row['マネタイズ機会'] == '中':
                    medium_opportunities.append(row)
        
        print("\n=== マネタイズ機会分析 ===")
        print(f"高優先度: {len(high_opportunities)}件")
        print(f"中優先度: {len(medium_opportunities)}件")
        
        if len(high_opportunities) > 0:
            print("\n【高優先度】:")
            for row in high_opportunities:
                content = row['メッセージ内容'][:50]
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {content}")
        
        if len(medium_opportunities) > 0:
            print("\n【中優先度】:")
            for i, row in enumerate(medium_opportunities[:5]):
                content = row['メッセージ内容'][:50]
                print(f"- {row['タイムスタンプ']} | {row['ユーザー名']} | {content}")
        
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
        user_stats = defaultdict(lambda: {'count': 0, 'last_message': ''})
        monetization_stats = defaultdict(int)
        reply_stats = defaultdict(int)
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user_name = row['ユーザー名']
                user_stats[user_name]['count'] += 1
                user_stats[user_name]['last_message'] = row['タイムスタンプ']
                
                monetization_stats[row['マネタイズ機会']] += 1
                reply_stats[row['返信ステータス']] += 1
        
        print("\n=== 顧客別サマリー ===")
        sorted_users = sorted(user_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        for user, stats in sorted_users:
            print(f"{user}: {stats['count']}件 (最終: {stats['last_message']})")
        
        print("\n=== マネタイズ機会別統計 ===")
        for level, count in monetization_stats.items():
            print(f"{level}: {count}件")
        
        print("\n=== 返信ステータス別統計 ===")
        for status, count in reply_stats.items():
            print(f"{status}: {count}件")
        
        return user_stats
    
    except Exception as e:
        print(f"サマリー生成エラー: {e}")
        return None

def generate_recommendations():
    """おすすめアクションを生成"""
    csv_file = '/home/ubuntu/line_webhook/customer_data.csv'
    
    if not os.path.exists(csv_file):
        return
    
    try:
        needs_reply_count = 0
        high_opportunities_count = 0
        user_last_message = {}
        new_followers_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['返信ステータス'] == '要返信':
                    needs_reply_count += 1
                
                if row['マネタイズ機会'] == '高':
                    high_opportunities_count += 1
                
                user_name = row['ユーザー名']
                timestamp = datetime.strptime(row['タイムスタンプ'], '%Y-%m-%d %H:%M:%S')
                if user_name not in user_last_message or timestamp > user_last_message[user_name]:
                    user_last_message[user_name] = timestamp
                
                if row['メッセージタイプ'] == 'follow':
                    new_followers_count += 1
        
        print("\n=== おすすめアクション ===")
        
        if needs_reply_count > 0:
            print(f"\n1. 【緊急】{needs_reply_count}件の返信漏れがあります")
            print("   → 優先的に返信してください")
        
        if high_opportunities_count > 0:
            print(f"\n2. 【重要】{high_opportunities_count}件の高優先度マネタイズ機会があります")
            print("   → 見積もりや提案を送ることをおすすめします")
        
        inactive_users = 0
        now = datetime.now()
        for user, last_msg in user_last_message.items():
            if now - last_msg > timedelta(days=30):
                inactive_users += 1
        
        if inactive_users > 0:
            print(f"\n3. 【フォローアップ】{inactive_users}名の顧客が30日以上連絡なし")
            print("   → フォローアップメッセージを送ることをおすすめします")
        
        if new_followers_count > 0:
            print(f"\n4. 【ウェルカム】{new_followers_count}名の新規フォロワー")
            print("   → ウェルカムメッセージを送ることをおすすめします")
    
    except Exception as e:
        print(f"推奨アクション生成エラー: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("LINE顧客管理システム - 分析レポート")
    print("=" * 60)
    
    analyze_reply_status()
    analyze_monetization_opportunities()
    generate_customer_summary()
    generate_recommendations()
    
    print("\n" + "=" * 60)
    print("分析完了")
    print("=" * 60)
