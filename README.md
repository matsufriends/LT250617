# キャラクター口調設定プロンプト自動生成プログラム

任意の名前を入力することで、その人物について自動で調べ、ChatGPT用の適切な口調設定プロンプトを自動生成するプログラムです。

## 主な特徴

- **🔍 多様な検索エンジン対応**: Google、Bing、DuckDuckGo、ChatGPT知識ベース
- **📖 包括的な情報収集**: Wikipedia、Web検索、YouTube字幕から実際の話し方を分析
- **🤖 高品質なプロンプト生成**: ChatGPT APIで収集した情報を整理・構造化
- **⚡ 安定した動作**: レート制限回避とエラー耐性を重視した設計
- **📊 詳細ログ**: 実行過程とAPI呼び出しを完全記録

## 🚀 クイックスタート

### 1. 環境準備

```bash
# 仮想環境を作成・有効化
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt
```

### 2. API Key設定

```bash
# OpenAI API Key（必須）
export OPENAI_API_KEY="your-openai-api-key"

# Google Custom Search API（推奨・レート制限回避）
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX="your-custom-search-engine-id"
```

### 3. 実行

```bash
# 基本的な使用方法
python main.py "ドラえもん"

# 高速・安定動作（推奨）
python main.py "ドラえもん" --use-chatgpt-search
```

## 📋 詳細セットアップ

### OpenAI API Key（必須）

