# Building figures from paper

```r
library(ggplot2)
library(grid)
library(gridExtra)
library(plyr)
require(dplyr)
require(scales)

themepurple = "#d0c1ff"
themeorange = "#ffab03"
themeyellow = "#fff7c1"
integrated_legend = theme(
  legend.position = c(0.3, 0.7),
  legend.background = element_rect(fill=themeyellow, size=0.5, linetype="solid"),
)
better_line_legend = guides(color = guide_legend(override.aes = list(size = 4)))
x_scale_truncated_dates = scale_x_discrete(label=function(x) substr(x, 6, 8))

setwd('/Users/rabdill/code/rxivist/paper/data') # *tk remove this
```

## Downloads per month

```sql
SELECT article_traffic.year||'-'||lpad(article_traffic.month::text, 2, '0') AS date,
	SUM(article_traffic.pdf),
	REPLACE(articles.collection, '-', ' ') AS collection
FROM paper.article_traffic
LEFT JOIN paper.articles ON article_traffic.article=articles.id
GROUP BY 1,3
ORDER BY 1,3;
```
(Data organized in `downloads_per_month_cumulative.xlsx`, then moved to `downloads_per_month_cumulative.csv`)

```r
monthframe=read.csv('downloads_per_month_cumulative.csv')

# Cumulative downloads:
yearline = "black"
yearline_size = 0.5
big_fontsize = 12
yearlabel = -210000

x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line(size=1.5) +
x_scale_truncated_dates +
better_line_legend +
labs(x = "", y = "total downloads") +
theme_bw() +
integrated_legend +
scale_y_continuous(breaks=seq(0, 3000000, 500000), labels=comma) +
theme(
  plot.margin = unit(c(1,8,1,1), "lines"), # for right-margin labels
  axis.text.x=element_blank(), # remove x axis labels
  axis.text.y = element_text(size=big_fontsize)
) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2979894, ymax = 3000000, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2900000, ymax = 2926524, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2714730, ymax = 2714730, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1507955, ymax = 1507955, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "evolutionary biology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1348577, ymax = 1348577, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 851647, ymax = 851647, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "cancer biology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 659128, ymax = 659128, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = yearlabel, ymax = yearlabel, xmin = 3, xmax = 3) +
geom_vline(xintercept=3, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = yearlabel, ymax = yearlabel, xmin = 15, xmax = 15) +
geom_vline(xintercept=15, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = yearlabel, ymax = yearlabel, xmin = 27, xmax = 27) +
geom_vline(xintercept=27, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = yearlabel, ymax = yearlabel, xmin = 39, xmax = 39) +
geom_vline(xintercept=39, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = yearlabel, ymax = yearlabel, xmin = 51, xmax = 51) +
geom_vline(xintercept=51, col=yearline, size=yearline_size)

gt <- ggplot_gtable(ggplot_build(x))
gt$layout$clip[gt$layout$name == "panel"] <- "off"
grid.draw(gt)

# Monthly downloads:
yearlabel = -25000

x <- ggplot(monthframe, aes(x=date, y=month, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(x = "month", y = "monthly downloads") +
theme_bw() +
theme(
  legend.position = c(0.25, 0.7),
  legend.background = element_rect(fill=themeyellow, size=0.5, linetype="solid"),
) +
x_scale_truncated_dates +
scale_y_continuous(breaks=seq(0, 200000, 25000), labels=comma) +
annotate("text", y=102000, x=31.5, label="A") +
annotate("text", y=168000, x=51.5, label="B") +
annotate("text", y=126100, x=53.75, label="C") +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2979894, ymax = 3000000, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2900000, ymax = 2926524, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2714730, ymax = 2714730, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 1507955, ymax = 1507955, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "evolutionary biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 1348577, ymax = 1348577, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 851647, ymax = 851647, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "cancer biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 659128, ymax = 659128, xmin = 61, xmax = 61) +
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


## Median downloads per category

```sql
SELECT d.article, d.downloads, REPLACE(a.collection, '-', ' ') AS collection
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL;
```

*Note: pulling this information from `alltime_ranks` and using an inner join means that papers with exactly 0 downloads are excluded from this calculation.*

```r
paperframe = read.csv('downloads_per_category.csv')

# Regular old bar plot:
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

# Bar plot WITH outliers:
ggplot(data=paperframe, aes(x=reorder(collection, downloads, FUN=median), y=downloads, fill=collection)) +
geom_boxplot() +
scale_y_log10() +
coord_flip()

# Box plot, NO outliers:
library(plyr)
medians <- ddply(paperframe, .(collection), summarise, med = median(downloads))

