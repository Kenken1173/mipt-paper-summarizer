import models
import yaml

# keywords.yaml のパス
file_path = "config/keywords.yaml"

def load_settings(path = file_path) -> dict:
    """ YAMLファイルから設定を読み込む関数 """
    with open(path, 'r', encoding = 'utf-8') as file:
        data = yaml.safe_load(file)
    return data

def filter_paper(paper: models.Paper):
    """ 論文をフィルタリングする関数 """
    settings = load_settings()
    abstract_paper = paper.abstract
    if paper.abstract is None:
        abstract_paper = "" # abstract が None の場合は空文字にする
    text = paper.title + abstract_paper
    text = text.lower()  # 大文字小文字を無視するために小文字化

    for primary_keyword in settings['primary_keywords']:
        if primary_keyword.lower() in text:
            break
    else:
        return None # 一次フィルタに引っかからない場合は不採用
    score = 0

    for item in settings['scoring_keywords']:
        if item['keyword'].lower() in text:
            score += item['weight']
    
    passed = score >= settings['score_threshold']

    matched_primary_keywords = [kw for kw in settings['primary_keywords'] if kw.lower() in text]
    matched_scoring_keywords = [kw['keyword'] for kw in settings['scoring_keywords'] if kw['keyword'].lower() in text]
    return models.FilterResult(matched_primary_keywords, score, passed, matched_scoring_keywords)

def filter_papers(papers: list[models.Paper]):
    """ 複数の論文をフィルタリングする関数 """
    result_list = []

    for paper in papers:
        result = filter_paper(paper)
        if (result is not None) and (result.passed):
            result_list.append((paper, result))
    
    # スコア降順、同点の場合は published_at の新しい順にソート
    result_list.sort(key=lambda x: (x[1].score, x[0].published_at), reverse=True)

    return result_list
