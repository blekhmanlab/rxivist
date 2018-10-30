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
theme(legend.position="bottom", axis.text.x = element_text(angle = 90, hjust = 1))
```



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