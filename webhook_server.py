#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import hmac
import hashlib
import base64
from datetime import datetime
from flask import Flask, request, abort
import requests
from threading import Thread
import zoom_background_handler as zoom_handler


app = Flask(__name__)

# LINE設定
CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET', '')
CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN', '')
ADMIN_USER_ID = os.environ.get('ADMIN_USER_ID', '')  # 管理者のLINE USER ID

# Google Sheets設定
SPREADSHEET_NAME = "LINE顧客管理システム"

def save_to_local_csv(data):
    """ローカルCSVファイルに保存（BOM付きUTF-8）"""
    import csv
    # 相対パスを使用（Render.com環境対応）
    csv_file = os.path.join(os.path.dirname(__file__), 'customer_data.csv')
    
    # ファイルが存在しない場合はヘッダーを書き込む
    file_exists = os.path.isfile(csv_file)
    
    try:
        # BOM付きUTF-8で書き込み（Excelで正しく開けるようにする）
        with open(csv_file, 'a', newline='', encoding='utf-8-sig') as f:
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
            print(f"✅ CSVに保存しました: {data[2]} - {data[4]}")
    except Exception as e:
        print(f"❌ CSV保存エラー: {e}")
        import traceback
        traceback.print_exc()

def send_reply_message(user_id, message_text):
    """LINEユーザーに返信メッセージを送信"""
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        'to': user_id,
        'messages': [
            {
                'type': 'text',
                'text': message_text
            }
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=5)
        if response.status_code == 200:
            print(f"✅ メッセージ送信成功: {user_id}")
            return True
        else:
            print(f"⚠️ メッセージ送信失敗: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ メッセージ送信エラー: {e}")
        return False

