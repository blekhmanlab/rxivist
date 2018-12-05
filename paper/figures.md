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
big_fontsize = 12

integrated_legend = theme(
  legend.position = c(0.35, 0.7),
  legend.background = element_rect(fill=themeoffwhite, size=0.5, linetype="solid"),
  legend.text = element_text(size=big_fontsize)
)
better_line_legend = guides(color = guide_legend(override.aes = list(size = 4)))

yearline = "black"
yearline_size = 0.5
yearline_alpha = 1
yearline_2014 = 8 # position of first year label
# Adds an x axis with delineations and labels for each year
# plot: A ggplot object
# labels: boolean. Whether to include the year numbers.
# yearlabel: A number indicating a y offset, for vertically positioning the year labels
add_year_x <- function(plot, labels, yearlabel)
{
  x <- plot +
    geom_vline(xintercept=2.5, col=yearline, size=yearline_size, alpha=yearline_alpha) +

    geom_vline(xintercept=14.5, col=yearline, size=yearline_size, alpha=yearline_alpha) +
    geom_vline(xintercept=26.5, col=yearline, size=yearline_size, alpha=yearline_alpha) +
    geom_vline(xintercept=38.5, col=yearline, size=yearline_size, alpha=yearline_alpha) +
    geom_vline(xintercept=50.5, col=yearline, size=yearline_size, alpha=yearline_alpha)

  if(labels) {
    x <- x +
      annotation_custom(
      grob = textGrob(label = "2014", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
      ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014, xmax = yearline_2014) +
    annotation_custom(
      grob = textGrob(label = "2015", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
      ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014+12, xmax = yearline_2014+12) +
    annotation_custom(
      grob = textGrob(label = "2016", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
      ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 24, xmax = yearline_2014 + 24) +
    annotation_custom(
      grob = textGrob(label = "2017", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
      ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 36, xmax = yearline_2014 + 36) +
    annotation_custom(
        grob = textGrob(label = "2018", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
        ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 48, xmax = yearline_2014 + 48)
  }
  return(x)
}

setwd('/Users/rabdill/code/rxivist/paper/data') # *tk remove this
```


## Figure 1: Papers

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	REPLACE(collection, '-', ' ') AS collection,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1,2
ORDER BY 1,2;
```
(Data organized in `submissions_per_month.xlsx`, then final numbers transferred to `submissions_per_month.csv`)

### Figure 1a: Cumulative monthly submissions per category

```r
monthframe=read.csv('submissions_per_month.csv')

x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line(size=1) +
labs(x = "", y = "Cumulative preprints") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 6100, 1000), labels=comma) +
theme(
  plot.margin = unit(c(1,8,1,1), "lines"), # for right-margin labels
  axis.text.x=element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  legend.position="none"
) +
annotation_custom(
  grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 6081, ymax = 6081, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 4150, ymax = 4150, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 3300, ymax = 3300, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 3000, ymax = 3000, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2600, ymax = 2600, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2245, ymax = 2245, xmin = 61, xmax = 61
) +
annotation_custom(
  grob = textGrob(label = "Cell Biology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1605, ymax = 1605, xmin = 61, xmax = 61
)

x <- add_year_x(x, FALSE)

cumulative <- ggplot_gtable(ggplot_build(x))
cumulative$layout$clip[cumulative$layout$name == "panel"] <- "off"
```

### Figure 1b: Monthly preprints per category

```r
x <- ggplot(monthframe, aes(x=date, y=submissions, fill=collection)) +
geom_bar(stat="identity", color="white") +
theme_bw() +
labs(x="Month", y="Preprints posted (month)") +
theme(
  axis.text.x=element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  axis.title.x = element_text(size=big_fontsize, vjust=-3),
  legend.position="none",
  plot.margin = unit(c(-0.75, 0, 0, 0), "cm") # for spacing in the plot_grid
)

x <- add_year_x(x, TRUE, -170)

monthly <- ggplot_gtable(ggplot_build(x))
monthly$layout$clip[monthly$layout$name == "panel"] <- "off"
```

### Figure 1 combined

```r
legendplot <- ggplot(
    monthframe, aes(x=date, y=submissions, fill=collection)
  ) +
  geom_bar(stat="identity", color="white") +
  guides(fill=guide_legend(ncol=3)) +
  theme(
    legend.text = element_text(size=big_fontsize),
    legend.margin = margin(t=30, b = 50, l = 100, unit = "pt")
  )

plot_grid(
  plot_grid(cumulative, monthly,
    labels=c("\n\n(a)", "(b)"),
    vjust = 0.25,
    rel_heights = c(1,1),
    ncol = 1, nrow = 2,
    align = "v"
  ),
  get_legend(legendplot),
  rel_heights = c(7,3),
  ncol=1, nrow=2
)
```

## Figure 2: Downloads


### Figure 2a: Median downloads per category
```sql
SELECT d.article, d.downloads, REPLACE(a.collection, '-', ' ') AS collection
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL;
```

```r
paperframe = read.csv('downloads_per_category.csv')

two_a <- ggplot(data=paperframe, aes(
    x=reorder(collection, downloads, FUN=median),
    y=downloads,
    fill=collection)) +
  geom_boxplot(outlier.shape = NA, coef=0) +
  scale_y_continuous(labels=comma) +
  coord_flip(ylim=c(0,1000)) +
  theme_bw() +
  labs(x="", y="Downloads per paper") +
  theme(
    panel.grid.major.y = element_blank(),
    legend.position="none",
    axis.text = element_text(size=big_fontsize),
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    plot.margin = unit(c(0.5,0.5,0,0), "cm")
  ) +
  geom_hline(yintercept=median(paperframe$downloads), col=themedarkgrey, linetype="dashed", size=1)

# comparing neuroscience papers to non-neuroscience:
paperframe$isneuro <- ifelse(paperframe$collection =='neuroscience',TRUE, FALSE)
ddply(paperframe, .(isneuro), summarise, med = median(downloads))
wilcox.test(downloads~isneuro, data=paperframe)

# comparing all collections:
leveneTest(downloads~collection, data=paperframe)
kruskal.test(downloads~collection, data=paperframe)
oneway.test(downloads~collection, data=paperframe) # Welch's ANOVA
```

### Figure 2b: Cumulative downloads over time, per category

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
x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
geom_line(size=1) +
labs(x = "Month", y = "Total downloads (cumulative)") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 3000000, 500000), labels=comma) +
theme(
  plot.margin = unit(c(0,6.5,0,0), "lines"), # for right-margin labels
  axis.text.x=element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title = element_text(size=big_fontsize),
  legend.position="none",
  panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA)
) +
annotation_custom(
  grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 3000000, ymax = 3050000, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2900000, ymax = 2926524, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 2714730, ymax = 2714730, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1507955, ymax = 1507955, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 1348577, ymax = 1348577, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 851647, ymax = 851647, xmin = 61, xmax = 61) +
annotation_custom(
  grob = textGrob(label = "Cancer Biology", hjust = 0, gp = gpar(fontsize = big_fontsize)),
  ymin = 659128, ymax = 659128, xmin = 61, xmax = 61)

x <- add_year_x(x, TRUE, -190000)

two_b <- ggplot_gtable(ggplot_build(x))
two_b$layout$clip[two_b$layout$name == "panel"] <- "off"
```

### Figure 2b (inset): Distribution of downloads per paper

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

two_binset <- ggplot(distroframe, aes(x=downloads)) +
  geom_histogram(
    fill=themeorange,
    bins = 50
  ) +
  scale_x_log10(labels = comma, expand=c(0,0)) +
  scale_y_continuous(labels = comma) +
  coord_cartesian(xlim=c(1, 100000)) +
  labs(y = "Papers", x = "Total downloads (log scale)") +
  geom_vline(
    xintercept=median(distroframe$downloads),
    col=themedarkgrey, linetype="dashed", size=1
  ) +
  annotate("text", x=median(distroframe$downloads)+6500, y=3250, label=paste("median:", round(median(distroframe$downloads), 2))) +
  theme_bw() +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA),
    axis.text = element_text(size=big_fontsize, color=themedarkgrey),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize),
    plot.margin = unit(c(0,0,0,0), "cm")
  )
```



### Figure 2c: Downloads per month, by year
```sql
SELECT month, year, sum(pdf) AS downloads
FROM paper.article_traffic
GROUP BY year, month
ORDER BY year, month
```

```r
dlframe=read.csv('downloads_per_month_per_year.csv')

yearlabel = 1.35
two_c <- ggplot(dlframe, aes(x=month, y=downloads, group=year, color=year)) +
  geom_line(size=1) +
  labs(x = "Month", y = "Overall downloads (month)") +
  theme_bw() +
  coord_cartesian(xlim=c(1,12)) +
  scale_y_continuous(breaks=seq(0, 1300000, 250000), labels=comma) +
  scale_x_continuous(breaks=seq(0, 12, 1), expand=c(0,0)) +
  theme(
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    panel.grid.minor = element_blank(),
    legend.position = "none",
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    plot.margin = unit(c(0.5,0,0,0), "cm"),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize, vjust = -35),
  ) +
  annotation_custom(
    grob = textGrob(label = "2013", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = -10000, ymax = -10000, xmin = 10, xmax = 10
  ) +
  annotation_custom(
    grob = textGrob(label = "2014", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = -15000, ymax = -15000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 100000, ymax = 100000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 185000, ymax = 185000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 375000, ymax = 375000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 750000, ymax = 750000, xmin = yearlabel, xmax = yearlabel
  )
```


### Figure 2d: Monthly downloads overall

```r
monthframe=read.csv('downloads_per_month_cumulative.csv')

x <- ggplot(monthframe, aes(x=date, y=month, group=collection, fill=collection)) +
geom_bar(stat="identity", color="white") +
labs(x = "Month", y = "Overall downloads (month)") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 1250000, 250000), labels=comma) +
theme(
  axis.text.x = element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  axis.title.x = element_text(size=big_fontsize, vjust=1),
  legend.position = "none",
  plot.margin = unit(c(0,0,0,0), "cm"),
  panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA)
)

x <- add_year_x(x, TRUE, -70000)

two_d <- ggplot_gtable(ggplot_build(x))
two_d$layout$clip[two_d$layout$name == "panel"] <- "off"
```



### Figure 2 combined

```r
ab <- align_plots(two_a, two_b, align = "h", axis = "bt")
bd <- align_plots(ab[[2]], two_d, align = "v", axis = "lr")
ac <- align_plots(ab[[1]], two_c, align = "v", axis = "r")
cd <- align_plots(ac[[2]], bd[[2]], align = "h", axis = "tb")

plot_grid(
  ac[[1]], bd[[1]], cd[[1]], cd[[2]],
  ncol = 2, nrow = 2,
  labels = c("(a)", "(b)", "(c)", "(d)")
) +
draw_plot(two_binset, 0.58, 0.72, 0.22, 0.22)

```

## Figure 3: Publications

### Figure 3a: Publication rate by month

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

x <- ggplot(paperframe, aes(x=month, y=rate)) +
geom_point() +
labs(x = "Month", y = "Proportion") +
theme_bw() +
theme(
  axis.text.x=element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.x = element_text(size=big_fontsize, hjust=0.45, vjust=-1.2),
  axis.title.y = element_text(size=big_fontsize),
  plot.margin = unit(c(0.5, 0.5, 0.5, 1), "cm")
) +
geom_hline(yintercept=0.40979, col=themedarkgrey, linetype="dashed", size=1) +
annotate("text", y=0.48, x=11.2, label="overall proportion: 0.4098")

x <- add_year_x(x, TRUE, -0.075)

monthrate <- ggplot_gtable(ggplot_build(x))
monthrate$layout$clip[monthrate$layout$name == "panel"] <- "off"
```


### Figure 3b: Publication rate by category

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

catproportion <- ggplot(
    data=pubframe,
    aes(
      x=reorder(collection, proportion),
      y=proportion,
      fill=collection
    )
  ) +
  geom_bar(stat="identity") +
  scale_y_continuous(expand=c(0,0)) +
  geom_hline(yintercept=0.40979, col=themedarkgrey, linetype="dashed", size=1) +
  labs(y="Proportion (category)") +
  theme_bw() +
  coord_flip() +
  theme(
    axis.text.x = element_text(size=big_fontsize, color = themedarktext),
    axis.text.y = element_text(size=big_fontsize, color = themedarktext),
    axis.title.y = element_blank(),
    legend.position="none",
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA)
  )
```

### Figure 3c: Total publications by category
```r
cattotals <- ggplot(
    data=pubframe,
    aes(
      x=reorder(collection, proportion),
      y=published,
      label=published,
      fill=collection
    )
  ) +
  geom_bar(stat="identity") +
  scale_y_continuous(labels=comma, expand=c(0,0), breaks=seq(0, 2500, 750)) +
  labs(x="", y="Count") +
  theme_bw() +
  coord_flip(ylim=c(-55,2500)) +
  theme(
    axis.text.y = element_blank(),
    legend.position="none",
    axis.text.x = element_text(size=big_fontsize, color = themedarktext),
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    plot.margin = unit(c(0, 0.5, 0, 0), "cm")
  )
```

### Figure 3 combined

```r
plot_grid(
  monthrate,
  plot_grid(catproportion, cattotals,
    labels=c("(b)", "(c)"),
    rel_widths=c(3,2),
    hjust = 0,
    ncol = 2, nrow = 1,
    align = "h"
  ),
  ncol = 1, nrow = 2,
  rel_heights = c(1,3),
  labels = c("(a)", ""),
  hjust = 0
)
```


## Figure 4: Preprint publications per journal

### Cleaning data

```sql
TRUNCATE paper.article_publications
INSERT INTO paper.article_publications (
	SELECT p.article, p.doi, p.publication
	FROM prod.article_publications p
	INNER JOIN paper.articles a ON a.id=p.article
)

UPDATE paper.article_publications SET publication=LOWER(publication)
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the journal', 'journal')
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the american journal', 'american journal')
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the international journal', 'international journal')
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '&', 'and')

-- SELECT DISTINCT publication
-- FROM paper.article_publications
-- ORDER BY 1

UPDATE paper.article_publications
SET publication='acta crystallographica section d'
WHERE publication='acta crystallographica section d structural biology'

UPDATE paper.article_publications
SET publication='american journal of physiology - renal physiology'
WHERE publication='american journal of physiology - renal physiology'

UPDATE paper.article_publications
SET publication='avian research'
WHERE publication='bmc avian research'

UPDATE paper.article_publications
SET publication='bioinformatics'
WHERE publication='bioinformatics '

UPDATE paper.article_publications
SET publication='cognitive, affective, and behavioral neuroscience'
WHERE publication='cognitive, affective and behavioral neuroscience'

UPDATE paper.article_publications
SET publication='cytometry part a'
WHERE publication='cytometry a'

UPDATE paper.article_publications
SET publication='development'
WHERE publication='development (cambridge, england)'

UPDATE paper.article_publications
SET publication='g3: genes|genomes|genetics'
WHERE publication IN (
  'g3',
  'g3 (bethesda, md.)',
  'g3 genes|genomes|genetics',
  'g3and#58; genes|genomes|genetics',
  'genes|genomes|genetics'
)

UPDATE paper.article_publications
SET publication='genes, brain and behavior'
WHERE publication='genes, brain, and behavior'

UPDATE paper.article_publications
SET publication='integrative biology'
WHERE publication IN (
  'integrative biology : quantitative biosciences from nano to macro',
  'integrrative biology'
)

UPDATE paper.article_publications
SET publication='journal of alzheimer''s disease'
WHERE publication='journal of alzheimer''s disease : jad'

UPDATE paper.article_publications
SET publication='journal of physical chemistry b'
WHERE publication='journal of physical chemistry. b'

UPDATE paper.article_publications
SET publication='journal of physiology'
WHERE publication='journal of physiology-paris'

UPDATE paper.article_publications
SET publication='journal of vegetation science'
WHERE publication='journal of vegitation science'

UPDATE paper.article_publications
SET publication='methods'
WHERE publication='methods (san diego, calif.)'

UPDATE paper.article_publications
SET publication='molecular and cellular proteomics'
WHERE publication='molecular and cellular proteomics : mcp'

UPDATE paper.article_publications
SET publication='philosophical transactions a'
WHERE publication='philosophical transactions of the royal society a: mathematical,				physical and engineering sciences'

UPDATE paper.article_publications
SET publication='philosophical transactions b'
WHERE publication='philosophical transactions of the royal society b: biological sciences'

UPDATE paper.article_publications
SET publication='pnas'
WHERE publication IN (
  'proceedings of the national academy of sciences',
  'proceedings of the national academy of sciences of the united states of america'
)

UPDATE paper.article_publications
SET publication='proceedings of the royal society b: biological sciences'
WHERE publication IN (
  'proceedings. biological sciences',
  'proceedings b'
)

UPDATE paper.article_publications
SET publication='retrovirology'
WHERE publication='bmc retrovirology'

UPDATE paper.article_publications
SET publication='science'
WHERE publication='science (new york, n.y.)'

UPDATE paper.article_publications
SET publication='slas discovery'
WHERE publication='slas discovery: advancing life sciences randd'

UPDATE paper.article_publications
SET publication='slas technology'
WHERE publication='slas technology: translating life sciences innovation'
```

*tk this query needs to change
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

/* Counts for Results section: */
SELECT publication, COUNT(article) AS articles
FROM paper.article_publications
GROUP BY publication
ORDER BY articles DESC
```

```r
pubframe = read.csv('publications_per_journal_categorical.csv')

asdf

figure <- ggplot(pubframe, aes(x=journal, y=tally, fill=collection)) +
  geom_bar(stat="identity", color="white") +
  aes(x = reorder(journal, tally, sum), y = tally, label = tally, fill = collection) +
  coord_flip() +
  labs(x = "Journal", y = "Preprints published") +
  theme_bw() +
  theme(
    panel.grid.major.y = element_blank(),
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    axis.title = element_text(size=big_fontsize),
    legend.position = "none",
    plot.margin = unit(c(0.2,1,0.5,0.2), "cm"),
  )

# The wide x-axis labels (up the side of the plot) mess up the
# alignment of the legend, so it gets added by hand
legendplot <- ggplot(pubframe, aes(x=journal, y=tally, fill=collection)) +
  geom_bar(stat="identity", color="white") +
  aes(x = reorder(journal, tally, sum), y = tally, label = tally, fill = collection) +
  coord_flip() +
  theme_bw() +
  theme(
    legend.text = element_text(size=big_fontsize),
    legend.title = element_text(size=big_fontsize),
    legend.margin = margin(b = 20, unit = "pt")
  ) +
  guides(fill=guide_legend(ncol=3))

plot_grid(figure, get_legend(legendplot),
  ncol = 1, nrow = 2,
  rel_heights = c(2,1)
)
```

## Figure 5: Median bioRxiv downloads per journal

```sql
SELECT d.article, d.downloads, p.publication
FROM paper.alltime_ranks d
LEFT JOIN paper.article_publications p ON d.article=p.article
WHERE p.publication IS NULL OR p.publication IN (
	SELECT publication FROM (
		SELECT publication, COUNT(article) AS tally
		FROM paper.article_publications
		GROUP BY publication
		ORDER BY tally DESC
		LIMIT 30
	) AS ranks
)
ORDER BY p.publication DESC, d.downloads DESC
```

```r
journalframe = read.csv('downloads_journal.csv')
impactframe = read.csv('impact_scores.csv')
details <- journalframe %>% left_join(impactframe)

ggplot(data=details, aes(
  x=reorder(journal, downloads, FUN=median),
  y=downloads,
  fill=open_access
)) +
geom_boxplot(
  outlier.shape = NA, coef=0
) +
theme_bw() +
coord_flip(ylim=c(0, 3650)) +
scale_y_continuous(breaks=seq(0, 3500, 500), expand=c(0,0), labels=comma) +
labs(x="Journal", y="Downloads per paper") +
theme(
  axis.title = element_text(size=big_fontsize),
  axis.text= element_text(size=big_fontsize, color = themedarktext)
) +
guides(fill=guide_legend(
  title = "Open access"
))

library(car)
leveneTest(downloads~journal, data=journalframe)
kruskal.test(downloads~journal, data=journalframe)
library(FSA)
dunnTest(downloads~journal, data=journalframe, method="bh")

medians <- journalframe %>%
  group_by(publication) %>%
  summarize(median = median(downloads))
```




### Comparing published and unpublished papers
```sql
/* Overall data */
SELECT d.article, d.downloads, EXTRACT(year FROM a.posted) AS year,
	CASE WHEN COUNT(p.article) > 0 THEN TRUE
    	ELSE FALSE
    END AS published
FROM paper.alltime_ranks d
LEFT JOIN paper.article_publications p ON d.article=p.article
LEFT JOIN paper.articles a ON d.article=a.id
GROUP BY d.article, a.posted
ORDER BY published DESC, d.downloads DESC

/* Data excluding all papers posted in 2018 */
SELECT *
FROM (
  SELECT d.article, d.downloads, EXTRACT(year FROM a.posted) AS year,
	CASE WHEN COUNT(p.article) > 0 THEN TRUE
    	ELSE FALSE
    END AS published
  FROM paper.alltime_ranks d
  LEFT JOIN paper.article_publications p ON d.article=p.article
  LEFT JOIN paper.articles a ON d.article=a.id
  GROUP BY d.article, a.posted
  ORDER BY published DESC, d.downloads DESC
) AS downloads
WHERE year < 2018;
```

```r
paperframe = read.csv('downloads_publication_status.csv')
library(car)
leveneTest(downloads~published, data=paperframe)
library(MASS)
wilcox.test(downloads~published, data=paperframe, alternative="less")

library(canprot)
CLES(filter(paperframe, published=='False')$downloads, filter(paperframe, published=='True')$downloads)
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


## Figure S2: Median downloads per year

```sql
SELECT d.article, d.downloads, EXTRACT(YEAR FROM a.posted) AS year
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id
WHERE a.collection IS NOT NULL;
```

```r
aframe = read.csv('downloads_per_year.csv')
mediandownloads <- aggregate(downloads~year,data=aframe,median)

# Stacked density plot:
papers <- ggplot(data=aframe, aes(
    x=downloads, group=year, fill=year
  )) +
  geom_density() +
  scale_x_continuous(trans="log10", labels=comma) +
  scale_y_continuous(breaks=seq(0.5, 1.5, 0.5)) +
  coord_cartesian(xlim=c(8,30000)) +
  theme_bw() +
  labs(x="total downloads", y="probability density") +
  theme(
    legend.position="none",
    axis.text = element_text(size=big_fontsize),
    axis.title = element_text(size=big_fontsize)
  ) +
  geom_vline(aes(xintercept=downloads), data=mediandownloads,
    col=themeorange, linetype="dashed", size=1) +
  geom_text(
    aes(label = paste("median:", downloads), x=downloads*3.5, y=1.2),
    data=mediandownloads
  ) +
  facet_grid(rows = vars(year)) +
  theme(
    strip.text = element_text(size=big_fontsize)
  )

leveneTest(downloads~year, data=paperframe)
kruskal.test(downloads~year, data=paperframe)
library(FSA)
dunnTest(downloads~year, data=paperframe, method="bh")
```

## Figure S3

### Figure S3a: Downloads in first month on bioRxiv
```sql
SELECT a.id, t.month, t.year, t.pdf AS downloads
FROM paper.articles a
LEFT JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.year = (
    SELECT MIN(year)
    FROM paper.article_traffic t
    WHERE t.article = a.id
  )
  AND t.month = (
    SELECT MIN(month)
    FROM paper.article_traffic t
    WHERE a.id=t.article AND
      year = (
        SELECT MIN(year)
        FROM paper.article_traffic t
        WHERE t.article = a.id
      )
  )
ORDER BY id
```
```r
firstframe = read.csv('downloads_by_first_month.csv')

firstplot <- ggplot(data=firstframe, aes(
  x=year,
  y=downloads,
  group=year
)) +
geom_boxplot(outlier.shape = NA, coef=0) +
scale_y_continuous(breaks=seq(0, 250, 50)) +
scale_x_continuous(breaks=seq(2013, 2018, 1)) +
coord_cartesian(ylim=c(0,160)) +
theme_bw() +
labs(x="Year", y="Downloads in first month") +
theme(
  legend.position="none",
  axis.text.y = element_text(size=big_fontsize),
  axis.title.y = element_text(size=big_fontsize),
  axis.title.x = element_blank(),
  axis.text.x = element_blank()
)
```

### Figure S3b: Best month of downloads
```sql
SELECT a.id, EXTRACT(year FROM a.posted) AS year, t.pdf AS downloads
FROM paper.articles a
LEFT JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.pdf = (
    SELECT MAX(pdf)
    FROM paper.article_traffic t
    WHERE t.article = a.id
  )
ORDER BY id
```

```r
maxframe = read.csv('downloads_max_by_year_posted.csv')

maxplot <- ggplot(data=maxframe, aes(
  x=year,
  y=downloads,
  group=year
)) +
geom_boxplot(outlier.shape = NA, coef=0) +
scale_x_continuous(breaks=seq(2013, 2018, 1)) +
coord_cartesian(ylim=c(0,210)) +
scale_y_continuous(breaks=seq(0, 250, 50)) +
theme_bw() +
labs(x="Year", y="Downloads in best month") +
theme(
  legend.position="none",
  axis.text.y = element_text(size=big_fontsize, color=themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  axis.title.x = element_blank(),
  axis.text.x = element_blank()
)
```

### Figure S3c: 2018 downloads, by year posted
```sql
SELECT a.id, EXTRACT(year FROM a.posted) AS year, SUM(t.pdf) AS downloads
FROM paper.articles a
LEFT JOIN paper.article_traffic t ON a.id=t.article
WHERE t.year=2018
GROUP BY a.id
ORDER BY downloads DESC
```

```r
latestframe = read.csv('2018_downloads_by_year_posted.csv')

latestplot <- ggplot(data=latestframe, aes(
  x=year,
  y=downloads,
  group=year
)) +
geom_boxplot(outlier.shape = NA, coef=0) +
scale_x_continuous(breaks=seq(2013, 2018, 1)) +
scale_y_continuous(breaks=seq(0, 250, 50)) +
coord_cartesian(ylim=c(0,280)) +
theme_bw() +
labs(x="Year posted", y="Downloads in 2018") +
theme(
  legend.position="none",
  axis.text.y = element_text(size=big_fontsize, color=themedarktext),
  axis.title = element_text(size=big_fontsize),
  axis.text.x = element_text(
    size=big_fontsize,
    hjust=1,
    color=themedarktext,
    angle = 45
  )
)
```

### Figure S3 combined

```r
plot_grid(firstplot, maxplot, latestplot,
  labels=c("(a)", "(b)", "(c)"),
  ncol = 1, nrow = 3,
  align = "v"
)
```

### Figure S5: Downloads over time relative to posting
```sql
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 1 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 2 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 1
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 3 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 2
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 4 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 3
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 5 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 4
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 6 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 5
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 7 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 6
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 8 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 7
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 9 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 8
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 10 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 9
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 11 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 10
  )
UNION
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS posted, a.collection, 12 AS monthnum, t.pdf AS downloads
FROM paper.articles a
INNER JOIN paper.article_traffic t
  ON a.id=t.article
  AND t.id IN (
    SELECT id
    FROM paper.article_traffic traf
    WHERE traf.article=a.id
    ORDER BY year, month
    LIMIT 1
    OFFSET 11
  )
ORDER BY id, monthnum

/* Overall median: */
SELECT median(pdf)
FROM paper.article_traffic
```
```r
firstframe = read.csv('downloads_by_months.csv')

ggplot(data=firstframe, aes(
  x=monthnum,
  y=downloads,
  group=monthnum
)) +
geom_line(outlier.shape = NA, coef=0) +
scale_y_continuous(breaks=seq(0, 150, 25)) +
scale_x_continuous(breaks=seq(0, 12, 1)) +
coord_cartesian(ylim=c(0,130)) +
theme_bw() +
labs(x="months on bioRxiv", y="downloads in month") +
theme(
  legend.position="none",
  axis.title = element_text(size=big_fontsize),
  axis.text = element_text(size=big_fontsize, color=themedarktext),
) +
geom_hline(yintercept=15, col=themedarkgrey, linetype="dashed", size=1)

# median_thing <- function(data, i){
#   print(sort(table(i),decreasing=TRUE)[1:3])
#   return(median(data[i]))
# }
# results <- boot(filter(firstframe, monthnum==1)$downloads, statistic=median_thing, R=100)
# boot.ci(results, conf=0.95, type="basic")
```


### Figure S6: Tweet-friendly graphs

#### Figure S6a: Total papers over time
```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1
ORDER BY 1;
```

```r
# Cumulative submissions over time
monthframe=read.csv('submissions_per_month_overall.csv')

yearlabel = -1000
x <- ggplot(monthframe, aes(date, cumulative, group=1)) +
geom_line(size=1) +
geom_area(fill=themepurple) +
labs(x = "", y = "", title="Total preprints on bioRxiv over time") +
theme_bw() +
scale_y_continuous(breaks=seq(0, 35000, 5000), expand=c(0,0), labels=comma) +
scale_x_discrete(expand=c(0,0)) +
theme(
  axis.text.x=element_blank(),
  axis.text.y = element_text(size=big_fontsize, color = themedarktext),
  axis.title.y = element_text(size=big_fontsize),
  legend.position="none"
) +
annotation_custom(
  grob = textGrob(label = "2014", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014, xmax = yearline_2014) +
geom_vline(xintercept=3, col=yearline, size=yearline_size, alpha=yearline_alpha) +
annotation_custom(
  grob = textGrob(label = "2015", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014+12, xmax = yearline_2014+12) +
geom_vline(xintercept=15, col=yearline, size=yearline_size, alpha=yearline_alpha) +
annotation_custom(
  grob = textGrob(label = "2016", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 24, xmax = yearline_2014 + 24) +
geom_vline(xintercept=27, col=yearline, size=yearline_size, alpha=yearline_alpha) +
annotation_custom(
  grob = textGrob(label = "2017", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 36, xmax = yearline_2014 + 36) +
geom_vline(xintercept=39, col=yearline, size=yearline_size, alpha=yearline_alpha) +
annotation_custom(
  grob = textGrob(label = "2018", hjust = 0.5, vjust=1, gp = gpar(fontsize = big_fontsize, col=themedarktext)),
  ymin = yearlabel, ymax = yearlabel, xmin = yearline_2014 + 48, xmax = yearline_2014 + 48) +
geom_vline(xintercept=51, col=yearline, size=yearline_size, alpha=yearline_alpha)

cumulative <- ggplot_gtable(ggplot_build(x))
cumulative$layout$clip[cumulative$layout$name == "panel"] <- "off"
grid.draw(cumulative)
```


## Analysis

Finding papers with traffic data from before the year they were posted:
```sql
SELECT * FROM (
	SELECT a.id, EXTRACT(year FROM a.posted) AS posted, MIN(t.year) AS traffic
	FROM paper.articles a
	INNER JOIN paper.article_traffic t ON a.id=t.article
	GROUP BY a.id
) AS years
WHERE posted != traffic
```

## Table S2: Paper count by author

```sql
SELECT a.id, a.name, COUNT(p.article) AS papers, COUNT(e.email) AS emails
FROM paper.authors a
INNER JOIN paper.article_authors p
  ON a.id=p.author
INNER JOIN paper.author_emails e
  ON a.id=e.author
GROUP BY 1
ORDER BY 3 DESC

```


## Table 1: Authors per year

```sql
SELECT firstcount.year, firstcount.count, overall.count
FROM (
  SELECT year, COUNT(DISTINCT author)
  FROM (
    SELECT a.author, MIN(EXTRACT(year FROM p.posted)) AS year
    FROM paper.article_authors a
    LEFT JOIN paper.articles p ON a.article=p.id
    GROUP BY 1
    ORDER BY 2
  ) AS allfirsts
  GROUP BY 1
) AS firstcount
LEFT JOIN (
  SELECT COUNT(DISTINCT a.author), EXTRACT(year FROM p.posted) AS year
  FROM paper.article_authors a
  LEFT JOIN paper.articles p ON a.article=p.id
  GROUP BY 2
  ORDER BY 2
) overall
ON firstcount.year = overall.year
```