ggplot(data=paperframe, aes(
  x=reorder(collection, downloads, FUN=median),
  y=downloads,
  fill=collection)) +
geom_boxplot(outlier.shape = NA, coef=0) +
scale_y_continuous(labels=comma) +
coord_flip(ylim=c(0,1000)) +
theme_bw() +
labs(x="collection", y="downloads per paper") +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none"
) +
geom_hline(yintercept=median(paperframe$downloads), col=themeorange, linetype="dashed", size=1) +
annotate("text", y=median(paperframe$downloads)+95, x=1, label=paste("overall median:", round(median(paperframe$downloads), 2))) +
geom_text(data = medians, aes(
  x = collection, y = med+40, label = med), size = 4)


library(car)
leveneTest(downloads~collection, data=paperframe)
kruskal.test(downloads~collection, data=paperframe)
library(FSA)
dunnTest(downloads~collection, data=paperframe, method="bh")
# (pasted into excel, headers changed to "a" "b" and "p_adj")
x = read.csv('downloads_pvalues.csv')
x <- spread(results, key='b', value='p_adj')
> write.table(x, file="testing.txt")

```

## Distribution of downloads per paper

```sql
SELECT *
FROM (
	SELECT a.id, COALESCE(SUM(t.pdf), 0) AS downloads
	FROM paper.articles a
	LEFT JOIN paper.article_traffic t ON a.id=t.article
	WHERE a.collection IS NOT NULL
	GROUP BY a.id
	ORDER BY downloads DESC
) AS totals
WHERE downloads > 0
```

```r
paperframe = read.csv('downloads_per_paper.csv')

ggplot(paperframe, aes(x=downloads)) +
  geom_histogram(
    color="black", fill=themepurple,
    bins = 50
  ) +
  scale_x_log10(labels = comma) +
  scale_y_continuous(labels = comma) +
  labs(y = "papers", x = "total downloads (log scale)") +
  geom_vline(
    xintercept=median(paperframe$downloads),
    col=themeorange, linetype="dashed", size=1
  ) +
  annotate("text", x=median(paperframe$downloads)+300, y=3450, label=paste("median:", round(median(paperframe$downloads), 2))) +
  theme_bw()
```

## Submissions per month

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	REPLACE(collection, '-', ' ') AS collection,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1,2
ORDER BY 1,2;
```
(Data organized in `submissions_per_month.xlsx`, then `submissions_per_month.csv`)

```r
# Cumulative submissions over time
monthframe=read.csv('submissions_per_month.csv')

yearlabel = -680
x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(x = "month", y = "total papers") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
scale_y_continuous(breaks=seq(0, 6100, 1000), labels=comma) +
theme(plot.margin = unit(c(1,8,1,1), "lines")) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 6081, ymax = 6081, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 4064, ymax = 4064, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "evolutionary biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2931, ymax = 2931, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2816, ymax = 2816, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2621, ymax = 2621, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 2245, ymax = 2245, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "cell biology", hjust = 0, gp = gpar(fontsize = 8)),
  ymin = 1605, ymax = 1605, xmin = 61, xmax = 61
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

# Cumulative submissions over time, stacked:
yearlabel = -2000

x <- ggplot(monthframe, aes(x=date, y=cumulative, fill=collection)) +
geom_bar(stat="identity", color="white") +
better_line_legend +
labs(x = "month", y = "total papers") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
scale_y_continuous(labels=comma) +
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

# Submissions per month, stacked:
yearlabel = -200
x <- ggplot(monthframe, aes(x=date, y=submissions, fill=collection)) +
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

# Submissions per month, NOT stacked:
yearlabel = -50
x <- ggplot(monthframe, aes(x=date, y=submissions, group=collection, color=collection)) +
geom_line() +
better_line_legend +
labs(x = "month", y = "papers") +
theme_bw() +
integrated_legend +
x_scale_truncated_dates +
scale_y_continuous(labels=comma) +
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


## Mean authors per paper

Extracting list of articles, the month and year they were posted, and how many authors they had:

```sql
SELECT
  a.id, a.collection,
  EXTRACT(MONTH FROM a.posted) AS month,
  EXTRACT(YEAR FROM a.posted) AS year,
  COUNT(w.author) AS authors
FROM paper.articles a
LEFT JOIN paper.article_authors w ON w.article=a.id
GROUP BY a.id, a.collection, a.posted
ORDER BY year, month;
```

Building figure:

```r
authorframe = read.csv('authors_per_paper.csv')

medians <- ddply(authorframe, .(collection), summarise, med = median(authors))

