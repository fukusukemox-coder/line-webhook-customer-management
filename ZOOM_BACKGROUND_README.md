# Zoom背景動画自動生成機能

LINEからのリクエストで自動的にZoom背景動画を生成する機能です。

## 機能概要

1. **LINEでリクエスト受信**
   - ユーザーが「Zoom背景 <名前>」とメッセージ送信
   - 動画素材を2本送信

2. **自動で動画生成**
   - Googleフォームのデータと照合
   - テンプレート画像を使用
   - 15秒のZoom背景動画を自動生成

3. **管理者確認**
   - 生成完了後、管理者に通知
   - 管理者が確認してから配信

## 使い方

### 顧客側の操作

1. LINE公式アカウントで「Zoom背景 福山修平」と送信
2. 動画素材を2本送信
   - 1本目: カット1用（自己紹介）
   - 2本目: カット2用（サービス紹介）
3. 生成完了の通知を待つ

### 管理者側の操作

1. **生成完了通知を受信**
   - LINEで管理者に通知が届く

2. **動画を確認**
   ```bash
   python3 manage_requests.py
   ```
   - リクエスト一覧が表示される
   - 番号を入力して詳細を確認

3. **配信**
   ```bash
   s [番号]
   ```
   - 確認後、LINEに配信

## Render.com設定

### 環境変数

以下の環境変数を設定してください:

```
LINE_CHANNEL_SECRET=<LINEチャネルシークレット>
LINE_CHANNEL_ACCESS_TOKEN=<LINEアクセストークン>
ADMIN_USER_ID=<管理者のLINE USER ID>
```

### ビルドコマンド

Renderのダッシュボードで以下を設定:

```
Build Command: ./render-build.sh
```

### 起動コマンド

```
Start Command: python3 webhook_server.py
```

## ファイル構成

```
line-webhook-customer-management/
├── webhook_server.py              # メインサーバー
├── zoom_background_handler.py     # Zoom背景処理
├── zoom_bg_automation.py          # 動画生成スクリプト
├── manage_requests.py             # 管理ツール
├── templates/                     # テンプレート画像
│   ├── template_cut1_fixed.png
│   ├── template_cut2_based_on_cut1.png
│   └── template_cut3_based_on_cut1.png
├── zoom_pending/                  # 一時ファイル
├── zoom_output/                   # 生成動画
└── zoom_requests/                 # リクエスト情報
```

## トラブルシューティング

### 問題: ffmpegが見つからない

**解決策:**
1. Renderのダッシュボードで「Build Command」を確認
2. `./render-build.sh`が設定されているか確認

### 問題: テンプレート画像が見つからない

**解決策:**
1. `templates/`ディレクトリが存在するか確認
2. 以下のファイルが存在するか確認:
   - `template_cut1_fixed.png`
   - `template_cut2_based_on_cut1.png`
   - `template_cut3_based_on_cut1.png`

### 問題: Googleフォームデータが取得できない

**解決策:**
1. `zoom_bg_automation.py`の`load_form_data()`を確認
2. rcloneの設定が必要な場合は、別途設定

## 今後の改善

1. **Googleフォームデータの自動取得**
   - 現在はローカルファイルから読み込み
   - Google Sheets APIで自動取得に変更

2. **テンプレート画像の動的生成**
   - 顧客情報（カラー、雰囲気）に応じて自動生成

3. **動画配信の自動化**
   - 管理者確認後、自動でLINE配信

4. **エラーハンドリング強化**
   - より詳細なエラーメッセージ
   - リトライ機能

## ライセンス

このシステムは映像制作moX様専用です。
