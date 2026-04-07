import models
import datetime
import urllib
# https://pypi.org/project/arxiv/
import arxiv

search_results = 1

# http://export.arxiv.org/api/query?search_query=FIELD:VALUE
params = {
    "search_query": "cat:quant-ph OR cat:cond-mat",
    "start": 0,
    "max_results": search_results,
    "sortBy": "submittedDate",
    "sortOrder": "descending"
}
url = urllib.parse.urlencode(params)

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

client = arxiv.Client()
search = arxiv.Search(query=params["search_query"], max_results=params["max_results"], sort_by=arxiv.SortCriterion.SubmittedDate, sort_order=arxiv.SortOrder.Descending)
results = client.results(search)

# イテレータをループして、各エントリを Paper に変換
papers = [entry_to_paper(entry) for entry in results]
print(papers)


# TODO: ここで、上記の知識を活用しながらarXiv API を叩いて、最近の論文を取得するコードを書く
def fetch_recent_papers(hours=24, max_results=search_results, test=False) -> list[models.Paper]:
    result = []
    test = True # テストモードではダミーデータを返す
    for _ in range(max_results):
        # arXiv API を叩いて、最近の論文を取得するコードを書く
        
        # ここではテストモードのときにダミーデータを返すようにする
        if test:
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