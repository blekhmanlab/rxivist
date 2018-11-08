# Building figures from paper

## Median downloads per category

```sql
SELECT d.article, d.downloads, a.collection
FROM alltime_ranks d
INNER JOIN articles a ON d.article=a.id;
```

```r
paperframe = read.csv('downloads_per_category.csv')
mediandownloads <- aggregate(downloads~collection,data=paperframe,median)

ggplot(data=mediandownloads, aes(x=reorder(collection, downloads), y=downloads, label=round(downloads, 2))) +
  geom_bar(stat="identity", fill="#d0c1ff") +
  coord_flip() +
  geom_hline(yintercept=median(paperframe$downloads), col="#AC131F") +
  labs(x="Collection", y="Mean downloads per paper") +
  geom_text(nudge_y=-40) +
  annotate("text", y=median(paperframe$downloads)+110, x=1, label=paste(round(median(paperframe$downloads), 2), "overall median"))
```

## Mean authors per paper

Extracting list of articles, the month and year they were posted, and how many authors they had:

```sql
SELECT
  a.id, a.collection,
  EXTRACT(MONTH FROM a.posted) AS month,
  EXTRACT(YEAR FROM a.posted) AS year,
  COUNT(w.author)
FROM articles a
LEFT JOIN article_authors w ON w.article=a.id
GROUP BY a.id, a.collection, a.posted
ORDER BY year, month;
```

Building figure:

```r
authorframe = read.csv('authors_per_paper.csv')
meanauthors <- aggregate(Authors~Collection,data=authorframe,mean)

ggplot(data=meanauthors, aes(x=reorder(Collection, Authors), y=Authors, label=round(Authors, 2))) +
  geom_bar(stat="identity", fill="#d0c1ff") +
  coord_flip() +
  geom_hline(yintercept=mean(authorframe$Authors), col="#AC131F") +
  labs(x="Collection", y="Mean authors per paper") +
  geom_text(nudge_y=-0.5) +
  annotate("text", y=mean(authorframe$Authors)+1.2, x=1, label=paste(round(mean(authorframe$Authors), 2), "overall mean"))
```

## Submissions per month

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS month,
	collection,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1,2
ORDER BY 1,2;
```

```r
monthframe=read.csv('submissions_per_month.csv')

ggplot(monthframe, aes(x=month, y=submissions, fill=collection)) +
geom_bar(stat="identity") +
theme(legend.position="bottom", axis.text.x = element_text(angle = 90, hjust = 1))
```

## Cumulative submissions per month

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	collection,
	COUNT(id) AS submissions
FROM articles
GROUP BY 1,2,3
ORDER BY 2,1,3;
```
(Data organized in `submissions_per_month_cumulative.xlsx`, then `submissions_per_month_cumulative.csv`)

```r
monthframe=read.csv('submissions_per_month_cumulative.csv')

ggplot(monthframe, aes(x=month, y=cumulative, group=collection, color=collection)) +
geom_line() +
labs(y = "total papers") +
theme(legend.position="bottom", axis.text.x = element_text(angle = 90, hjust = 1))
```

## Cumulative downloads per month

```sql
SELECT article_traffic.year||'-'||lpad(article_traffic.month::text, 2, '0') AS date,
	SUM(article_traffic.pdf),
	articles.collection
FROM paper.article_traffic
LEFT JOIN paper.articles ON article_traffic.article=articles.id
GROUP BY 1,3
ORDER BY 1,3;
```
(Data organized in `downloads_per_month_cumulative.xlsx`, then `downloads_per_month_cumulative.csv`)

```r
monthframe=read.csv('downloads_per_month_cumulative.csv')

ggplot(monthframe, aes(x=month, y=cumulative, group=collection, color=collection)) +
geom_line() +
labs(y = "total downloads") +
theme(legend.position="bottom", axis.text.x = element_text(angle = 90, hjust = 1))

ggplot(monthframe, aes(x=month, y=monthly, group=collection, color=collection)) +
geom_line() +
labs(y = "monthly downloads") +
theme(legend.position="bottom", axis.text.x = element_text(angle = 90, hjust = 1))
```

## Journals publishing preprints

```sql
SELECT max(journal), COUNT(article) AS tally
FROM (SELECT REGEXP_REPLACE(publication, '^The ', '') AS journal, article FROM prod.article_publications) AS stripped
GROUP BY lower(journal)
ORDER BY tally DESC, max(journal);
```

Consolidate duplicates:

| Original | Variant |
| --- | ----------- |
| Acta Crystallographica Section D | Acta Crystallographica Section D Structural Biology |
| Alzheimer's & Dementia | Alzheimers & Dementia |
| American Journal of Physiology - Renal Physiology | American Journal of Physiology-Renal Physiology |
| Bioinformatics | Bioinformatics (with trailing space) |
| Cell Death & Differentiation | Cell Death and Differentiation |
| Cell Death & Disease | Cell Death and Disease |
| Cell Host & Microbe | Cell Host and Microbe |
| Development | Development (Cambridge, England) |
| Epidemiology & Infection | Epidemiology and Infection |
| G3: Genes|Genomes|Genetics | G3 |
|  | G3&#58; Genes|Genomes|Genetics |
|  | G3 Genes|Genomes|Genetics |
|  | G3 (Bethesda, Md.) |
|  | Genes|Genomes|Genetics |
| Integrative Biology | Integrative Biology : Quantitative Biosciences From Nano To Macro |
|  | Integrrative Biology |
| Journal Of Physical Chemistry B | Journal Of Physical Chemistry. B |
| Methods | Methods (San Diego, Calif.) |
| Molecular & Cellular Proteomics | Molecular & Cellular Proteomics : MCP |
| Philosophical Transactions of the Royal Society A: Mathematical,				Physical and Engineering Sciences" | Philosophical Transactions A |
| Philosophical Transactions of the Royal Society B: Biological Sciences | Philosophical Transactions B |
| Plant & Cell Physiology | Plant and Cell Physiology |
| Plant, Cell & Environment | Plant, Cell and Environment |
| Proceedings of the Royal Society B: Biological Sciences | Proceedings B |
|   | Proceedings. Biological Sciences |
| PNAS | Proceedings of the National Academy of Sciences |
| Science | Science (New York, N.Y.) |
| SLAS Discovery | SLAS DISCOVERY: Advancing Life Sciences R&D |
| SLAS Technology | SLAS TECHNOLOGY: Translating Life Sciences Innovation |

## Statements in paper

Number of authors with an ORCID identifier: `SELECT COUNT(id) FROM authors WHERE orcid IS NOT NULL;`

Authors with an email:
```sql
SELECT COUNT(DISTINCT a.id)
FROM paper.authors AS a
INNER JOIN paper.author_emails AS e on a.id=e.author
WHERE e.email is NOT NULL;
```

Authors with multiple emails:
```sql
SELECT COUNT(id) FROM (
	SELECT a.id, COUNT(e.email) AS emails
	FROM paper.authors AS a
	INNER JOIN paper.author_emails AS e on a.id=e.author
	GROUP BY a.id
) AS emailcounts
WHERE emails > 1;
```

Author email addresses: `SELECT COUNT(email) FROM paper.author_emails;`
Duplicate email entries: `SELECT COUNT(email) - COUNT(DISTINCT email) FROM paper.author_emails;`