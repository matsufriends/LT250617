# キャラクター口調設定プロンプト自動生成プログラム

任意の名前を入力することで、その人物について自動で調べ、ChatGPT用の適切な口調設定プロンプトを自動生成するプログラムです。

## 機能

- **Wikipedia情報収集**: 基本的な人物情報を取得
- **Google検索**: 追加の関連情報を収集
- **YouTube字幕抽出**: 動画の字幕から実際の話し方を分析
- **ChatGPT API**: 収集した情報を整理して高品質なプロンプトを生成
- **キャッシュ機能**: 同一人物の再検索を高速化

## セットアップ

### 1. 仮想環境の作成とライブラリのインストール

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
source venv/bin/activate

# 必要なライブラリをインストール
pip install -r requirements.txt
```

### 2. OpenAI API Keyの設定

以下のいずれかの方法でAPI Keyを設定してください：

**方法1: 環境変数で設定**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**方法2: コマンドライン引数で指定**
```bash
python main.py "キャラクター名" --api-key "your-api-key-here"
```

## 使用方法

### 基本的な使用方法

```bash
# 仮想環境を有効化してから実行
source venv/bin/activate
python main.py "ドラえもん"
```

### オプション

```bash
python main.py "キャラクター名" [オプション]
```

#### 利用可能なオプション

- `--api-key`: OpenAI API Keyを直接指定
- `--no-cache`: キャッシュを使用せずに新規取得
- `--output`, `-o`: 結果を指定したファイルに保存

### 使用例

```bash
# 基本的な使用
python main.py "坂本龍馬"

# キャッシュを使わずに新規取得
python main.py "織田信長" --no-cache

# 結果をファイルに保存
python main.py "夏目漱石" -o prompt_natsume.txt

# API Keyを直接指定
python main.py "宮本武蔵" --api-key "sk-..."
```

## 出力例

プログラムを実行すると、以下のような形式でプロンプトが生成されます：

```
=== キャラクター口調プロンプト生成: ドラえもん ===

📚 情報収集中...
📖 Wikipedia情報を収集中...
🔍 Google検索情報を収集中...
🎥 YouTube情報を収集中...
🤖 プロンプト生成中...

============================================================
生成されたプロンプト:
============================================================

あなたは「ドラえもん」として振る舞ってください。

以下の特徴を持って話してください：
- 一人称は「ぼく」を使用
- 語尾に「〜だよ」「〜なんだ」を多用
- 優しく親しみやすい口調
- のび太への愛情を込めた話し方
- 時々関西弁が混じることがある
...
============================================================
```

## プロジェクト構造

```
├── main.py                 # メインプログラム
├── requirements.txt        # 必要なライブラリ
├── collectors/            # 情報収集モジュール
│   ├── wikipedia_collector.py
│   ├── google_collector.py
│   └── youtube_collector.py
├── generators/            # プロンプト生成モジュール
│   └── prompt_generator.py
└── utils/                 # ユーティリティ
    └── __init__.py
```

## 注意事項

- OpenAI API使用料が発生します（gpt-3.5-turboで1回あたり約1〜2円程度）
- Google検索の大量実行はIPブロックの可能性があります
- YouTube字幕が無効な動画は取得できません
- インターネット接続が必要です

## トラブルシューティング

### API Keyエラー
```
エラー: OpenAI API Keyが設定されていません。
```
→ 環境変数またはコマンドライン引数でAPI Keyを設定してください

### インポートエラー
```
ModuleNotFoundError: No module named 'openai'
```
→ `pip install -r requirements.txt` を実行してください

### 検索結果が見つからない
→ 名前の表記を変更するか、より一般的な名前で試してください

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