ggplot(data=authorframe, aes(
  x=reorder(collection, authors, FUN=mean),
  y=authors,
  fill=collection
)) +
geom_boxplot(outlier.shape = NA) +
stat_summary(fun.y=mean, geom="point", shape=23, size=2) +
scale_y_continuous() +
coord_flip(ylim=c(0,25)) +
theme_bw() +
labs(x="collection", y="authors per paper") +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none"
) +
geom_hline(yintercept=median(authorframe$authors), col=themeorange, linetype="dashed", size=1) +
annotate("text", y=median(authorframe$authors)+4, x=1, label=paste("overall median:", round(median(authorframe$authors), 2))) +
geom_text(data = medians, aes(
  x = collection, y = med+40, label = med), size = 4)


# library(car)
# leveneTest(Authors ~ Collection, data=authorframe)
# kruskal.test(Authors ~ Collection, data=authorframe)
# pairwise.wilcox.test(authorframe$Authors, authorframe$Collection, p.adjust.method="BH")
# library(FSA)
# dunnTest(Authors ~ Collection, data=authorframe, method="bh")
```


## Preprint publications per journal

Consolidate duplicates:

| Original | Variant |
| --- | ----------- |
| Acta Crystallographica Section D Structural Biology | Acta Crystallographica Section D |
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
| Philosophical Transactions of the Royal Society A: Mathematical, Physical and Engineering Sciences | Philosophical Transactions of the Royal Society A: Mathematical,				Physical and Engineering Sciences
|  | Philosophical Transactions A |
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
SELECT topname AS journal, tally, REPLACE(collection, '-', ' ') AS collection
FROM (
	SELECT max(journal) AS topname, COUNT(article) AS tally, collection
	FROM (
		SELECT REGEXP_REPLACE(p.publication, '^The Journal', 'Journal') AS journal, p.article, a.collection
		FROM paper.article_publications p
		INNER JOIN paper.articles a ON p.article=a.id
	) AS stripped
	GROUP BY lower(journal), collection
	ORDER BY max(journal), tally DESC
) AS biglist
WHERE topname IN (
	SELECT journal FROM (
		SELECT max(journal) AS journal, COUNT(article) AS tally
		FROM (SELECT REGEXP_REPLACE(publication, '^The Journal', 'Journal') AS journal, article FROM paper.article_publications) AS stripped
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
geom_text(aes(journal, total, label = total, fill = NULL), data = totals, hjust=-0.3)

```

## Publications per category

```sql
SELECT p.collection, p.published, t.total, (p.published::decimal / t.total)
FROM (
  SELECT a.collection, COUNT(p.article) AS published
  FROM paper.article_publications p
  INNER JOIN paper.articles a ON p.article=a.id
  GROUP BY collection
  ORDER BY collection
) AS p
INNER JOIN (
  SELECT collection, COUNT(id) AS total
  FROM paper.articles
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
  geom_hline(yintercept=0.40979, col=themeorange, linetype="dashed", size=1) +
  annotate("text", y=0.45, x=4, label="overall proportion: 0.4098") +
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

## Publication rate

### Monthly rate

```sql
SELECT month, posted, published, published::decimal/posted AS rate
FROM (
  SELECT EXTRACT(YEAR FROM a.posted)||'-'||lpad(EXTRACT(MONTH FROM a.posted)::text, 2, '0') AS month,
	COUNT(a.id) AS posted,
  COUNT(p.doi) AS published
  FROM paper.articles a
  LEFT JOIN paper.article_publications p ON a.id=p.article
  GROUP BY month
  ORDER BY month
) AS counts
```

```r
paperframe = read.csv('publication_rate_month.csv')

yearlabel = -0.07

x <- ggplot(paperframe, aes(x=month, y=rate)) +
geom_point() +
labs(x = "month", y = "proportion published") +
theme_bw() +
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

### Annual rate

```sql
SELECT year, posted, published, posted-published AS unpublished, published::decimal/posted AS rate
FROM (
  SELECT EXTRACT(YEAR FROM a.posted) AS year,
	COUNT(a.id) AS posted,
  COUNT(p.doi) AS published
  FROM paper.articles a
  LEFT JOIN paper.article_publications p ON a.id=p.article
  GROUP BY year
  ORDER BY year
) AS counts
```

```r
paperframe = read.csv('publication_rate_year.csv')

ggplot(paperframe, aes(x=year, y=rate)) +
geom_bar(stat="identity") +
labs(x = "year", y = "proportion published") +
theme_bw()

paperframe = read.csv('publication_rate_year_long.csv')

ggplot(paperframe, aes(x=year, y=count, fill=category)) +
geom_bar(stat="identity", color="white") +
```

