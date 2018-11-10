# Building figures from paper

```r
library(ggplot2)
library(grid)

themepurple = "#d0c1ff"
themeorange = "#ffab03"
themeyellow = "#fff7c1"

integrated_legend = theme(
  legend.position = c(0.25, 0.7),
  legend.background = element_rect(fill=themeyellow, size=0.5, linetype="solid"),
)

better_line_legend = guides(color = guide_legend(override.aes = list(size = 4)))

x_scale_truncated_dates = scale_x_discrete(label=function(x) substr(x, 6, 8))
```

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
geom_bar(stat="identity", fill=themepurple) +
coord_flip() +
geom_hline(yintercept=median(paperframe$downloads), col=themeorange, linetype="dashed", size=1) +
labs(x="Collection", y="Median downloads per paper") +
geom_text(nudge_y=-40) +
annotate("text", y=median(paperframe$downloads)+55, x=1, label=paste("overall median:", round(median(paperframe$downloads), 2))) +
theme_bw() +
theme(panel.grid.major.y = element_blank())
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

ggplot(monthframe, aes(x=month, y=submissions, fill=collection)) +
geom_bar(stat="identity", color="white") +
theme_bw() +
integrated_legend
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
)

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
ggplot(monthframe, aes(x=month, y=cumulative, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(y = "total downloads") +
theme_bw() +
integrated_legend +
scale_x_discrete(label=function(x) substr(x, 6, 8)) +
scale_y_continuous(breaks=seq(0, 3000000, 500000))

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

```r
pubframe = read.csv('publications_per_journal.csv')

ggplot(data=pubframe[0:20,], aes(x=reorder(publication, count), y=count, label=count)) +
  geom_bar(stat="identity", fill=themepurple) +
  coord_flip() +
  labs(y = "bioRxiv papers published", x = "") +
  geom_text(nudge_y=-20) +
  theme_bw() +
  theme(panel.grid.major.y = element_blank())
```

## Distribution of downloads per paper

```sql
SELECT a.id, COALESCE(SUM(t.pdf), 0) AS downloads
FROM prod.articles a
LEFT JOIN prod.article_traffic t ON a.id=t.article
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