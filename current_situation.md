# MIPT Paper Summarizer 現在のタスク整理（仕様書 v3 ベース）

## 0. 目的
- 毎朝 JST 7:00 に arXiv 新着を収集し、MIPT 関連論文を要約して Notion DB に自動登録する。
- GitHub Actions 上で無人運用し、失敗時はログで追跡できる状態にする。

## 1. 最優先タスク（着手順）

### 1-1. リポジトリ基盤の作成
- [ ] ディレクトリを仕様どおり作成
	- [ ] `.github/workflows/`
	- [ ] `config/`
	- [ ] `src/`
	- [ ] `tests/`
- [ ] `requirements.txt` を作成（最低限: `arxiv`, `pyyaml`, `requests`, `python-dotenv`, `notion-client`, `pytest`, `google-generativeai` など）
- [ ] `.env.example` を作成
	- [ ] `GEMINI_API_KEY`
	- [ ] `NOTION_API_KEY`
	- [ ] `NOTION_DATABASE_ID`
- [ ] `.gitignore` に `.env`, `__pycache__/`, `.pytest_cache/` などを追加

### 1-2. 設定ファイルの準備
- [ ] `config/keywords.yaml` を仕様書の内容で作成
	- [ ] `primary_keywords`
	- [ ] `scoring_keywords`
	- [ ] `score_threshold`
- [ ] `config/prompts.yaml` を仕様書の内容で作成
	- [ ] `system_prompt`
	- [ ] `user_prompt_template`

### 1-3. コア実装（Python）
- [ ] `src/models.py`
	- [ ] `Paper` データクラス
	- [ ] `Summary` データクラス
- [ ] `src/fetcher.py`
	- [ ] arXiv から `quant-ph OR cond-mat.stat-mech` を取得
	- [ ] 取得範囲を過去 24-48 時間で制限
	- [ ] API エラー時の 3 回リトライ（5s -> 15s -> 45s）
- [ ] `src/filter.py`
	- [ ] 一次フィルタ（`primary_keywords` OR）
	- [ ] 重み付きスコア計算
	- [ ] 閾値以上を抽出しスコア降順ソート
- [ ] `src/summarizer.py`
	- [ ] Gemini `gemini-2.0-flash` 呼び出し
	- [ ] YAML パース
	- [ ] パース失敗時フォールバック（`one_line` に生テキスト、他は `解析失敗`）
	- [ ] 429 時の 60 秒待機リトライ（最大 3 回）
- [ ] `src/notion_client.py`
	- [ ] Notion DB スキーマに対応した page 作成処理
	- [ ] 要約失敗時でも最小情報（タイトル/URL/スコア）登録
- [ ] `src/main.py`
	- [ ] Fetch -> Filter -> Summarize -> Deliver のパイプライン接続
	- [ ] 実行ログの整形出力（件数、成功/失敗、処理時間）

## 2. 自動実行・運用タスク

### 2-1. GitHub Actions
- [ ] `.github/workflows/daily-summarize.yml` を作成
	- [ ] `schedule: '0 22 * * *'`
	- [ ] `workflow_dispatch`
	- [ ] Python 3.12 セットアップ
	- [ ] `pip install -r requirements.txt`
	- [ ] `python src/main.py` 実行
	- [ ] `timeout-minutes: 10`

### 2-2. Secrets / Notion 設定
- [ ] GitHub Secrets 登録
	- [ ] `GEMINI_API_KEY`
	- [ ] `NOTION_API_KEY`
	- [ ] `NOTION_DATABASE_ID`
- [ ] Notion Integration を DB に接続
- [ ] Notion DB のプロパティ名と型を仕様と一致させる

## 3. テストタスク
- [ ] `tests/test_fetcher.py`
	- [ ] 正常系（論文取得）
	- [ ] タイムアウト/503 リトライ
- [ ] `tests/test_filter.py`
	- [ ] 一次フィルタの通過判定
	- [ ] スコア計算
	- [ ] 閾値フィルタ・並び順
- [ ] `tests/test_summarizer.py`
	- [ ] YAML 正常パース
	- [ ] パース失敗フォールバック
	- [ ] API 429 リトライ
- [ ] `tests/fixtures/` に arXiv レスポンスサンプルを配置
- [ ] `pytest` でローカル実行確認

## 4. 受け入れ条件（Done 定義）
- [ ] ローカルで `python src/main.py` 実行時、ログに件数と結果が出る
- [ ] 手動実行（`workflow_dispatch`）で Notion に論文が登録される
- [ ] 日次スケジュールで 1 週間連続稼働できる
- [ ] エラー時の挙動が仕様どおり（Notion エラーはジョブ失敗、それ以外は継続）

## 5. 直近アクション（今日やること）
- [ ] プロジェクト雛形作成（フォルダ、requirements、env、設定 YAML）
- [ ] `fetcher.py` と `filter.py` を先に実装し、フィルタ結果を標準出力で確認
- [ ] その後 `summarizer.py` を追加し、1-2 件で YAML パース確認
- [ ] 最後に `notion_client.py` と GitHub Actions を接続して手動実行テスト