# Building figures from paper

```r
library(ggplot2)
library(grid)
library(gridExtra)
library(plyr)

themepurple = "#d0c1ff"
themeorange = "#ffab03"
themeyellow = "#fff7c1"

integrated_legend = theme(
  legend.position = c(0.35, 0.7),
  legend.background = element_rect(fill=themeyellow, size=0.5, linetype="solid"),
)

better_line_legend = guides(color = guide_legend(override.aes = list(size = 4)))

x_scale_truncated_dates = scale_x_discrete(label=function(x) substr(x, 6, 8))
```

## Median downloads per category

```sql
SELECT d.article, d.downloads, a.collection
FROM prod.alltime_ranks d
INNER JOIN prod.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL;
```

```r
paperframe = read.csv('downloads_per_category.csv')
mediandownloads <- aggregate(downloads~collection,data=paperframe,median)

ggplot(data=mediandownloads, aes(x=reorder(collection, downloads), y=downloads, label=round(downloads, 2), fill=collection)) +
geom_bar(stat="identity") +
coord_flip() +
geom_hline(yintercept=median(paperframe$downloads), col=themeorange, linetype="dashed", size=1) +
labs(x="collection", y="median downloads per paper") +
geom_text(nudge_y=-40) +
annotate("text", y=median(paperframe$downloads)+45, x=1, label=paste("overall median:", round(median(paperframe$downloads), 2))) +
theme_bw() +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none"
)
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

ggplot(data=meanauthors, aes(x=reorder(Collection, Authors), y=Authors, label=round(Authors, 2), fill=Collection)) +
geom_bar(stat="identity") +
coord_flip() +
geom_hline(yintercept=mean(authorframe$Authors), col=themeorange, linetype="dashed", size=1) +
labs(x="Collection", y="Mean authors per paper") +
geom_text(nudge_y=-0.5) +
annotate("text", y=mean(authorframe$Authors)+1.0, x=1, label=paste("overall mean:", round(mean(authorframe$Authors), 2))) +
theme_bw() +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none"
)
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

yearlabel = -280
x <- ggplot(monthframe, aes(x=month, y=submissions, fill=collection)) +
geom_bar(stat="identity", color="white") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 3, xmax = 3) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 15, xmax = 15) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 27, xmax = 27) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 39, xmax = 39) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 51, xmax = 51)

gt <- ggplot_gtable(ggplot_build(x))
gt$layout$clip[gt$layout$name == "panel"] <- "off"
grid.draw(gt)
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

yearlabel = -680
x <- ggplot(monthframe, aes(x=month, y=cumulative, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(y = "total papers") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
scale_y_continuous(breaks=seq(0, 6000, 1000)) +
theme(plot.margin = unit(c(1,8,1,1), "lines")) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 5663, ymax = 5663, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 3884, ymax = 3884, xmin = 60, xmax = 60
) +
annotation_custom(
  grob = textGrob(label = "evolutionary biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2720, ymax = 2820, xmin = 60, xmax = 60
) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2690, ymax = 2690, xmin = 60, xmax = 60
) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2429, ymax = 2429, xmin = 60, xmax = 60
) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2139, ymax = 2139, xmin = 60, xmax = 60
) +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 3, xmax = 3) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 15, xmax = 15) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 27, xmax = 27) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 39, xmax = 39) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 51, xmax = 51)

gt <- ggplot_gtable(ggplot_build(x))
gt$layout$clip[gt$layout$name == "panel"] <- "off"
grid.draw(gt)

```

## Downloads per month

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

# Cumulative downloads:
yearlabel = -290000
x <- ggplot(monthframe, aes(x=month, y=cumulative, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(y = "total downloads") +
theme_bw() +
integrated_legend +
scale_x_discrete(label=function(x) substr(x, 6, 8)) +
scale_y_continuous(breaks=seq(0, 3000000, 500000)) +
theme(plot.margin = unit(c(1,8,1,1), "lines")) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2900000, ymax = 2773420, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2750000, ymax = 2766697, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2585360, ymax = 2585360, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 1434111, ymax = 1434111, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "evolutionary biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 1286774, ymax = 1286774, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 781316, ymax = 781316, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "cancer biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 621069, ymax = 621069, xmin = 60, xmax = 60) +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 3, xmax = 3) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 15, xmax = 15) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 27, xmax = 27) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 39, xmax = 39) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = yearlabel, ymax = yearlabel, xmin = 51, xmax = 51)

gt <- ggplot_gtable(ggplot_build(x))
gt$layout$clip[gt$layout$name == "panel"] <- "off"
grid.draw(gt)

