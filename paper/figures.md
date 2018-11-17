# Building figures from paper

```r
library(ggplot2)
library(grid)
library(gridExtra)
library(cowplot) # for combining figures
library(plyr)
require(dplyr)
require(scales)

themepurple = "#d0c1ff"
themeorange = "#ffab03"
themeyellow = "#fff7c1"
themeoffwhite = "#f2f6ff"
themedarkgrey = "#565656"

themedarktext = "#707070"
yearline = "black"
yearline_size = 0.5
big_fontsize = 12

integrated_legend = theme(
  legend.position = c(0.35, 0.7),
  legend.background = element_rect(fill=themeoffwhite, size=0.5, linetype="solid"),
  legend.text = element_text(size=big_fontsize)
)
better_line_legend = guides(color = guide_legend(override.aes = list(size = 4)))

setwd('/Users/rabdill/code/rxivist/paper/data') # *tk remove this
```






## Figure 1

### Figure 1a: Median downloads per category
```sql
SELECT d.article, d.downloads, REPLACE(a.collection, '-', ' ') AS collection
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL;
```

```r
paperframe = read.csv('downloads_per_category.csv')

medianplot <- ggplot(data=paperframe, aes(
  x=reorder(collection, downloads, FUN=median),
  y=downloads,
  fill=collection)) +
geom_boxplot(outlier.shape = NA, coef=0) +
scale_y_continuous(labels=comma) +
coord_flip(ylim=c(0,1000)) +
# coord_cartesian(ylim=c(0,1000)) +
theme_bw() +
labs(x="", y="downloads per paper") +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none",
  axis.text = element_text(size=big_fontsize, hjust=0.9)
) +
geom_hline(yintercept=median(paperframe$downloads), col=themedarkgrey, linetype="dashed", size=1)
```

### Figure 1b: Distribution of downloads per paper

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
distroframe = read.csv('downloads_per_paper.csv')

other <- ggplot(distroframe, aes(x=downloads)) +
geom_histogram(
  fill=themeorange,
  bins = 50
) +
scale_x_log10(labels = comma) +
scale_y_continuous(label=function(x) x/1000) +
labs(y = "papers (thousands)", x = "total downloads (log scale)") +
geom_vline(
  xintercept=median(distroframe$downloads),
  col=themedarkgrey, linetype="dashed", size=1
) +
annotate("text", x=median(distroframe$downloads)+6500, y=3250, label=paste("median:", round(median(distroframe$downloads), 2))) +
theme_bw() +
theme(
  plot.background = element_rect(fill = themeoffwhite)
)
```

### Figure 1c: Cumulative downloads over time, per category

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
yearlabel = -210000

x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line(size=1) +
labs(x = "month", y = "total downloads") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 3000000, 500000), labels=comma) +
theme(
  plot.margin = unit(c(1,8,1,1), "lines"), # for right-margin labels
  axis.text.x=element_blank(), # remove x axis labels
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  legend.position="none"
) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 3000000, ymax = 3050000, xmin = 61, xmax = 61) +
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
  grob = textGrob(label = "2014", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = 3, xmax = 3) +
geom_vline(xintercept=3, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = 15, xmax = 15) +
geom_vline(xintercept=15, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = 27, xmax = 27) +
geom_vline(xintercept=27, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = 39, xmax = 39) +
geom_vline(xintercept=39, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = 51, xmax = 51) +
geom_vline(xintercept=51, col=yearline, size=yearline_size)

main <- ggplot_gtable(ggplot_build(x))
main$layout$clip[main$layout$name == "panel"] <- "off"
```

### Figure 1 combined

```r
plot_grid(medianplot, main, labels=c("(a)", "(c)"),
  label_x = .2, label_y = 0,
  hjust = -0.5, vjust = -0.5,
  ncol = 2, nrow = 1,
  align = "h"
) +
draw_plot_label("(b)", size = 14, x = 0.6, y=0.6)

print(other, vp = viewport(
  width = 0.22, height = 0.3,
  x = 0.71,
  y = 0.75
))
```





