# MIPT分野特化型 論文自動要約・通知システム 仕様書 v3

## 更新履歴

| バージョン | 日付 | 変更内容 |
|-----------|------|---------|
| v1 | - | 初版（Linux/cron/Ollama前提） |
| v2 | 2026-04-07 | 実行環境・推論バックエンド・通知先を実態に合わせて全面改訂 |
| v3 | 2026-04-07 | 実行基盤をGitHub Actionsに変更。Ollamaフォールバック廃止。ディレクトリ構成・エラーハンドリング・ロードマップを対応修正 |
| v4 | 2026-04-08 | cond-mat.stat-mech -> cond-matに検索範囲を増加、実行日と同じ日の新着論文を取得するように変更 |

---

## 1. システム概要

本システムは、arXivの量子情報分野（quant-ph等）から最新の論文情報を毎朝自動取得し、LLMを用いてMIPT（測定誘起相転移）に関連する重要論文を抽出・要約し、Notionデータベースに自動登録するパイプラインである。

### 1.1 設計方針

- **サーバーレス・クラウド完結**: GitHub Actionsで日次実行。ローカルPCの電源・スリープに依存しない。
- **完全自動・無人運用**: スケジュールトリガーによる日次実行。障害時はログに記録し、翌日リトライ。
- **コスト0運用**: GitHub Actions無料枠 + Gemini API無料枠 + arXiv API + Notion API（無料プラン）で完結。

---

## 2. 技術スタック

| 項目 | 選定 | 備考 |
|------|------|------|
| 実行環境 | GitHub Actions（ubuntu-latest） | 無料枠: 2,000分/月。日次1回なら月30分程度 |
| 言語 | Python 3.12 | |
| スケジューラ | GitHub Actions `schedule` (cron構文) | 毎朝 JST 7:00（UTC 22:00）に実行 |
| データソース | arXiv API（Primary） | Semantic Scholar API（Optional、フェーズ2） |
| 推論エンジン | Google Gemini API（無料枠） | `gemini-2.0-flash` 推奨。無料枠: 15 RPM / 1500 RPD |
| 通知・保存先 | Notion API → データベース | |
| シークレット管理 | GitHub Actions Secrets | `GEMINI_API_KEY`, `NOTION_API_KEY`, `NOTION_DATABASE_ID` |

### 2.1 GitHub Actions の構成

#### ワークフロー定義（`.github/workflows/daily-summarize.yml`）

```yaml
name: Daily MIPT Paper Summarizer

on:
  schedule:
    # JST 7:00 = UTC 22:00 (前日)
    - cron: '0 22 * * *'
  workflow_dispatch:  # 手動実行も可能

jobs:
  summarize:
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run summarizer
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
          NOTION_DATABASE_ID: ${{ secrets.NOTION_DATABASE_ID }}
        run: python src/main.py
```

#### シークレット設定手順

1. GitHubリポジトリの Settings → Secrets and variables → Actions
2. 以下の3つを「New repository secret」で登録:
   - `GEMINI_API_KEY`: Google AI StudioのAPIキー
   - `NOTION_API_KEY`: Notionインテグレーションのシークレット（`secret_xxx`）
   - `NOTION_DATABASE_ID`: 対象データベースのID

#### 注意事項

- GitHub Actionsの `schedule` は指定時刻から **5〜15分程度遅延** する場合がある（正常動作）
- `workflow_dispatch` を設定しているため、GitHub上から手動実行も可能（デバッグ・テスト時に有用）
- 無料枠（2,000分/月）に対し、日次実行は月30分程度。余裕は十分

### 2.2 Gemini API 無料枠の確認（2026年4月時点）

> **重要**: 無料枠の仕様は変更される可能性がある。開発開始前に最新の情報を確認すること。
> https://ai.google.dev/pricing

日次で10〜20本の論文アブストラクトを処理する想定では、無料枠（1日あたり1,500リクエスト）で十分に収まる。

---

## 3. ディレクトリ構成

```
mipt-paper-summarizer/
├── .github/
│   └── workflows/
│       └── daily-summarize.yml  # GitHub Actions ワークフロー
├── README.md
├── requirements.txt
├── .env.example            # テンプレート（Secrets移行後も開発用に残す）
├── config/
│   ├── keywords.yaml       # 検索キーワード・スコアリング設定
│   └── prompts.yaml        # LLMプロンプト定義
├── src/
│   ├── __init__.py
│   ├── main.py             # エントリポイント
│   ├── fetcher.py          # arXiv API 論文取得
│   ├── filter.py           # キーワードフィルタリング・スコアリング
│   ├── summarizer.py       # LLM要約（Gemini APIクライアント）
│   ├── notion_client.py    # Notion API 書き込み
│   └── models.py           # データクラス定義（Paper, Summary等）
└── tests/
    ├── test_fetcher.py
    ├── test_filter.py
    └── test_summarizer.py
```

---

## 4. 機能要件

### 4.1 論文取得・フィルタリング（Fetch & Filter）