# Monthly downloads:
ggplot(monthframe, aes(x=month, y=monthly, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(y = "monthly downloads") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
scale_y_continuous(breaks=seq(0, 200000, 25000)) +
annotate("text", y=102000, x=31.5, label="A") +
annotate("text", y=168000, x=51.5, label="B") +
annotate("text", y=126000, x=53.75, label="C")
```

## Preprint publications per journal

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


```sql
SELECT max(journal), COUNT(article) AS tally
FROM (SELECT REGEXP_REPLACE(publication, '^The Journal', 'Journal') AS journal, article FROM prod.article_publications) AS stripped
GROUP BY lower(journal)
ORDER BY tally DESC, max(journal);


SELECT topname AS journal, tally, collection
FROM (
	SELECT max(journal) AS topname, COUNT(article) AS tally, collection
	FROM (
		SELECT REGEXP_REPLACE(p.publication, '^The Journal', 'Journal') AS journal, p.article, a.collection
		FROM prod.article_publications p
		INNER JOIN prod.articles a ON p.article=a.id
	) AS stripped
	GROUP BY lower(journal), collection
	ORDER BY max(journal), tally DESC
) AS biglist
WHERE topname IN (
	SELECT journal FROM (
		SELECT max(journal) AS journal, COUNT(article) AS tally
		FROM (SELECT REGEXP_REPLACE(publication, '^The Journal', 'Journal') AS journal, article FROM prod.article_publications) AS stripped
		GROUP BY lower(journal)
		ORDER BY tally DESC, max(journal)
		LIMIT 30
	) AS ranks
)
```

```r
pubframe = read.csv('publications_per_journal_categorical.csv')

totals <- pubframe %>%
  group_by(journal) %>%
  summarize(total = sum(tally))

ggplot(pubframe, aes(x=journal, y=tally, fill=collection)) +
geom_bar(stat="identity", color="white") +
aes(x = reorder(journal, tally, sum), y = tally, label = tally, fill = collection) +
coord_flip() +
labs(y = "bioRxiv papers published", x = "") +
theme_bw() +
theme(
  legend.position = c(0.7, 0.3),
  legend.background = element_rect(fill=themeyellow, size=0.5, linetype="solid"),
  panel.grid.major.y = element_blank()
) +
geom_text(aes(journal, total, label = total, fill = NULL), data = totals, hjust=-0.45)

```

## Publications per category

```sql
SELECT p.collection, p.published, t.total, (p.published::decimal / t.total)
FROM (
  SELECT a.collection, COUNT(p.article) AS published
  FROM prod.article_publications p
  INNER JOIN prod.articles a ON p.article=a.id
  GROUP BY collection
  ORDER BY collection
) AS p
INNER JOIN (
  SELECT collection, COUNT(id) AS total
  FROM prod.articles
  GROUP BY collection
  ORDER BY collection
) AS t ON t.collection=p.collection
```


```r
pubframe = read.csv('publications_per_category.csv')

proportion <- ggplot(
    data=pubframe,
    aes(
      x=reorder(collection, proportion),
      y=proportion,
      label=round(proportion, 2),
      fill=collection
    )
  ) +
  geom_bar(stat="identity") +
  geom_hline(yintercept=0.4158399, col=themeorange, linetype="dashed", size=1) +
  annotate("text", y=0.475, x=4, label="overall proportion: 0.41584") +
  labs(x="collection", y="proportion of total") +
  geom_text(nudge_y=-0.02) +
  theme_bw() +
  theme(
    panel.grid.major.y = element_blank(),
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position="none"
  )

totals <- ggplot(
    data=pubframe,
    aes(
      x=reorder(collection, proportion),
      y=published,
      label=published,
      fill=collection
    )
  ) +
  geom_bar(stat="identity") +
  labs(x="", y="count of preprints published elsewhere") +
  geom_text(nudge_y=50) +
  theme_bw() +
  theme(
    panel.grid.major.y = element_blank(),
    axis.text.x = element_blank(),
    legend.position="none"
  )

grid.arrange(totals,proportion)
```


## Distribution of downloads per paper

```sql
SELECT a.id, COALESCE(SUM(t.pdf), 0) AS downloads
FROM prod.articles a
LEFT JOIN prod.article_traffic t ON a.id=t.article
WHERE a.collection IS NOT NULL
GROUP BY a.id
ORDER BY downloads DESC;
```

```r
paperframe = read.csv('downloads_per_paper.csv')

ggplot(paperframe, aes(x=downloads)) +
  geom_histogram(
    color="black", fill=themepurple,
    bins = 50
  ) +
  scale_x_log10() +
  labs(y = "papers", x = "total downloads (log scale)") +
  geom_vline(
    xintercept=median(paperframe$downloads),
    col=themeorange, linetype="dashed", size=1
  ) +
  annotate("text", x=median(paperframe$downloads)+300, y=3450, label=paste("median:", round(median(paperframe$downloads), 2))) +
  theme_bw()
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

Skewness of downloads per paper:

```r
library(moments)
paperframe = read.csv('downloads_per_paper.csv')
skewness(paperframe$downloads)
```
