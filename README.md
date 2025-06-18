# キャラクター口調設定プロンプト自動生成プログラム

任意のキャラクター名から、ChatGPT用の極端に誇張された口調設定プロンプトを自動生成します。

## セットアップ

```bash
# 環境準備
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# API Key設定（必須）
export OPENAI_API_KEY="your-openai-api-key"
```

## 使い方

```bash
# 基本（推奨）
python main.py "ドラえもん" --use-chatgpt-search

# 高速実行
python main.py "初音ミク" --use-chatgpt-search --no-youtube

# Google API使用（要設定）
python main.py "ピカチュウ"
```

## オプション

| オプション | 説明 |
|------------|------|
| `--use-chatgpt-search` | ChatGPT検索（レート制限なし） |
| `--use-bing` | Bing検索を使用 |
| `--use-duckduckgo` | DuckDuckGo検索を使用 |
| `--no-youtube` | YouTube字幕取得を無効化 |
| `--output -o` | ファイル出力 |

## トラブルシューティング

- **検索レート制限エラー**: `--use-chatgpt-search` を使用
- **API Keyエラー**: 環境変数 `OPENAI_API_KEY` を設定
- **検索結果なし**: キャラクター名の表記を変更

## 詳細情報

- 技術仕様: `CLAUDE.md`
- Google API設定: `GOOGLE_SETUP.md`