# Google Custom Search API セットアップガイド

## 概要
Google Custom Search APIを使用するには、以下の2つが必要です：
1. **API Key** - Google Cloud Platformで取得
2. **Search Engine ID (CX)** - Programmable Search Engineで作成

## 手順

### 1. Google Cloud Platform でAPIキーを取得

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. プロジェクトを作成または選択
3. 「APIとサービス」→「認証情報」を開く
4. 「認証情報を作成」→「APIキー」をクリック
5. 作成されたAPIキーをコピー

### 2. Custom Search Engine (検索エンジン) を作成

1. [Programmable Search Engine](https://programmablesearchengine.google.com/)にアクセス
2. 「検索エンジンを追加」をクリック
3. 設定：
   - **検索するサイト**: `*.com` を入力（全体を検索する場合）
   - **言語**: 日本語
   - **検索エンジンの名前**: 任意の名前（例：「キャラクター検索」）
4. 「作成」をクリック
5. 作成後、「コントロールパネル」を開く
6. **検索エンジン ID** をコピー（`cx=` の後の文字列）

### 3. 検索エンジンの設定を調整

1. コントロールパネルで「検索機能」を開く
2. 「ウェブ全体を検索」をONにする
3. 「画像検索」をOFFにする（テキスト検索のみ使用）
4. 「セーフサーチ」をOFFにする

### 4. 環境変数を設定

```bash
# .envファイルまたはシェルで設定
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_CX="your-search-engine-id-here"
```

### 5. APIを有効化

Google Cloud Consoleで以下のAPIを有効化：
1. 「APIとサービス」→「ライブラリ」
2. 「Custom Search API」を検索
3. 「有効にする」をクリック

## トラブルシューティング

### 404エラーが出る場合
- Search Engine ID (CX) が正しいか確認
- 検索エンジンが削除されていないか確認
- URLに余分なスペースが含まれていないか確認

### 403エラーが出る場合
- APIキーが正しいか確認
- Custom Search APIが有効になっているか確認
- 課金設定が有効か確認

### 429エラーが出る場合
- 無料枠（100クエリ/日）を超過
- 有料プランにアップグレードするか、翌日まで待つ

## 料金

- **無料枠**: 100クエリ/日
- **有料**: $5 per 1,000クエリ（100クエリ/日を超えた分）

## 参考リンク

- [Custom Search API ドキュメント](https://developers.google.com/custom-search/v1/overview)
- [Programmable Search Engine](https://programmablesearchengine.google.com/)
- [Google Cloud Console](https://console.cloud.google.com/)