#### データソース
- arXiv API（Atom/RSS）
- クエリ: `cat:quant-ph OR cat:cond-mat`
- 取得範囲: 実行日と同じ日の新着論文（週末を跨ぐ場合に備え48時間）

#### キーワード設定（`config/keywords.yaml`）

```yaml
# 一次フィルタ: いずれかを含む論文のみ通過
primary_keywords:
  - "measurement-induced"
  - "monitored quantum"
  - "entanglement transition"
  - "hybrid circuit"

# スコアリング: マッチしたキーワードごとに加点
scoring_keywords:
  - keyword: "post-selection"
    weight: 3
  - keyword: "error correction"
    weight: 3
  - keyword: "decoding"
    weight: 2
  - keyword: "feedback"
    weight: 2
  - keyword: "Clifford"
    weight: 1
  - keyword: "Haar random"
    weight: 1

# スコア閾値: この値以上の論文のみLLMに渡す
score_threshold: 2
```

#### フィルタリングフロー

1. arXiv APIからraw論文リストを取得
2. `primary_keywords` による一次フィルタ（OR条件）
3. 通過した論文に対し `scoring_keywords` でスコア計算
4. `score_threshold` 以上の論文のみを要約対象とする
5. スコア降順でソート

### 4.2 要約・分析（Summarize & Analyze）

#### プロンプト定義（`config/prompts.yaml`）

```yaml
system_prompt: |
  あなたは量子情報科学および統計力学、特にMIPT（測定誘起相転移）の専門家です。
  与えられた論文のAbstractを読み、以下の項目を日本語で簡潔に抽出してください。
  出力は必ず以下のYAML形式のみで返してください。余分な説明は不要です。

  core_question: この論文が解決しようとしている問いを1〜2文で
  novelty: 手法の新規性（特にポストセレクション回避、新しい測定スキームに注目）を1〜2文で
  stabilizer_connection: 量子誤り訂正・デコードとの関連（無ければ「なし」）
  category: 以下から1つ選択 [実験向き, 純粋理論, 数値計算]
  importance: 以下から1つ選択 [A:最優先, B:標準, C:参考]
  one_line: 一行要約（30字以内）

user_prompt_template: |
  タイトル: {title}
  著者: {authors}
  URL: {url}
  Abstract: {abstract}
```

#### パース戦略

- Gemini API: YAML形式での構造化出力を期待。パース成功時はフィールドごとに分解。
- パース失敗時のフォールバック: 生テキストをそのまま `one_line` フィールドに格納し、他フィールドは `"解析失敗"` で埋める。

### 4.3 Notion連携（Deliver）

#### Notionデータベースのスキーマ

| プロパティ名 | 型 | 内容 |
|-------------|-----|------|
| タイトル | Title | 論文タイトル |
| URL | URL | arXivリンク |
| 投稿日 | Date | arXiv投稿日 |
| 重要度 | Select | A / B / C |
| カテゴリ | Select | 実験向き / 純粋理論 / 数値計算 |
| コア・プロブレム | Rich Text | LLM出力 |
| 手法の新規性 | Rich Text | LLM出力 |
| QEC関連 | Rich Text | LLM出力 |
| ひとこと要約 | Rich Text | LLM出力 |
| フィルタスコア | Number | キーワードスコアリングの値 |
| ステータス | Select | 未読 / 読了 / 要精読 |

#### セットアップ手順

