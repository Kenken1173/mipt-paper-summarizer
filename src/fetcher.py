import models
import datetime
# https://pypi.org/project/arxiv/
import arxiv
import logging
import time

search_results = 3

# http://export.arxiv.org/api/query?search_query=FIELD:VALUE
params = {
    "search_query": "cat:quant-ph OR cat:cond-mat",
    "max_results": search_results,
}

def entry_to_paper(entry) -> models.Paper:
    """ 1つの arXiv API のエントリーを Paper クラスに変換する関数 """
    return models.Paper(
        title = entry.title,
        authors = [author.name for author in entry.authors],
        url = entry.entry_id,
        abstract = entry.summary,
        published_at = entry.published,
        arxiv_id = entry.get_short_id()
    )

client = arxiv.Client(delay_seconds=3)

def fetch_recent_papers(params = params, test=True) -> list[models.Paper]:
    # ここではテストモードのときにダミーデータを返すようにする
    if test:
        result = []
        for _ in range(params["max_results"]):
            paper = models.Paper(
                title = "Example Paper Title",
                authors = ["Author A", "Author B"],
                url = "https://arxiv.org/abs/hogehoge",
                abstract = "This is a dummy abstract for the example paper.",
                published_at = datetime.datetime.now(),
                arxiv_id = "hogehoge"
            )
            result.append(paper)
        return result

    # arXiv API を叩いて、最近の論文を取得するコードを書く
    search = arxiv.Search(query=params["search_query"], max_results=params["max_results"], sort_by=arxiv.SortCriterion.SubmittedDate, sort_order=arxiv.SortOrder.Descending)
    
    today = datetime.datetime.now(datetime.timezone.utc).date()
    cutoff = today -  datetime.timedelta(days=2)  # 過去2日以内
    papers = []
    retry_delays = [3, 3, 3] # エラーが発生した場合のリトライの待ち時間（秒）
    for attempt, delay in enumerate(retry_delays):
        try:
            for entry in client.results(search):
                if entry.published.date() < cutoff:
                    break
                papers.append(entry_to_paper(entry))
            break # 成功したらループを抜ける
        except Exception as e:
            logging.warning(f"arXiv API エラー試行 {attempt + 1}/3: {e}")
            papers.clear() # エラーが発生した場合は取得した論文をクリアする
            if attempt < len(retry_delays) - 1:
                time.sleep(delay)
            else:
                logging.error("arXiv API: 全リトライ失敗。終了します。")
        
    logging.info(f"arXiv取得完了: {len(papers)}本")

    return papers

# print(fetch_recent_papers(test=False)) # デバッグ用: 実際のAPIを叩いて論文を取得する場合は test=False にする