def get_user_profile(user_id):
    """LINEユーザーのプロフィールを取得"""
    url = f'https://api.line.me/v2/bot/profile/{user_id}'
    headers = {
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            profile = response.json()
            return profile.get('displayName', 'Unknown')
        else:
            print(f"⚠️ プロフィール取得失敗: {response.status_code}")
            return 'Unknown'
    except Exception as e:
        print(f"❌ プロフィール取得エラー: {e}")
        return 'Unknown'

def get_auto_reply(message_text):
    """キーワードベースの自動返信メッセージを取得"""
    # 長いキーワードを優先するため、順序を指定
    auto_replies = [
        # 長いキーワードを最優先
        ('詳しい実績', '非公開実績をご覧いただけます！\n\n🔒 非公開実績\nhttps://www.notion.so/moxmovie/a4b31ca6873c48d7bc3caea433e83ae2\n\nパスワードは個別にお伝えいたします。\n担当者からのメッセージをお待ちください！\n\nご不明な点があれば、お気軽にお問い合わせください！'),
        
        # 納期関連
        ('納期', '納期の目安について📅\n\n✅ 一般的な納期\n・企業紹介映像: 約1ヶ月\n・SNS用動画: 約2週間\n・イベント撮影: 約2週間\n・編集のみ: 約1〜2週間\n\n※プロジェクトの規模や内容により変動します\n※お急ぎの場合はご相談ください\n\nまずはお気軽にお問い合わせください！'),
        ('いつまで', '納期の目安について📅\n\n✅ 一般的な納期\n・企業紹介映像: 約1ヶ月\n・SNS用動画: 約2週間\n・イベント撮影: 約2週間\n・編集のみ: 約1〜2週間\n\n※プロジェクトの規模や内容により変動します\n※お急ぎの場合はご相談ください\n\nまずはお気軽にお問い合わせください！'),
        ('何日', '納期の目安について📅\n\n✅ 一般的な納期\n・企業紹介映像: 約1ヶ月\n・SNS用動画: 約2週間\n・イベント撮影: 約2週間\n・編集のみ: 約1〜2週間\n\n※プロジェクトの規模や内容により変動します\n※お急ぎの場合はご相談ください\n\nまずはお気軽にお問い合わせください！'),
        ('期間', '納期の目安について📅\n\n✅ 一般的な納期\n・企業紹介映像: 約1ヶ月\n・SNS用動画: 約2週間\n・イベント撮影: 約2週間\n・編集のみ: 約1〜2週間\n\n※プロジェクトの規模や内容により変動します\n※お急ぎの場合はご相談ください\n\nまずはお気軽にお問い合わせください！'),
        
        # 撮影時間関連
        ('撮影時間', '撮影時間の目安について⏱️\n\n✅ 一般的な撮影時間\n・企業紹介映像: 半日〜1日\n・インタビュー撮影: 2〜3時間\n・イベント撮影: イベント時間に応じて\n・商品撮影: 半日程度\n\n※内容や規模により変動します\n※詳しくはお見積もり時にご案内いたします\n\nまずはお気軽にお問い合わせください！'),
        ('何時間', '撮影時間の目安について⏱️\n\n✅ 一般的な撮影時間\n・企業紹介映像: 半日〜1日\n・インタビュー撮影: 2〜3時間\n・イベント撮影: イベント時間に応じて\n・商品撮影: 半日程度\n\n※内容や規模により変動します\n※詳しくはお見積もり時にご案内いたします\n\nまずはお気軽にお問い合わせください！'),
        ('どのくらい', '撮影時間の目安について⏱️\n\n✅ 一般的な撮影時間\n・企業紹介映像: 半日〜1日\n・インタビュー撮影: 2〜3時間\n・イベント撮影: イベント時間に応じて\n・商品撮影: 半日程度\n\n※内容や規模により変動します\n※詳しくはお見積もり時にご案内いたします\n\nまずはお気軽にお問い合わせください！'),
        
        # ドローン撮影関連
        ('ドローン', 'ドローン空撮も対応可能です！🚁\n（国土交通省の許可取得済み）\n\n📍 対応内容\n・通常ドローン空撮（4K撮影）\n・FPVドローン撮影（ダイナミックな映像）\n・企業施設・イベント会場の俯瞰撮影\n・観光地・景観の撮影\n\n✨ FPVドローンの特徴\n・従来のドローンでは難しい迫力ある映像\n・建物内部や狭い空間の撮影も可能\n・映画やCMのようなダイナミックな演出\n\n💰 料金目安\n・通常ドローン空撮: 8万円〜\n・FPVドローン撮影: 12万円〜\n※編集料は別途お見積もり\n\n詳しくはお問い合わせください！'),
        ('空撮', 'ドローン空撮も対応可能です！🚁\n（国土交通省の許可取得済み）\n\n📍 対応内容\n・通常ドローン空撮（4K撮影）\n・FPVドローン撮影（ダイナミックな映像）\n・企業施設・イベント会場の俯瞰撮影\n・観光地・景観の撮影\n\n✨ FPVドローンの特徴\n・従来のドローンでは難しい迫力ある映像\n・建物内部や狭い空間の撮影も可能\n・映画やCMのようなダイナミックな演出\n\n💰 料金目安\n・通常ドローン空撮: 8万円〜\n・FPVドローン撮影: 12万円〜\n※編集料は別途お見積もり\n\n詳しくはお問い合わせください！'),
        ('fpv', 'ドローン空撮も対応可能です！🚁\n（国土交通省の許可取得済み）\n\n📍 対応内容\n・通常ドローン空撮（4K撮影）\n・FPVドローン撮影（ダイナミックな映像）\n・企業施設・イベント会場の俯瞰撮影\n・観光地・景観の撮影\n\n✨ FPVドローンの特徴\n・従来のドローンでは難しい迫力ある映像\n・建物内部や狭い空間の撮影も可能\n・映画やCMのようなダイナミックな演出\n\n💰 料金目安\n・通常ドローン空撮: 8万円〜\n・FPVドローン撮影: 12万円〜\n※編集料は別途お見積もり\n\n詳しくはお問い合わせください！'),
        
        # 修正・リテイク関連
        ('修正', '修正・リテイク対応について📝\n\n✅ 基本対応\n・初回納品後、2回まで無料で修正対応いたします\n・細かな調整や微修正も丁寧に対応\n\n💡 修正内容の例\n・テロップの文言変更\n・BGMの差し替え\n・カット割りの調整\n・色味の微調整\n\n⚠️ 追加料金が発生する場合\n・3回目以降の修正: 2万円〜/回\n・再撮影が必要な場合: 別途お見積もり\n・大幅な構成変更: 別途お見積もり\n\nまずはお気軽にご相談ください！'),
        ('リテイク', '修正・リテイク対応について📝\n\n✅ 基本対応\n・初回納品後、2回まで無料で修正対応いたします\n・細かな調整や微修正も丁寧に対応\n\n💡 修正内容の例\n・テロップの文言変更\n・BGMの差し替え\n・カット割りの調整\n・色味の微調整\n\n⚠️ 追加料金が発生する場合\n・3回目以降の修正: 2万円〜/回\n・再撮影が必要な場合: 別途お見積もり\n・大幅な構成変更: 別途お見積もり\n\nまずはお気軽にご相談ください！'),
        ('やり直し', '修正・リテイク対応について📝\n\n✅ 基本対応\n・初回納品後、2回まで無料で修正対応いたします\n・細かな調整や微修正も丁寧に対応\n\n💡 修正内容の例\n・テロップの文言変更\n・BGMの差し替え\n・カット割りの調整\n・色味の微調整\n\n⚠️ 追加料金が発生する場合\n・3回目以降の修正: 2万円〜/回\n・再撮影が必要な場合: 別途お見積もり\n・大幅な構成変更: 別途お見積もり\n\nまずはお気軽にご相談ください！'),
        ('変更', '修正・リテイク対応について📝\n\n✅ 基本対応\n・初回納品後、2回まで無料で修正対応いたします\n・細かな調整や微修正も丁寧に対応\n\n💡 修正内容の例\n・テロップの文言変更\n・BGMの差し替え\n・カット割りの調整\n・色味の微調整\n\n⚠️ 追加料金が発生する場合\n・3回目以降の修正: 2万円〜/回\n・再撮影が必要な場合: 別途お見積もり\n・大幅な構成変更: 別途お見積もり\n\nまずはお気軽にご相談ください！'),
        
        # 契約・発注の流れ
        ('契約', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        ('発注', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        ('流れ', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        ('手順', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        ('どうやって', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        ('申し込み', 'ご依頼の流れについて📋\n\n1️⃣ ヒアリング\n・目的や用途、イメージをお聞かせください\n・LINE、お電話、対面、オンラインMTG対応可能です\n\n2️⃣ お見積もり\n・お見積もり・ご相談は完全無料です！\n・内容に応じて料金や納期をご提示します\n\n3️⃣ ご契約・打ち合わせ\n・お見積もりにご納得いただけましたら契約\n・詳細な打ち合わせを行います\n\n4️⃣ 撮影・制作\n・スケジュールに沿って撮影・編集を進めます\n・プロの機材と技術で高品質な映像を制作します\n\n5️⃣ 納品\n・初回納品後、2回まで無料で修正対応\n・完成した映像をお渡しします\n\nまずはお気軽にご相談ください！'),
        
        # 営業日・定休日関連
        ('お休み', '営業日について📅\n\n基本的に年中無休で対応しております！\n土日祝日もご相談・お見積もり可能です。\n\n⏰ 返信時間\n平日・土日: 10:00〜18:00\n※夜間や早朝のメッセージは翌営業時間内にご返信いたします\n\nお急ぎの場合はその旨お知らせください！'),
        ('休み', '営業日について📅\n\n基本的に年中無休で対応しております！\n土日祝日もご相談・お見積もり可能です。\n\n⏰ 返信時間\n平日・土日: 10:00〜18:00\n※夜間や早朝のメッセージは翌営業時間内にご返信いたします\n\nお急ぎの場合はその旨お知らせください！'),
        ('定休日', '営業日について📅\n\n基本的に年中無休で対応しております！\n土日祝日もご相談・お見積もり可能です。\n\n⏰ 返信時間\n平日・土日: 10:00〜18:00\n※夜間や早朝のメッセージは翌営業時間内にご返信いたします\n\nお急ぎの場合はその旨お知らせください！'),
        ('ポートフォリオ', '制作実績はこちらからご覧いただけます！\n\n🎬 公開実績\nhttps://www.mox-motage.com/works\n\nより詳しい実績（非公開含む）をご希望の場合は、\n「詳しい実績を見たい」とメッセージをお送りください。\nパスワードをお伝えいたします！\n\nご不明な点があれば、お気軽にお問い合わせください！'),
        ('実績', '制作実績はこちらからご覧いただけます！\n\n🎬 公開実績\nhttps://www.mox-motage.com/works\n\nより詳しい実績（非公開含む）をご希望の場合は、\n「詳しい実績を見たい」とメッセージをお送りください。\nパスワードをお伝えいたします！\n\nご不明な点があれば、お気軽にお問い合わせください！'),
        ('営業時間', '営業時間は以下の通りです。\n\n平日: 9:00 - 21:00\n土日祝: 9:00 - 17:00\n不定休\n\nお気軽にお問い合わせください！'),
        # 料金・価格関連（既存）
        ('料金', '料金については、プロジェクトの内容や規模によって異なります。\n\n詳しいお見積もりをご希望の場合は、以下の情報をお知らせください。\n\n1. 映像の種類（企業紹介、イベント、商品PRなど）\n2. 映像の長さ\n3. 納期\n4. 使用目的\n\n担当者から詳しいお見積もりをお送りいたします！'),
        ('価格', '料金については、プロジェクトの内容や規模によって異なります。\n\n詳しいお見積もりをご希望の場合は、以下の情報をお知らせください。\n\n1. 映像の種類（企業紹介、イベント、商品PRなど）\n2. 映像の長さ\n3. 納期\n4. 使用目的\n\n担当者から詳しいお見積もりをお送りいたします！'),
        ('いくら', '料金については、プロジェクトの内容や規模によって異なります。\n\n詳しいお見積もりをご希望の場合は、以下の情報をお知らせください。\n\n1. 映像の種類（企業紹介、イベント、商品PRなど）\n2. 映像の長さ\n3. 納期\n4. 使用目的\n\n担当者から詳しいお見積もりをお送りいたします！'),
        ('場所', '事務所の住所は以下の通りです。\n\n〔住所〕\n〒670-0012\n兵庫県姫路市本町127番地\n大手前ダイネンBLD.II 3F\n\n〔電話番号〕\n080-1755-4598\n\n〔メール〕\nfukusuke.mox@gmail.com\n\nお越しの際は、事前にご連絡いただけると助かります！'),
        ('住所', '事務所の住所は以下の通りです。\n\n〔住所〕\n〒670-0012\n兵庫県姫路市本町127番地\n大手前ダイネンBLD.II 3F\n\n〔電話番号〕\n080-1755-4598\n\n〔メール〕\nfukusuke.mox@gmail.com\n\nお越しの際は、事前にご連絡いただけると助かります！'),
        ('メニュー', '主なサービス内容は以下の通りです。\n\n■ 企業紹介映像\n■ 商品・SNS用動画\n■ イベント撮影\n■ ドローン空撮\n■ 動画編集\n\n詳しい内容やお見積もりは、お気軽にお問い合わせください！'),
        ('サービス', '主なサービス内容は以下の通りです。\n\n■ 企業紹介映像\n■ 商品・SNS用動画\n■ イベント撮影\n■ ドローン空撮\n■ 動画編集\n\n詳しい内容やお見積もりは、お気軽にお問い合わせください！'),
    ]
    
    # 長いキーワードから優先的にチェック
    for keyword, reply in auto_replies:
        if keyword in message_text:
            return reply
    
    return None

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

def is_business_hours():
    """営業時間内かどうかを判定（平日:9:00-21:00、土日祝:9:00-17:00）"""
    now = datetime.now()
    hour = now.hour
    day_of_week = now.weekday()  # 0=月曜日, 6=日曜日
    
    # 土日祝日（5,6 = 土曜日、日曜日）
    if day_of_week >= 5:
        return 9 <= hour < 17
    # 平日
    else:
        return 9 <= hour < 21

def send_admin_notification(user_name, message_content, monetization_level):
    """管理者に高優先度顧客の通知を送信"""
    if not ADMIN_USER_ID:
        print("⚠️ ADMIN_USER_IDが設定されていません")
        return
    
    notification_text = f"🚨 高優先度顧客からのメッセージ！\n\n👤 顧客名: {user_name}\n💰 優先度: {monetization_level}\n📝 メッセージ:\n{message_content}\n\n今すぐ対応してください！"
    
    send_reply_message(ADMIN_USER_ID, notification_text)
    print(f"📢 管理者に通知送信: {user_name}")

def process_webhook_event(event):
    """Webhookイベントを処理（バックグラウンド実行用）"""
    try:
        if event['type'] == 'message':
            # メッセージイベント
            user_id = event['source']['userId']
            message_type = event['message']['type']
            
            print(f"📨 メッセージ受信: user_id={user_id}, type={message_type}")
            
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
                # Zoom背景用の動画かチェック
                if user_id in zoom_handler.pending_requests:
                    message_id = event['message']['id']
                    video_path = zoom_handler.download_line_video(message_id, CHANNEL_ACCESS_TOKEN)
                    if video_path:
                        zoom_result = zoom_handler.handle_zoom_video_message(user_id, video_path)
                        if zoom_result:
                            if isinstance(zoom_result, dict) and zoom_result.get('success'):
                                # 生成完了
                                send_reply_message(user_id, zoom_result['message'])
                                # 管理者に通知
                                if ADMIN_USER_ID:
                                    admin_msg = f"🎥 Zoom背景動画生成完了！\n\n👤 顧客: {zoom_result.get('message', '')}\n📹 動画: {zoom_result.get('video_path', '')}\n\n確認後、manage_requests.pyで配信してください。"
                                    send_reply_message(ADMIN_USER_ID, admin_msg)
                                print(f"✅ Zoom背景生成完了: {user_name}")
                            else:
                                # エラー
                                send_reply_message(user_id, zoom_result.get('message', 'エラーが発生しました。'))
                        else:
                            # まだ動画が揃っていない
                            if isinstance(zoom_result, str):
                                send_reply_message(user_id, zoom_result)
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
            
            # Zoom背景リクエストをチェック
            if message_type == 'text':
                zoom_reply = zoom_handler.handle_zoom_text_message(user_id, message_content)
                if zoom_reply:
                    send_reply_message(user_id, zoom_reply)
                    print(f"🎥 Zoom背景リクエスト処理: {user_name}")
                else:
                    # キーワードベースの自動返信をチェック
                    auto_reply = get_auto_reply(message_content)
                    if auto_reply:
                        send_reply_message(user_id, auto_reply)
                        print(f"🤖 自動返信送信: {user_name}")
                    # 営業時間外の場合は追加メッセージ
                    elif not is_business_hours():
                        after_hours_message = "営業時間外のメッセージをありがとうございます。\n\n⏰ 営業時間\n平日: 9:00～21:00\n土日祝: 9:00～17:00\n\n翌営業時間内にご返信させていただきます。\nお急ぎの場合はその旨お知らせください！"
                        send_reply_message(user_id, after_hours_message)
                        print(f"🌙 営業時間外自動返信: {user_name}")
                
                # 高優先度顧客の場合は管理者に通知
                if monetization == '高':
                    send_admin_notification(user_name, message_content, monetization)
            
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
            
            print(f"✅ メッセージ記録完了: {user_name} - {message_content}")
        
        elif event['type'] == 'follow':
            # フォローイベント
            user_id = event['source']['userId']
            print(f"👤 新規フォロー: user_id={user_id}")
            
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
            
            # 自動挨拶メッセージを送信
            welcome_message = f"{user_name}様\n\nこんにちは！映像制作 moX（もっくす）です🎬\n\n友だち追加ありがとうございます！\n\nご質問やお見積もりなど、お気軽にメッセージをお送りください。\n担当者が確認次第、ご返信させていただきます。\n\nよろしくお願いいたします！"
            send_reply_message(user_id, welcome_message)
            
            print(f"✅ 新規フォロー記録: {user_name}")
        
        elif event['type'] == 'unfollow':
            # アンフォローイベント
            user_id = event['source']['userId']
            print(f"👋 アンフォロー: user_id={user_id}")
            
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
            
            print(f"✅ アンフォロー記録: {user_id}")
    
    except Exception as e:
        print(f"❌ イベント処理エラー: {e}")
        import traceback
        traceback.print_exc()

@app.route('/webhook', methods=['POST'])
def webhook():
    """LINEからのWebhookを受信"""
    
    print(f"🔔 Webhook受信: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 署名検証
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    print(f"📝 Body length: {len(body)}")
    
    if CHANNEL_SECRET:
        hash_value = hmac.new(
            CHANNEL_SECRET.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_signature = base64.b64encode(hash_value).decode('utf-8')
        
        if signature != expected_signature:
            print(f"❌ 署名検証失敗")
            abort(400)
        else:
            print(f"✅ 署名検証成功")
    
    # イベント処理（バックグラウンドで実行）
    try:
        events = json.loads(body)['events']
        print(f"📊 イベント数: {len(events)}")
        
        # 各イベントをバックグラウンドで処理
        for event in events:
            thread = Thread(target=process_webhook_event, args=(event,))
            thread.daemon = True
            thread.start()
            print(f"🚀 バックグラウンド処理開始: {event['type']}")
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 即座に200を返す（LINEのタイムアウトを回避）
    print(f"✅ 200 OK返信")
    return 'OK', 200

@app.route('/health', methods=['GET'])
def health():
    """ヘルスチェック"""
    return 'OK', 200

@app.route('/', methods=['GET'])
def index():
    """ルートパス"""
    return 'LINE Webhook Server is running!', 200

@app.route('/download', methods=['GET'])
def download_csv():
    """ＣＳＶファイルをダウンロード"""
    from flask import send_file
    csv_file = os.path.join(os.path.dirname(__file__), 'customer_data.csv')
    
    if os.path.exists(csv_file):
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'LINE顧客管理_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    else:
        return 'データがまだありません。LINEでメッセージを送信してください。', 404

@app.route('/stats', methods=['GET'])
def stats():
    """統計情報を表示"""
    csv_file = os.path.join(os.path.dirname(__file__), 'customer_data.csv')
    
    if not os.path.exists(csv_file):
        return 'データがまだありません', 404
    
    try:
        import csv
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        total_messages = len(rows)
        needs_reply = sum(1 for row in rows if row.get('返信ステータス') == '要返信')
        high_opportunities = sum(1 for row in rows if row.get('マネタイズ機会') == '高')
        
        users = set(row.get('ユーザー名', 'Unknown') for row in rows)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>LINE顧客管理システム - 統計</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #00B900; }}
                .stat {{ background: #f0f0f0; padding: 20px; margin: 10px 0; border-radius: 5px; }}
                .stat h2 {{ margin: 0 0 10px 0; color: #333; }}
                .stat p {{ margin: 5px 0; font-size: 24px; font-weight: bold; color: #00B900; }}
                .download-btn {{ 
                    display: inline-block;
                    background: #00B900;
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin-top: 20px;
                }}
                .download-btn:hover {{ background: #009900; }}
            </style>
        </head>
        <body>
            <h1>📊 LINE顧客管理システム</h1>
            <div class="stat">
                <h2>総メッセージ数</h2>
                <p>{total_messages}件</p>
            </div>
            <div class="stat">
                <h2>返信が必要なメッセージ</h2>
                <p>{needs_reply}件</p>
            </div>
            <div class="stat">
                <h2>高優先度マネタイズ機会</h2>
                <p>{high_opportunities}件</p>
            </div>
            <div class="stat">
                <h2>総顧客数</h2>
                <p>{len(users)}名</p>
            </div>
            <a href="/download" class="download-btn">💾 CSVファイルをダウンロード</a>
            <a href="/broadcast" class="download-btn" style="background: #FF6B6B; margin-left: 10px;">📢 プッシュ配信</a>
        </body>
        </html>
        '''
        return html
    except Exception as e:
        return f'エラー: {e}', 500

@app.route('/broadcast', methods=['GET', 'POST'])
def broadcast():
    """プッシュ配信ページ"""
    from flask import render_template_string
    
    if request.method == 'POST':
        message_text = request.form.get('message', '')
        target_type = request.form.get('target_type', 'all')
        
        if not message_text:
            return 'メッセージを入力してください', 400
        
        # CSVファイルから顧客リストを取得
        csv_file = os.path.join(os.path.dirname(__file__), 'customer_data.csv')
        
        if not os.path.exists(csv_file):
            return '顧客データがありません', 404
        
        try:
            import csv
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # ターゲットをフィルタリング
            target_users = set()
            for row in rows:
                user_id = row.get('ユーザーID', '')
                if not user_id or user_id == 'Unknown':
                    continue
                
                if target_type == 'all':
                    target_users.add(user_id)
                elif target_type == 'high_priority':
                    if row.get('マネタイズ機会') == '高':
                        target_users.add(user_id)
                elif target_type == 'needs_reply':
                    if row.get('返信ステータス') == '要返信':
                        target_users.add(user_id)
                elif target_type == 'new_customers':
                    if row.get('備考') == '新規顧客':
                        target_users.add(user_id)
            
            # メッセージを送信
            success_count = 0
            for user_id in target_users:
                if send_reply_message(user_id, message_text):
                    success_count += 1
            
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>配信完了</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    h1 {{ color: #00B900; }}
                    .success {{ background: #d4edda; padding: 20px; border-radius: 5px; color: #155724; }}
                    a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #00B900; color: white; text-decoration: none; border-radius: 5px; }}
                </style>
            </head>
            <body>
                <h1>✅ 配信完了</h1>
                <div class="success">
                    <p>対象: {len(target_users)}人</p>
                    <p>成功: {success_count}人</p>
                </div>
                <a href="/stats">統計ページに戻る</a>
            </body>
            </html>
            '''
        except Exception as e:
            return f'エラー: {e}', 500
    
    # GETリクエスト: 配信フォームを表示
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>プッシュ配信</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #00B900; }
            form { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            label { display: block; margin-top: 15px; font-weight: bold; }
            select, textarea { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 3px; }
            textarea { height: 150px; font-family: Arial, sans-serif; }
            button { background: #00B900; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; margin-top: 20px; font-size: 16px; }
            button:hover { background: #009900; }
            .back-btn { display: inline-block; margin-top: 20px; padding: 10px 20px; background: #6c757d; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>📢 プッシュ配信</h1>
        <form method="POST">
            <label for="target_type">配信対象:</label>
            <select name="target_type" id="target_type">
                <option value="all">全顧客</option>
                <option value="high_priority">高優先度マネタイズ機会</option>
                <option value="needs_reply">返信が必要な顧客</option>
                <option value="new_customers">新規顧客</option>
            </select>
            
            <label for="message">メッセージ:</label>
            <textarea name="message" id="message" placeholder="配信するメッセージを入力してください..."></textarea>
            
            <button type="submit">📤 配信する</button>
        </form>
        <a href="/stats" class="back-btn">統計ページに戻る</a>
    </body>
    </html>
    '''
    return html

if __name__ == '__main__':
    # 環境変数の確認
    if not CHANNEL_ACCESS_TOKEN:
        print("⚠️ 警告: LINE_CHANNEL_ACCESS_TOKENが設定されていません")
    else:
        print("✅ LINE_CHANNEL_ACCESS_TOKEN設定済み")
    
    if not CHANNEL_SECRET:
        print("⚠️ 警告: LINE_CHANNEL_SECRETが設定されていません")
    else:
        print("✅ LINE_CHANNEL_SECRET設定済み")
    
    # サーバー起動
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 サーバー起動: ポート {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
