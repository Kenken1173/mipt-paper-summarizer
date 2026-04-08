import models
import yaml

# keywords.yaml のパス
file_path = "config/keywords.yaml"

def load_settings(path = file_path) -> dict:
    """ YAMLファイルから設定を読み込む関数 """
    with open(path, 'r', encoding = 'utf-8') as file:
        data = yaml.safe_load(file)
    return data

def filter_papers(papers: list[models.Paper]):
    """ 論文のリストをフィルタリングする関数 """
"""TODO:
1本判定ロジックの設計

判定対象テキストは title + abstract を連結
大文字小文字は無視して比較
一次フィルタは OR 条件
一次フィルタに1つも引っかからなければ即不採用
スコアは scoring_keywords の keyword ごとに「含むなら weight 加点」
passed は score >= threshold
matched_primary_keywords と matched_scoring_keywords は実際に当たった語だけ保存
ここで大事なのは「同じ語が何回出ても1回だけ加点」か「出現回数分加点」かを先に決めることです。
仕様書の文面だと前者（語ごとに加点1回）が自然です。

3. 論文リスト処理の流れ

全論文を順に判定
一次フィルタ通過かつ閾値以上だけ残す
各論文と FilterResult をセットで保持
スコア降順でソート
同点時は published_at の新しい順にすると運用しやすい
4. 先に決めておくとハマらないポイント

ハイフン揺れ対策
例: measurement-induced と measurement induced
最初はそのまま実装し、必要なら後で正規化を追加
abstract が空や None の場合
title だけで判定できるようにしておく
ログ出力
入力件数、一次通過件数、最終通過件数を出すとデバッグが楽
5. テスト観点（最小）

一次キーワードに一致しない論文は落ちる
一次一致するがスコア不足なら落ちる
一次一致かつ閾値以上なら通る
同点スコアの並び順が安定している
大文字小文字違いでも一致する
今のあなたの進め方としては、まず「1本判定関数」を先に完成させ、その後でリスト処理に広げるのが最短です。
必要なら次に、あなたが書いた実装を見て「仕様適合チェックだけ」をコード非提示でレビューします。
"""