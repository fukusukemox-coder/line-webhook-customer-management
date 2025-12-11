# LINE顧客管理システム

LINEメッセージを自動的に記録し、顧客管理を効率化するシステムです。

## 機能

- ✅ LINEメッセージの自動記録（テキスト、画像、動画、音声、ファイル、位置情報、スタンプ）
- ✅ フォロー/アンフォローイベントの記録
- ✅ 返信が必要なメッセージの自動検出
- ✅ マネタイズ機会の自動分析（高/中/低/要確認）
- ✅ CSVファイルのダウンロード（BOM付きUTF-8、Excelで文字化けなし）
- ✅ 統計ダッシュボード

## システム構成

- **プラットフォーム**: Render.com（無料プラン）
- **フレームワーク**: Flask（Python）
- **LINE Messaging API**: Channel ID 2008640179
- **Webhook URL**: https://line-webhook-customer-management.onrender.com/webhook
- **GitHubリポジトリ**: https://github.com/fukusukemox-coder/line-webhook-customer-management

## エンドポイント

### 1. Webhook（POST /webhook）
LINEからのメッセージを受信するエンドポイント。

### 2. 統計ダッシュボード（GET /stats）
URL: https://line-webhook-customer-management.onrender.com/stats

表示内容：
- 総メッセージ数
- 返信が必要なメッセージ数
- 高優先度マネタイズ機会数
- 総顧客数

### 3. CSVダウンロード（GET /download）
URL: https://line-webhook-customer-management.onrender.com/download

CSVファイルの形式：
- エンコーディング: BOM付きUTF-8（Excelで文字化けなし）
- 列: タイムスタンプ、ユーザーID、ユーザー名、メッセージタイプ、メッセージ内容、返信ステータス、マネタイズ機会、備考

## 使い方

### 1. メッセージの自動記録
LINEでメッセージを受信すると、自動的にCSVファイルに記録されます。

### 2. 統計の確認
https://line-webhook-customer-management.onrender.com/stats にアクセスして、統計を確認します。

### 3. CSVファイルのダウンロード
統計ダッシュボードの「💾 CSVファイルをダウンロード」ボタンをクリックするか、
https://line-webhook-customer-management.onrender.com/download に直接アクセスします。

### 4. Google Sheetsにインポート
1. ダウンロードしたCSVファイルをGoogle Sheetsで開く
2. 「ファイル」→「インポート」→「アップロード」でCSVファイルを選択
3. インポート設定で「区切り文字」を「カンマ」に設定

## 返信ステータスの判定基準

以下のキーワードが含まれる場合、「要返信」と判定されます：
- `?`, `？`
- `どう`, `いつ`, `どこ`, `なに`
- `教えて`, `知りたい`, `できます`, `お願い`

それ以外は「確認済み」と判定されます。

## マネタイズ機会の判定基準

### 高
- `見積`, `予算`, `料金`, `価格`, `費用`
- `依頼`, `発注`, `契約`, `購入`

### 中
- `興味`, `詳しく`, `教えて`, `知りたい`
- `相談`, `検討`

### 低
- `ありがとう`, `よろしく`, `わかりました`, `OK`

### 要確認
- 上記のいずれにも該当しない場合

## 注意事項

### Render.com無料プランの制限
- サーバーが非アクティブ時（15分間リクエストがない場合）にスリープします
- スリープから復帰するまでに最大50秒かかることがあります
- **重要**: サーバーが再起動すると、CSVファイルが消える可能性があります

### 推奨事項
- **定期的にCSVファイルをダウンロード**してバックアップを取ってください
- 重要なデータは、Google Sheetsなどの外部ストレージに保存してください

## デプロイ

GitHubにプッシュすると、Render.comが自動的に新しいコードをデプロイします。

```bash
git add .
git commit -m "Update message"
git push
```

## 環境変数

Render.comの環境変数に以下を設定してください：

- `LINE_CHANNEL_SECRET`: LINEチャネルシークレット
- `LINE_CHANNEL_ACCESS_TOKEN`: LINEチャネルアクセストークン

## トラブルシューティング

### メッセージが記録されない
1. Render.comのログを確認
2. LINE Developers Consoleでwebhook URLが正しく設定されているか確認
3. Webhookの利用が「オン」になっているか確認

### CSVファイルが消えた
Render.comの無料プランでは、サーバーが再起動するとファイルが消えます。定期的にダウンロードしてバックアップを取ってください。

### 文字化けする
CSVファイルはBOM付きUTF-8で保存されているため、Excelで正しく開けるはずです。それでも文字化けする場合は、メモ帳で開いて確認してください。

## ライセンス

MIT License

## 作成者

福助（映像制作 moX）
