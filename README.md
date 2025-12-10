# LINE顧客管理システム

LINEメッセージを自動的に記録し、返信漏れとマネタイズ機会を分析するWebhookシステム

## 機能

- LINEメッセージの自動記録
- 返信漏れ検知
- マネタイズ機会分析
- Google Driveへの自動エクスポート

## セットアップ

### 環境変数

以下の環境変数を設定してください：

- `LINE_CHANNEL_SECRET`: LINEチャネルシークレット
- `LINE_CHANNEL_ACCESS_TOKEN`: LINEチャネルアクセストークン
- `PORT`: ポート番号（デフォルト: 5000）

### デプロイ

Render.comでのデプロイを推奨します。

1. このリポジトリをRender.comに接続
2. 環境変数を設定
3. デプロイ

### 使い方

1. Webhook URLをLINE Developers Consoleに設定
2. LINEでメッセージを受信すると自動的に記録されます
3. `analyze_customers.py`を実行して分析レポートを生成

## ライセンス

MIT