[OpenAI Platform](https://platform.openai.com/account/api-keys)でAPI Keyを取得：

**環境変数で設定（推奨）**
```bash
export OPENAI_API_KEY="sk-..."
```

**コマンドライン引数で指定**
```bash
python main.py "キャラクター名" --api-key "sk-..."
```

### Google Custom Search API（推奨）

レート制限エラー（429エラー）を回避するため、Google Custom Search APIの使用を強く推奨：

1. **Google Cloud Console設定**
   - [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
   - Custom Search APIを有効化
   - API Keyを作成

2. **Programmable Search Engine設定**
   - [Programmable Search Engine](https://programmablesearchengine.google.com/)でカスタム検索エンジンを作成
   - 検索対象: `*`（全Web検索）
   - Search Engine ID（CX）を取得

3. **環境変数設定**
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   export GOOGLE_CX="your-search-engine-id"
   ```

## 🎯 使用方法とオプション

### 基本コマンド

```bash
python main.py "キャラクター名" [オプション]
```

### 推奨オプション

```bash
# 最も安定した方法（ChatGPT検索）
python main.py "初音ミク" --use-chatgpt-search

# ファイル出力付き
python main.py "ずんだもん" --use-chatgpt-search -o result.txt

# 高速実行（YouTube無効）
python main.py "織田信長" --use-chatgpt-search --no-youtube
```

### 全オプション一覧

| オプション | 説明 |
|------------|------|
| `--api-key` | OpenAI API Keyを直接指定 |
| `--output`, `-o` | 結果をファイルに保存 |
| `--use-chatgpt-search` | **推奨**: ChatGPT知識ベース検索（レート制限なし） |
| `--use-bing` | Bing検索を使用 |
| `--use-duckduckgo` | DuckDuckGo検索を使用 |
| `--no-google` | Google検索を無効化（レート制限回避） |
| `--no-youtube` | YouTube字幕収集を無効化（高速化） |

### 検索エンジン選択ガイド

| 検索エンジン | 推奨度 | メリット | デメリット |
|--------------|--------|----------|------------|
| **ChatGPT知識ベース** | ⭐⭐⭐ | レート制限なし、高速、安定 | 2023年4月以降の情報なし |
| **Google Custom Search API** | ⭐⭐ | 最新情報、高精度 | API Key設定が必要 |
| **Bing検索** | ⭐ | 設定不要、安定 | 検索精度が劣る場合あり |
| **Google検索（標準）** | △ | 高精度 | レート制限エラーのリスク |
| **DuckDuckGo検索** | △ | プライバシー重視 | エラー率が高い |

## 📁 プロジェクト構造

```
├── main.py                     # メインプログラム
├── config.py                   # 設定管理（リファクタリング後）
├── requirements.txt            # 依存関係
│
├── core/                      # 🆕 コアシステム
│   ├── character_info_service.py   # サービス層
│   ├── collector_factory.py       # ファクトリーパターン
│   ├── interfaces.py              # 共通インターフェース
│   └── exceptions.py              # カスタム例外
│
├── collectors/                # 情報収集モジュール
│   ├── wikipedia_collector.py     # Wikipedia情報
│   ├── google_collector.py        # Google検索（Custom Search API対応）
│   ├── bing_collector.py          # Bing検索
│   ├── duckduckgo_collector.py    # DuckDuckGo検索
│   ├── chatgpt_collector.py       # ChatGPT知識ベース
│   └── youtube_collector.py       # YouTube字幕
│
├── generators/                # プロンプト生成
│   └── prompt_generator.py
│
├── utils/                     # 🆕 共通ユーティリティ
│   ├── api_client.py             # OpenAI API クライント
│   ├── execution_logger.py       # 実行ログ管理
│   ├── text_processor.py         # テキスト処理
│   ├── timing.py                 # 時間計測
│   └── http_client.py            # HTTP通信
│
└── cache/                     # ログファイル
    ├── execution_log_*.json       # 実行ログ
    └── latest_execution_log.json  # 最新ログ
```

## 💰 コスト

### OpenAI API（gpt-4oモデル）
- **プロンプト生成**: 約5〜15円/回
- **自己紹介生成**: 約2〜5円/回  
- **ポリシー対応版**: 約5〜10円/回
- **合計**: 約10〜30円/回

### Google Custom Search API
- **1日100回まで無料**
- **100回以降**: $5/1000クエリ
- **安定性向上**により実質的なコスト削減効果

### その他
- Wikipedia、YouTube字幕収集：**完全無料**

## 🔧 トラブルシューティング

### よくあるエラーと対処法

#### API Keyエラー
```
エラー: OpenAI API Keyが設定されていません。
```
**対処法**: 環境変数またはコマンドライン引数でAPI Keyを設定

#### レート制限エラー（429エラー）
```
Google検索でレート制限エラーが発生しました
```
**対処法**: 
1. `--use-chatgpt-search`でChatGPT検索に切り替え（推奨）
2. Google Custom Search APIを設定
3. `--use-bing`でBing検索に切り替え

#### インポートエラー
```
ModuleNotFoundError: No module named 'openai'
```
**対処法**: 仮想環境で`pip install -r requirements.txt`を実行

#### 検索結果が見つからない
**対処法**:
1. 名前の表記を変更（ひらがな/カタカナ/漢字）
2. `--use-chatgpt-search`を試行
3. より一般的な名前で検索

### 推奨トラブルシューティング手順

1. **ChatGPT検索を試す**（最も安定）
   ```bash
   python main.py "キャラクター名" --use-chatgpt-search
   ```

2. **YouTube無効で高速化**
   ```bash
   python main.py "キャラクター名" --use-chatgpt-search --no-youtube
   ```

3. **ログ確認**
   ```bash
   cat cache/latest_execution_log.json
   ```

## 📊 出力例

```
=== キャラクター口調プロンプト生成: ドラえもん ===
🤖 検索エンジン: ChatGPT知識ベース（完全AI検索）
    ✨ Web検索不要でレート制限なし、2023年4月までの知識を使用
🎥 YouTube字幕: 有効

📚 情報収集中...
📖 Wikipedia情報を収集中...
🤖 ChatGPT知識ベース検索中...
🎥 YouTube情報を収集中...
🤖 プロンプト生成中...

============================================================
生成されたプロンプト:
============================================================

あなたは「ドラえもん」として振る舞ってください。

以下の特徴を持って話してください：
- 一人称は「ぼく」を使用
- 語尾に「〜だよ」「〜なんだ」を多用
- 優しく親しみやすい口調で話す
- のび太への愛情を込めた話し方
- 時々関西弁が混じることがある
- 困った時は「なんてこった」「大変だ」などの表現を使用

感情表現：
- 喜び: 「やったー！」「すごいじゃないか！」
- 困惑: 「えー？」「どうしよう」  
- 怒り: 「もう！」「だめだよ」

セリフ例：
- 「のび太くん、宿題はやったの？」
- 「ぼくのポケットから道具を出してあげるよ」
- 「みんなで仲良くしなくちゃだめだよ」

============================================================

📊 実行ログ: セッションID 20241216_143052
   - 実行ステップ: 4/4
   - API呼び出し: 3/3
   - ログファイル: cache/execution_log_20241216_143052.json
```

## ⚖️ ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

バグ報告や機能提案は Issue でお願いします。プルリクエストも歓迎します。

---

**開発者向け情報**: より詳細な技術仕様については `CLAUDE.md` をご覧ください。