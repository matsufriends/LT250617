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

# Google API設定（推奨）
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX="your-search-engine-id"
```

Google API設定方法は `GOOGLE_SETUP.md` を参照してください。

## 使い方

```bash
# 基本（Google API使用）
python main.py "ドラえもん"

# ChatGPT知識ベース使用（Google API未設定時の代替）
python main.py "初音ミク" --use-chatgpt-search

# 高速実行（YouTube無効）
python main.py "ピカチュウ" --no-youtube
```

## オプション

| オプション | 説明 |
|------------|------|
| `--use-chatgpt-search` | ChatGPT検索（Google API未設定時の代替） |
| `--use-bing` | Bing検索を使用 |
| `--use-duckduckgo` | DuckDuckGo検索を使用 |
| `--no-youtube` | YouTube字幕取得を無効化 |
| `--output -o` | ファイル出力 |

## トラブルシューティング

- **Google API設定エラー**: `GOOGLE_SETUP.md` を参照して設定
- **レート制限エラー**: `--use-chatgpt-search` を使用
- **API Keyエラー**: 環境変数 `OPENAI_API_KEY` を設定
- **検索結果なし**: キャラクター名の表記を変更

## 詳細情報

- 技術仕様: `CLAUDE.md`
- Google API設定: `GOOGLE_SETUP.md`