## Figure 2

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	REPLACE(collection, '-', ' ') AS collection,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1,2
ORDER BY 1,2;
```
(Data organized in `submissions_per_month.xlsx`, then final numbers transferred to `submissions_per_month.csv`)

### Figure 2a: Cumulative monthly submissions per category

```r
# Cumulative submissions over time
monthframe=read.csv('submissions_per_month.csv')

yearlabel1 = -380
x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line(size=1) +
labs(x = "", y = "cumulative preprints") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 6100, 1000), labels=comma) +
theme(
  plot.margin = unit(c(1,8,1,1), "lines"), # for right-margin labels
  axis.text.x=element_blank(), # remove x axis labels
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  legend.position="none"
) +
annotation_custom(
  grob = textGrob(label = "neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 6081, ymax = 6081, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 4064, ymax = 4064, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "evolutionary bio.", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 3200, ymax = 3200, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "genomics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2900, ymax = 2900, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2600, ymax = 2600, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "genetics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2245, ymax = 2245, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "cell biology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1605, ymax = 1605, xmin = 61, xmax = 61
) +
geom_vline(xintercept=3, col=yearline, size=yearline_size) +
geom_vline(xintercept=15, col=yearline, size=yearline_size) +
geom_vline(xintercept=27, col=yearline, size=yearline_size) +
geom_vline(xintercept=39, col=yearline, size=yearline_size) +
geom_vline(xintercept=51, col=yearline, size=yearline_size)

cumulative <- ggplot_gtable(ggplot_build(x))
cumulative$layout$clip[cumulative$layout$name == "panel"] <- "off"
```

### Figure 2b: Monthly preprints per category

```r
yearlabel2 = -140
x <- ggplot(monthframe, aes(x=date, y=submissions, fill=collection)) +
geom_bar(stat="identity", color="white") +
theme_bw() +
labs(x="month", y="preprints posted (month)") +
theme(
  axis.text.x=element_blank(), # remove x axis labels
  axis.text = element_text(size=big_fontsize, color = themedarktext),
  axis.title = element_text(size=big_fontsize),
  legend.position="none"
) +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel2, ymax = yearlabel2, xmin = 3, xmax = 3) +
geom_vline(xintercept=3, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel2, ymax = yearlabel2, xmin = 15, xmax = 15) +
geom_vline(xintercept=15, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel2, ymax = yearlabel2, xmin = 27, xmax = 27) +
geom_vline(xintercept=27, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel2, ymax = yearlabel2, xmin = 39, xmax = 39) +
geom_vline(xintercept=39, col=yearline, size=yearline_size) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 1, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel2, ymax = yearlabel2, xmin = 51, xmax = 51) +
geom_vline(xintercept=51, col=yearline, size=yearline_size)

monthly <- ggplot_gtable(ggplot_build(x))
monthly$layout$clip[monthly$layout$name == "panel"] <- "off"
```

### Figure 2 combined

```r
legendplot <- ggplot(
    monthframe, aes(x=date, y=submissions, fill=collection)
  ) +
  geom_bar(stat="identity", color="white") +
  guides(fill=guide_legend(ncol=3)) +
  theme(legend.text = element_text(size=big_fontsize))

legend <- get_legend(legendplot)

pics <- plot_grid(cumulative, monthly,
  labels=c("(a)", "(b)"),
  rel_heights = c(1,1),
  label_x = 0, label_y = 0,
  hjust = -0.5, vjust = -0.5,
  ncol = 1, nrow = 2,
  align = "v"
)

plot_grid(
  pics, legend,
  rel_heights = c(3,1),
  ncol=1, nrow=2
)
```







## Figure S1

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
  x=reorder(collection, authors, FUN=median),
  y=authors,
  fill=collection
)) +
geom_boxplot(outlier.shape = NA) +
scale_y_continuous() +
coord_flip(ylim=c(0,25)) +
theme_bw() +
labs(x="collection", y="authors per paper") +
theme(
  panel.grid.major.y = element_blank(),
  legend.position="none",
  axis.text = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
) +
# geom_hline(yintercept=median(authorframe$authors), col=themedarkgrey, linetype="dashed", size=1) +
# annotate("text", y=median(authorframe$authors)+4, x=1, label=paste("overall median:", round(median(authorframe$authors), 2))) +
```