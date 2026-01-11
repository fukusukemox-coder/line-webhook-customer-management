#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zoom背景画像生成モジュール（動画なし、画像のみ）
"""

import os
import json
import requests
from datetime import datetime

# 環境変数
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

def generate_zoom_background_images(customer_data, output_dir='output'):
    """
    顧客情報から3枚のZoom背景画像を生成
    
    Args:
        customer_data: 顧客情報の辞書
        output_dir: 出力ディレクトリ
    
    Returns:
        生成された画像のパスリスト
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 顧客情報を取得
    name = customer_data.get('お名前', '')
    display_name = customer_data.get('表示名(店名・屋号)', '')
    title = customer_data.get('肩書き', '')
    catchphrase = customer_data.get('ひと言キャッチ', '')
    service1 = customer_data.get('できること①', '')
    service2 = customer_data.get('できること②', '')
    contact_method = customer_data.get('連絡方法・連絡先', '')
    atmosphere = customer_data.get('雰囲気', 'ナチュラル')
    color = customer_data.get('カラー', 'グリーン系')
    keywords = customer_data.get('連想キーワード', '')
    taste = customer_data.get('テイスト', '')
    
    print(f"🎨 画像生成開始: {name} 様")
    print(f"  雰囲気: {atmosphere}")
    print(f"  カラー: {color}")
    print(f"  テイスト: {taste}")
    
    # 共通のスタイル指示
    style_prompt = f"""
Professional Zoom background template, 1920x1080 pixels, 16:9 aspect ratio.
Style: {atmosphere}, {taste}
Color scheme: {color}
Keywords: {keywords}
Design elements: watercolor botanical decorations, elegant layout
Left side: text area with clean background
Right side: frame for video/image placement
High quality, professional, clean design
"""
    
    generated_images = []
    
    # カット1: 自己紹介
    try:
        print("  📸 カット1生成中...")
        cut1_prompt = f"""{style_prompt}

Left side text content (in Japanese):
- Large name: {name}
- Subtitle: {title}
- Company: {display_name}
- Catchphrase: {catchphrase}

Right side: Vertical frame (9:16 aspect ratio) for video placement, elegant border

Text should be clearly readable, well-spaced, professional Japanese typography
"""
        
        cut1_path = os.path.join(output_dir, f'cut1_intro_{name}.png')
        generate_image_via_api(cut1_prompt, cut1_path)
        generated_images.append(cut1_path)
        print(f"  ✅ カット1完成: {cut1_path}")
    
    except Exception as e:
        print(f"  ❌ カット1生成エラー: {e}")
    
    # カット2: サービス紹介
    try:
        print("  📸 カット2生成中...")
        cut2_prompt = f"""{style_prompt}

Left side text content (in Japanese):
- Header: "提供サービス" (Services)
- Service 1: {service1}
- Service 2: {service2}

Right side: Horizontal frame (16:9 aspect ratio) for video placement, elegant border

Text should be clearly readable, well-spaced, professional Japanese typography
"""
        
        cut2_path = os.path.join(output_dir, f'cut2_services_{name}.png')
        generate_image_via_api(cut2_prompt, cut2_path)
        generated_images.append(cut2_path)
        print(f"  ✅ カット2完成: {cut2_path}")
    
    except Exception as e:
        print(f"  ❌ カット2生成エラー: {e}")
    
    # カット3: お問い合わせ
    try:
        print("  📸 カット3生成中...")
        cut3_prompt = f"""{style_prompt}

Left side text content (in Japanese):
- Header: "お問い合わせ" (Contact)
- Company: {display_name}
- Contact info: {contact_method}

Right side: Square frame for QR code placement, elegant border

Text should be clearly readable, well-spaced, professional Japanese typography
"""
        
        cut3_path = os.path.join(output_dir, f'cut3_contact_{name}.png')
        generate_image_via_api(cut3_prompt, cut3_path)
        generated_images.append(cut3_path)
        print(f"  ✅ カット3完成: {cut3_path}")
    
    except Exception as e:
        print(f"  ❌ カット3生成エラー: {e}")
    
    print(f"🎉 画像生成完了: {len(generated_images)}枚")
    return generated_images


def generate_image_via_api(prompt, output_path):
    """
    OpenAI APIで画像を生成
    
    Args:
        prompt: 画像生成プロンプト
        output_path: 出力ファイルパス
    """
    
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY環境変数が設定されていません")
    
    # OpenAI API呼び出し
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'dall-e-3',
        'prompt': prompt,
        'n': 1,
        'size': '1792x1024',  # 16:9に近い比率
        'quality': 'standard'
    }
    
    response = requests.post(
        'https://api.openai.com/v1/images/generations',
        headers=headers,
        json=data,
        timeout=60
    )
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    image_url = result['data'][0]['url']
    
    # 画像をダウンロード
    img_response = requests.get(image_url, timeout=30)
    if img_response.status_code == 200:
        with open(output_path, 'wb') as f:
            f.write(img_response.content)
    else:
        raise Exception(f"画像ダウンロード失敗: {img_response.status_code}")


if __name__ == '__main__':
    # テスト用
    test_data = {
        'お名前': '福山 修平',
        '表示名(店名・屋号)': '映像制作moX',
        '肩書き': '映像クリエイター',
        'ひと言キャッチ': '想いを映像で伝える',
        'できること①': '商品・サービス紹介動画作成',
        'できること②': 'ドローン空撮',
        '連絡方法・連絡先': 'SASAEAI',
        '雰囲気': 'ナチュラル',
        'カラー': 'グリーン系',
        '連想キーワード': '自然、植物、優しい',
        'テイスト': '水彩画風'
    }
    
    images = generate_zoom_background_images(test_data)
    print(f"生成された画像: {images}")