## Downloads for published papers

```sql
SELECT d.article, d.downloads,
	CASE WHEN COUNT(p.article) > 0 THEN TRUE
    	ELSE FALSE
    END AS published
FROM paper.alltime_ranks d
LEFT JOIN paper.article_publications p ON d.article=p.article
GROUP BY d.article
ORDER BY published DESC, d.downloads DESC
```

```r
paperframe = read.csv('downloads_publication_status.csv')
medians <- ddply(paperframe, .(published), summarise, med = median(downloads))

ggplot(data=paperframe, aes(
  x=reorder(published, downloads, FUN=median),
  y=downloads,
  fill=published
)) +
geom_boxplot(outlier.shape = NA, fill=themepurple) +
theme_bw() +
coord_flip(ylim=c(0, 1500)) +
labs(x="published in journal?") +
geom_text(data=medians, size=4, aes(x=published, y=med+35, label=med))

# ggplot(data=paperframe, aes(
#   x=reorder(published, downloads, FUN=median),
#   y=downloads,
#   fill=published
# )) +
# geom_violin() +
# theme_bw() +
# coord_flip(ylim=c(0, 2000)) +
# geom_hline(data=medians, aes(yintercept=med, color=published), linetype='dashed') +
# labs(x="published in journal?")


# ggplot(data=paperframe, aes(x=downloads, group=published, color=published)) +
# geom_freqpoly(bins=100, aes(y = ..density..)) +
# scale_x_log10(labels = comma) +
# scale_y_continuous() +
# theme_bw() +
# geom_text(data = medians, size = 4, aes(
#   x = med, y = 0, label = med
# ))

library(car)
leveneTest(downloads~published, data=paperframe)
library(MASS)
wilcox.test(downloads~published, data=paperframe)
# kruskal.test(downloads~published, data=paperframe)
```

## Downloads for journal publications

```sql
SELECT d.article, d.downloads, p.publication AS journal
FROM paper.alltime_ranks d
LEFT JOIN paper.article_publications p ON d.article=p.article
WHERE p.publication IS NULL OR lower(p.publication) IN (
	SELECT lower(journal) FROM (
		SELECT max(journal) AS journal, COUNT(article) AS tally
		FROM (SELECT REGEXP_REPLACE(publication, '^The Journal', 'Journal') AS journal, article FROM paper.article_publications) AS stripped
		GROUP BY lower(journal)
		ORDER BY tally DESC, max(journal)
		LIMIT 30
	) AS ranks
)
ORDER BY journal DESC, d.downloads DESC
```

```r
journalframe = read.csv('downloads_journal.csv')
# aggregate(downloads~journal, data=journalframe, median)

ggplot(data=journalframe, aes(
  x=reorder(journal, downloads, FUN=median),
  y=downloads
)) +
geom_boxplot(
  outlier.shape = NA, coef=0,
  fill=themepurple) +
theme_bw() +
coord_flip(ylim=c(0, 3800)) +
labs(x="journal")

library(car)
leveneTest(downloads~journal, data=journalframe)
kruskal.test(downloads~journal, data=journalframe)
library(FSA)
dunnTest(downloads~journal, data=journalframe, method="bh")


# Plotting median against journal impact factor:
medians <- paperframe %>%
  group_by(journal) %>%
  summarize(median = median(downloads))

impactframe = read.csv('impact_scores.csv')
final <- medians %>% left_join(impactframe)

library(ggrepel)
ggplot(data=final, aes(x=median, y=impact, label=journal)) +
geom_point() +
geom_text_repel(aes(label=journal),hjust=0, vjust=0) +
theme_bw() +
labs(x="median downloads per paper", y="2017 journal impact score") +
geom_smooth(method='lm')

linearMod <- lm(median~impact, data=final)
summary(linearMod)
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

Most-downloaded paper:

```sql
SELECT d.article, d.downloads, REPLACE(a.collection, '-', ' ') AS collection
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL
ORDER BY downloads DESC
LIMIT 5;
```

Publication rates over time:

```sql
SELECT COUNT(p.doi)
FROM paper.articles a
INNER JOIN paper.article_publications p ON a.id=p.article
WHERE a.posted < '1-1-2014'
```

Authors who posted in 2018:

```sql
SELECT COUNT(DISTINCT a.author)
FROM paper.article_authors a
INNER JOIN paper.articles p ON p.id=a.article
WHERE p.posted > '12-31-2017';
```

Papers per author:

```sql
SELECT author, COUNT(article)
FROM paper.article_authors
GROUP BY author;
```

```r
asdf
```