1. [Notion Integrations](https://www.notion.so/my-integrations) でインテグレーションを作成
2. 発行されたAPIキー（`secret_xxx`）を `.env` に設定
3. 対象データベースでインテグレーションを「接続」として追加
4. データベースIDを `.env` に設定

```env
# .env.example（ローカル開発用。本番ではGitHub Actions Secretsを使用）
GEMINI_API_KEY=your_gemini_api_key
NOTION_API_KEY=secret_xxx
NOTION_DATABASE_ID=your_database_id
```

---

## 5. データフロー

```
┌──────────────────────────────────────────────────────┐
│  GitHub Actions schedule (毎朝 JST 7:00 / UTC 22:00)│
│  or workflow_dispatch（手動実行）                     │
│  → python src/main.py                                │
└──────────┬───────────────────────────────────────────┘
           │
           ▼
┌────────────────────────┐     ┌───────────────────┐
│  1. Fetch              │     │  arXiv API        │
│  arxiv パッケージで取得 │◄────│  quant-ph         │
│  過去24-48時間の新着   │     │  cond-mat│
└──────────┬─────────────┘     └───────────────────┘
           │ raw論文リスト
           ▼
┌────────────────────────┐
│  2. Filter & Score     │
│  primary_keywords一次  │
│  scoring_keywordsで加点│
│  閾値以上のみ通過      │
└──────────┬─────────────┘
           │ フィルタ済み論文 (5-15本想定)
           ▼
┌────────────────────────┐     ┌───────────────────┐
│  3. Summarize          │     │  Gemini API       │
│  プロンプト送信&パース │◄───►│  gemini-2.0-flash │
└──────────┬─────────────┘     └───────────────────┘
           │ 構造化サマリ
           ▼
┌────────────────────────┐     ┌───────────────────┐
│  4. Deliver            │     │  Notion API       │
│  Notionに行追加        │────►│  データベース      │
└────────────────────────┘     └───────────────────┘
           │
           ▼
┌────────────────────────┐
│  5. Log                │
│  取得N本→フィルタM本   │
│  →要約成功K本→失敗J本  │
│  GitHub Actions console│
└────────────────────────┘
```

---

## 6. エラーハンドリング

| 障害パターン | 対応 |
|-------------|------|
| arXiv APIタイムアウト / 503 | 3回リトライ（指数バックオフ: 5s→15s→45s）。全失敗時はログに記録し終了 |
| 新着論文0件 | 正常終了。ログに「該当論文なし」と記録 |
| フィルタ通過0件 | 正常終了。ログに記録 |
| Gemini API エラー（429 Rate Limit） | 60秒待機してリトライ（最大3回）。全失敗時は該当論文を未要約としてNotionに登録（タイトル・URL・スコアのみ） |
| Gemini API エラー（その他） | ログに記録。該当論文はタイトル・URL・スコアのみNotionに登録 |
| LLM出力パース失敗 | 生テキストをそのまま保存（セクション4.2参照） |
| Notion API エラー | ログにエラー出力。GitHub Actionsのジョブを失敗ステータスで終了（メール通知あり） |
| ネットワーク全断 | GitHub Actionsジョブ失敗。翌日自動リトライ |

---

## 7. ログ仕様

### 出力先
- GitHub Actionsのコンソール出力（標準出力 / 標準エラー出力）
- ジョブ失敗時はGitHubからメール通知が届く（デフォルト設定）

### 記録項目（各実行ごと）

```
[2026-04-07 07:00:15] INFO  実行開始
[2026-04-07 07:00:18] INFO  arXiv取得完了: 45本 (quant-ph: 38, cond-mat.stat-mech: 7)
[2026-04-07 07:00:18] INFO  一次フィルタ通過: 8本
[2026-04-07 07:00:18] INFO  スコア閾値通過: 5本 (閾値: 2)
[2026-04-07 07:00:25] INFO  要約完了: 5/5本 (バックエンド: gemini)
[2026-04-07 07:00:27] INFO  Notion登録完了: 5本
[2026-04-07 07:00:27] INFO  実行完了 (所要時間: 12秒)
```

ログはGitHub Actionsの実行履歴として90日間保持される。

---

## 8. 開発時の注意事項

### APIマナー
- arXiv API: リクエスト間隔を **3秒以上** 空けること（公式ガイドライン）
- Gemini API: 無料枠のレートリミット（15 RPM）を超えないよう、リクエスト間に4秒のインターバルを設定

### セキュリティ
- APIキーは **GitHub Actions Secrets** で管理（リポジトリのSettings → Secrets）
- ローカル開発時は `.env` を使用し、`.gitignore` に含めること
- `.env.example` をリポジトリに含め、必要な変数名のみ記載

### テスト方針
- `tests/` にユニットテストを配置
- arXiv APIレスポンスのモック（`tests/fixtures/` にサンプルXMLを配置）
- LLM出力のパースロジックのテスト（正常系・異常系）
- テストは `pytest` で実行可能にする
- PRやpush時にテストを自動実行するCIワークフローの追加も検討（フェーズ2）

---

## 9. フェーズ2 拡張計画

| 機能 | 概要 | 優先度 |
|------|------|--------|
| セマンティック検索 | `sentence-transformers` でembeddingベースのフィルタリング | 中 |
| 全文解析 | PDFダウンロード → `PyMuPDF` でIntro/Conclusionを精査 | 中 |
| 週次トレンドレポート | 1週間分の要約を集約し、MIPTトレンドを生成 | 低 |
| Semantic Scholar連携 | 被引用数・関連論文の自動取得 | 低 |
| Notion既読管理 | 「要精読」マーク論文の自動リマインド | 低 |

---

## 10. 開発ロードマップ

### Week 1: 基盤構築
- [x] GitHubリポジトリ作成・ディレクトリ構成・`requirements.txt`
- [x] arXiv API取得モジュール（`fetcher.py`）
- [ ] キーワードフィルタリング（`filter.py`）
- [ ] 動作確認: `python src/main.py` でフィルタ結果をターミナルに出力

### Week 2: LLM連携
- [ ] Gemini APIクライアント（`summarizer.py`）
- [ ] プロンプト送信 & YAMLパース処理
- [ ] プロンプト調整（実際のアブストラクトで品質検証）
- [ ] パース失敗時のフォールバック実装

### Week 3: Notion連携 & GitHub Actions自動化
- [ ] Notionインテグレーション設定・データベース作成
- [ ] Notion書き込みモジュール（`notion_client.py`）
- [ ] GitHub Actions Secrets設定
- [ ] ワークフロー（`.github/workflows/daily-summarize.yml`）作成
- [ ] `workflow_dispatch` で手動実行テスト
- [ ] スケジュール実行で1週間の試験運用開始
