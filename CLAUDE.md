# 技術仕様書

## アーキテクチャ

```
main.py → CharacterInfoService → CollectorFactory → 各種Collector
                                                      ↓
                                                 BaseCollector
```

### 主要コンポーネント

- **CharacterInfoService** (`core/`): ビジネスロジック統括
- **CollectorFactory** (`core/`): 検索エンジンの動的生成
- **BaseCollector** (`core/interfaces.py`): 統一インターフェース
- **各種Collector** (`collectors/`): Wikipedia、Google、Bing、DuckDuckGo、ChatGPT、YouTube
- **PromptGenerator** (`generators/`): ChatGPT APIでプロンプト生成
- **ExecutionLogger** (`utils/`): 実行ログとパフォーマンス分析

## データフロー

1. **情報収集**
   - Wikipedia → 基本情報
   - Web検索 → 詳細情報とセリフ
   - YouTube → 字幕からセリフ抽出

2. **プロンプト生成**
   - 収集データをChatGPT APIに送信
   - カオス誇張モード（3倍の強度）で生成
   - 商標配慮（二次創作として明記）

## 主要機能

### CharacterQuote
- Web/YouTubeから具体的セリフを抽出
- 信頼性スコア（0.0-1.0）で品質管理
- 最大30個をプロンプトに含める

### 検索エンジン選択
```python
# 優先順位
1. ChatGPT検索（--use-chatgpt-search）
2. Bing（--use-bing）
3. DuckDuckGo（--use-duckduckgo）
4. Google（デフォルト、レート制限あり）
```

### エラーハンドリング
- `CharacterPromptError`: 基底例外
- `CollectorError`: 収集エラー
- `SearchEngineError`: 検索エラー
- `APIError`: API呼び出しエラー

## 設定（config.py）

```python
# 主要設定
OPENAI_MODEL = "gpt-4o"
OPENAI_MAX_TOKENS = 4000
GOOGLE_DELAY = 10.0  # レート制限対策
YOUTUBE_MAX_URLS = 20
YOUTUBE_MAX_TRANSCRIPTS = 10
```

## 拡張方法

### 新しいCollector追加
```python
class NewCollector(SearchEngineCollector):
    def collect_info(self, name: str, **kwargs) -> CollectionResult:
        # 実装
        
    def search_youtube_videos(self, name: str, **kwargs) -> List[str]:
        # YouTube URL検索実装
```

### CollectorFactoryに登録
```python
# SearchEngineTypeに追加
# create_search_engine_collectorに分岐追加
```

## 開発時の注意

1. **レート制限**: Google検索は10秒遅延必須
2. **API Key管理**: 環境変数使用、コード埋め込み禁止
3. **ログ出力**: ExecutionLogger経由で統一
4. **エラー処理**: 必ずtry-exceptでラップ

## 制約

- キャラクター固有の最適化禁止（中立性維持）
- 収集データのみ使用（創作禁止）
- 極端な誇張表現必須（エンタメ重視）
- 商標配慮（二次創作明記）