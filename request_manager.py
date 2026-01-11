#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zoom背景画像生成依頼の管理システム
"""

import json
import os
from datetime import datetime

REQUESTS_FILE = 'requests/pending.json'

def add_request(customer_name, user_id):
    """
    新しい依頼を追加
    
    Args:
        customer_name: 顧客名
        user_id: LINE user ID
    """
    
    # 既存の依頼を読み込み
    if os.path.exists(REQUESTS_FILE):
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
    else:
        requests = []
    
    # 新しい依頼を追加
    new_request = {
        'customer_name': customer_name,
        'user_id': user_id,
        'timestamp': datetime.now().isoformat(),
        'status': 'pending'
    }
    
    requests.append(new_request)
    
    # ファイルに保存
    os.makedirs(os.path.dirname(REQUESTS_FILE), exist_ok=True)
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 依頼を記録しました: {customer_name}")
    return new_request


def get_pending_requests():
    """
    未処理の依頼を取得
    
    Returns:
        未処理の依頼のリスト
    """
    
    if not os.path.exists(REQUESTS_FILE):
        return []
    
    with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
        requests = json.load(f)
    
    return [r for r in requests if r['status'] == 'pending']


def mark_as_completed(customer_name):
    """
    依頼を完了としてマーク
    
    Args:
        customer_name: 顧客名
    """
    
    if not os.path.exists(REQUESTS_FILE):
        return
    
    with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
        requests = json.load(f)
    
    for req in requests:
        if req['customer_name'] == customer_name and req['status'] == 'pending':
            req['status'] = 'completed'
            req['completed_at'] = datetime.now().isoformat()
    
    with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 依頼を完了としてマークしました: {customer_name}")


if __name__ == '__main__':
    # テスト
    add_request('福山 修平', 'U1234567890')
    pending = get_pending_requests()
    print(f"未処理の依頼: {len(pending)}件")
    for req in pending:
        print(f"  - {req['customer_name']} ({req['timestamp']})")
