# Tracking the popularity and outcome of all bioRxiv preprints

Below is the code used to generate all figures in the manuscript.

* [Figure 1](#figure-1-papers): Papers
* [Figure 2](#figure-2-downloads): Downloads
  * [Supplement 1](#figure-2-supplement-1-downloads-over-time-relative-to-posting): Downloads over time relative to posting
  * [Supplement 2](#figure-2-supplement-2-proportion-of-downloads-per-month-on-biorxiv): Proportion of downloads per month on bioRxiv
  * [Supplement 3](#figure-2-supplement-3-downloads-by-year-posted): Downloads by year posted
  * [Supplement 4](#figure-2-supplement-4-median-downloads-per-year): Median downloads per year posted
* [Figure 3](#figure-3-publications): Publications
* [Figure 4](#figure-4-time-to-publication): Time to publication
* [Figure 5](#figure-5-preprint-publications-per-journal): Preprint publications per journal
* [Figure 6](#figure-6-median-biorxiv-downloads-per-journal): Median bioRxiv downloads per journal
* [Table 1](#table-1-authors-per-year): Authors per journal
* [Table 2](#table-2-downloads-of-published-and-unpublished-papers): Downloads of published and unpublished papers
* [Table S1](#table-s1-articles-per-journal-september-2018): Articles per journal, September 2018
* [Table S2](#table-s2-papers-per-author): Papers per author
* [Table S3](#table-s3-authors-and-papers-by-institution): Authors and papers by institution
* [In-text analysis](#analysis)

## R environment setup
```r
library(ggplot2)
library(grid)
library(gridExtra)
library(cowplot) # for combining figures
library(plyr)
require(dplyr)
require(scales)
library(ggrepel)

themepurple = "#d0c1ff"
themeorange = "#ffab03"
themeyellow = "#fff7c1"
themeoffwhite = "#f2f6ff"
themedarkgrey = "#565656"

themedarktext = "#707070"
big_fontsize = unit(12, "pt")

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

color.neuroscience = '#47a7f8'
color.bioinformatics = '#c99332'
color.evolutionarybio = '#56bd88'
color.genomics = '#55bdb8'
color.microbiology = '#50b7de'
color.genetics = '#56bea0'
color.cellbio = '#98a733'
color.cancerbio = '#aba233'

capitalized_cats <- data.frame(
  "old" = c(
    'animal behavior and cognition',
    'biochemistry',
    'bioengineering',
    'bioinformatics',
    'biophysics',
    'cancer biology',
    'cell biology',
    'clinical trials',
    'developmental biology',
    'ecology',
    'epidemiology',
    'evolutionary biology',
    'genetics',
    'genomics',
    'immunology',
    'microbiology',
    'molecular biology',
    'neuroscience',
    'paleontology',
    'pathology',
    'pharmacology and toxicology',
    'physiology',
    'plant biology',
    'scientific communication and education',
    'synthetic biology',
    'systems biology',
    'zoology'
  ),
  "new" = c(
    'Animal Behav. & Cognition',
    'Biochemistry',
    'Bioengineering',
    'Bioinformatics',
    'Biophysics',
    'Cancer Bio.',
    'Cell Bio.',
    'Clinical Trials',
    'Developmental Bio.',
    'Ecology',
    'Epidemiology',
    'Evolutionary Bio.',
    'Genetics',
    'Genomics',
    'Immunology',
    'Microbiology',
    'Molecular Bio.',
    'Neuroscience',
    'Paleontology',
    'Pathology',
    'Pharmacology & Toxicology',
    'Physiology',
    'Plant Bio.',
    'Scientific Comm. & Edu.',
    'Synthetic Bio.',
    'Systems Bio.',
    'Zoology'
  )
)

capitalized_journals <- data.frame(
  "old" = c(
    'scientific reports',
    'elife',
    'plos one',
    'nature communications',
    'bioinformatics',
    'pnas',
    'plos computational biology',
    'plos genetics',
    'genetics',
    'nucleic acids research',
    'g3',
    'g3: genes|genomes|genetics',
    'neuroimage',
    'genome biology',
    'genome research',
    'bmc genomics',
    'journal of neuroscience',
    'molecular biology and evolution',
    'bmc bioinformatics',
    'cell reports',
    'nature genetics',
    'nature methods',
    'peerj',
    'genome biology and evolution',
    'plos biology',
    'mbio',
    'biophysical journal',
    'molecular ecology',
    'development',
    'molecular biology of the cell',
    'gigascience'
  ),
  "new" = c(
    'Scientific Reports',
    'eLife',
    'PLOS ONE',
    'Nature Communications',
    'Bioinformatics',
    'PNAS',
    'PLOS Computational Biology',
    'PLOS Genetics',
    'Genetics',
    'Nucleic Acids Research',
    'G3',
    'G3',
    'NeuroImage',
    'Genome Biology',
    'Genome Research',
    'BMC Genomics',
    'Journal of Neuroscience',
    'Molecular Biology and Evolution',
    'BMC Bioinformatics',
    'Cell Reports',
    'Nature Genetics',
    'Nature Methods',
    'PeerJ',
    'Genome Biology and Evolution',
    'PLOS Biology',
    'mBio',
    'Biophysical Journal',
    'Molecular Ecology',
    'Development',
    'Molecular Biology of the Cell',
    'GigaScience'
  )
)
```

## Figure 1: Papers

The following SQL query fetches monthly submissions per category; the file `submissions_per_month_cumulative.xlsx` has an example of how to use these to generate running totals for each category, which are then written to `submissions_per_month.csv`.
```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	REPLACE(collection, '-', ' ') AS collection,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1,2
ORDER BY 1,2;
```

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
    grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.neuroscience)),
    ymin = 6081, ymax = 6081, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.bioinformatics)),
    ymin = 4150, ymax = 4150, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.evolutionarybio)),
    ymin = 3300, ymax = 3300, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.genomics)),
    ymin = 3000, ymax = 3000, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.microbiology)),
    ymin = 2600, ymax = 2600, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.genetics)),
    ymin = 2245, ymax = 2245, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Cell Biology", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.cellbio)),
    ymin = 1605, ymax = 1605, xmin = 62, xmax = 62
  )

x <- add_year_x(x, TRUE, -480)

# We have to change these settings to allow labels to appear
# outside the plot margins:
cumulative <- ggplot_gtable(ggplot_build(x))
cumulative$layout$clip[cumulative$layout$name == "panel"] <- "off"
```

### Figure 1b: Monthly preprints per category

```r
# Convert category names to capitalized versions for printing:
printable <- monthframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(date, collection, submissions, cumulative)

x <- ggplot(printable, aes(x=date, y=submissions, fill=collection)) +
  geom_bar(stat="identity", color="white") +
  theme_bw() +
  labs(x="Month", y="Preprints posted (month)") +
  scale_y_continuous(labels=comma) +
  theme(
    axis.text.x=element_blank(),
    axis.text.y = element_text(size=big_fontsize, color = themedarktext),
    axis.title.y = element_text(size=big_fontsize),
    axis.title.x = element_text(size=big_fontsize, vjust=-3),
    legend.position="none",
    plot.margin = unit(c(-0.45, 0, 0, 0), "cm") # for spacing in the plot_grid
  ) +
  annotation_custom(
    grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.neuroscience)),
    ymin = 450, ymax = 450, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.microbiology)),
    ymin = 700, ymax = 700, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.bioinformatics)),
    ymin = 1710, ymax = 1710, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.genomics)),
    ymin = 900, ymax = 900, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.evolutionarybio)),
    ymin = 1150, ymax = 1150, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.genetics)),
    ymin = 1000, ymax = 1000, xmin = 62, xmax = 62
  ) +
  annotation_custom(
    grob = textGrob(label = "Cell Biology", hjust = 0, gp = gpar(fontsize = big_fontsize, col=color.cellbio)),
    ymin = 1450, ymax = 1450, xmin = 62, xmax = 62
  )

x <- add_year_x(x, TRUE, -150)

monthly <- ggplot_gtable(ggplot_build(x))
monthly$layout$clip[monthly$layout$name == "panel"] <- "off"
```

#### Figure 1a (inset): Total papers over time

Query for fetching overall monthly submission numbers (not categorized); another column, `cumulative`, is required for the figure and was calculated in this case using Excel.

```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS month,
	COUNT(id) AS submissions
FROM paper.articles
GROUP BY 1
ORDER BY 1;
```

Building the figure:
```r
totalframe=read.csv('submissions_per_month_overall.csv')

axisfunc <- function() {
  function(x) paste(x/1000, "k")
}

x <- ggplot(totalframe, aes(month, cumulative, group=1)) +
  geom_line(size=1) +
  geom_area(fill=themepurple) +
  labs(x = "Month", y = "Total preprints") +
  theme_bw() +
  scale_y_continuous(breaks=seq(0, 40000, 10000), expand=c(0,0), labels=axisfunc()) +
  scale_x_discrete(expand=c(0,0)) +
  theme(
    axis.text.x=element_blank(),
    axis.text.y = element_text(size=big_fontsize, color = themedarktext),
    axis.title.y = element_text(size=big_fontsize),
    legend.position="none"
  )

x <- add_year_x(x, FALSE)

totals <- ggplot_gtable(ggplot_build(x))
totals$layout$clip[totals$layout$name == "panel"] <- "off"
```

### Figure 1 combined

```r
# Legend is built as separate plot so we can more
# easily control its position
legendplot <- ggplot(
    printable, aes(x=date, y=submissions, fill=collection)
  ) +
  geom_bar(stat="identity", color="white") +
  guides(fill=guide_legend(
    ncol=3,
    title = "Collection"
  )) +
  theme(
    legend.text = element_text(size=big_fontsize),
    legend.margin = margin(t=30, b = 50, l = 0, unit = "pt")
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
  ) +
  draw_plot(totals, 0.12, 0.77, 0.42, 0.2)
```

## Figure 2: Downloads

Query for monthly download data by category; as with Figure 1, running totals are calculated by inserting these values into `downloads_per_month.xlsx` and saving the results to `downloads_per_month_cumulative.csv`.

```sql
SELECT article_traffic.year||'-'||lpad(article_traffic.month::text, 2, '0') AS date,
	SUM(article_traffic.pdf) AS month,
	REPLACE(articles.collection, '-', ' ') AS collection
FROM paper.article_traffic
LEFT JOIN paper.articles ON article_traffic.article=articles.id
GROUP BY 1,3
ORDER BY 1,3;
```

### Figure 2a: Monthly downloads overall

```r
monthframe = read.csv('downloads_per_month_cumulative.csv')
monthframe <- monthframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(date,collection,month,cumulative)

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
    plot.margin = unit(c(0,0,0,0.2), "cm"),
    panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA)
  ) +
  annotation_custom(
    grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.neuroscience)),
    ymin = 220000, ymax = 220000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.bioinformatics)),
    ymin = 970000, ymax = 970000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.genomics)),
    ymin = 480000, ymax = 480000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.genetics)),
    ymin = 580000, ymax = 580000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.microbiology)),
    ymin = 375000, ymax = 375000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.evolutionarybio)),
    ymin = 650000, ymax = 650000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Cell Biology", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.cellbio)),
    ymin = 780000, ymax = 780000, xmin = 62, xmax = 62)

x <- add_year_x(x, TRUE, -70000)

two_a <- ggplot_gtable(ggplot_build(x))
two_a$layout$clip[two_a$layout$name == "panel"] <- "off"
```

### Figure 2b: Downloads per month, by year

Query written to `downloads_per_month_per_year.csv`:

```sql
SELECT month, year, sum(pdf) AS downloads
FROM paper.article_traffic
GROUP BY year, month
ORDER BY year, month
```

Panel:
```r
dlframe=read.csv('downloads_per_month_per_year.csv')

yearlabel = 1.35
endyearlabel = 9.9
two_b <- ggplot(dlframe, aes(x=month, y=downloads, group=year, color=year)) +
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
    ymin = -10000, ymax = -10000, xmin = endyearlabel, xmax = endyearlabel
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
    grob = textGrob(label = "2015", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 168000, ymax = 168000, xmin = endyearlabel, xmax = endyearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 195000, ymax = 195000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2016", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 360000, ymax = 360000, xmin = endyearlabel, xmax = endyearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 400000, ymax = 400000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2017", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 660000, ymax = 660000, xmin = endyearlabel, xmax = endyearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 765000, ymax = 765000, xmin = yearlabel, xmax = yearlabel
  ) +
  annotation_custom(
    grob = textGrob(label = "2018", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 1160000, ymax = 1160000, xmin = endyearlabel+0.3, xmax = endyearlabel+0.3
  )
```

### Figure 2c: Cumulative downloads over time, per category

```r
monthframe=read.csv('downloads_per_month_cumulative.csv')
monthframe <- monthframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(date,collection,month,cumulative)

# Cumulative downloads:
x <- ggplot(monthframe, aes(x=date, y=cumulative, group=collection, color=collection)) +
  geom_line(size=1) +
  labs(x = "Month", y = "Total downloads (cumulative)") +
  theme_bw() +
  scale_y_continuous(breaks=seq(0, 3500000, 500000), labels=comma) +
  theme(
    plot.margin = unit(c(0,6.5,0.5,0), "lines"),
    axis.text.x=element_blank(),
    axis.text.y = element_text(size=big_fontsize, color = themedarktext),
    axis.title = element_text(size=big_fontsize),
    legend.position="none",
    panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA)
  ) +
  annotation_custom(
    grob = textGrob(label = "Neuroscience", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.neuroscience)),
    ymin = 3200000, ymax = 3200000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Bioinformatics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.bioinformatics)),
    ymin = 3050000, ymax = 3050000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Genomics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.genomics)),
    ymin = 2900000, ymax = 2900000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Genetics", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.genetics)),
    ymin = 1600000, ymax = 1600000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Evolutionary Bio.", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.evolutionarybio)),
    ymin = 1400000, ymax = 1400000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Microbiology", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.microbiology)),
    ymin = 950000, ymax = 950000, xmin = 62, xmax = 62) +
  annotation_custom(
    grob = textGrob(label = "Cancer Biology", hjust = 0, gp = gpar(fontsize = big_fontsize, col = color.cancerbio)),
    ymin = 700000, ymax = 700000, xmin = 62, xmax = 62)

x <- add_year_x(x, TRUE, -190000)

two_c <- ggplot_gtable(ggplot_build(x))
two_c$layout$clip[two_c$layout$name == "panel"] <- "off"
```

### Figure 2c (inset): Distribution of downloads per paper

```r
two_cinset <- ggplot(paperframe, aes(x=downloads)) +
  geom_histogram(
    fill=themeorange,
    bins = 50
  ) +
  scale_x_log10(labels = comma, expand=c(0,0)) +
  scale_y_continuous(labels = comma) +
  coord_cartesian(xlim=c(1, 100000)) +
  labs(y = "Papers", x = "Total downloads (log scale)") +
  geom_vline(
    xintercept=median(paperframe$downloads),
    col=themedarkgrey, linetype="dashed", size=1
  ) +
  annotate("text", x=median(paperframe$downloads)+6500, y=3250, label=paste("median:", round(median(paperframe$downloads), 2))) +
  theme_bw() +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=0.5, fill = NA),
    axis.text = element_text(size=big_fontsize, color=themedarkgrey),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize),
    plot.margin = unit(c(0,0,0,0), "cm")
  )
```

### Figure 2d: Median downloads per category

Query written to `downloads_per_category.csv`:

```sql
SELECT d.article, d.downloads, REPLACE(a.collection, '-', ' ') AS collection
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id;
```

Panel:

```r
paperframe = read.csv('downloads_per_category.csv')
paperframe <- paperframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(article, downloads, collection)

two_d <- ggplot(data=paperframe, aes(
    x=reorder(collection, downloads, FUN=median),
    y=downloads,
    fill=collection)) +
  geom_boxplot(outlier.shape = NA, coef=0) +
  scale_y_continuous(labels=comma) +
  coord_flip(ylim=c(0,1000)) +
  theme_bw() +
  labs(x="", y="Downloads per paper") +
  theme(
    legend.position="none",
    axis.text = element_text(size=big_fontsize),
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    plot.margin = unit(c(0.5,0.5,0,0), "cm")
  ) +
  geom_hline(yintercept=median(paperframe$downloads), col='yellow', linetype="dashed", size=1.5)
```

### Figure 2 combined

```r
# Aligning panel axes:
ac <- align_plots(two_a, two_c, align = "v", axis = "lr")
ab <- align_plots(ac[[1]], two_b, align = "h", axis = "bt")
bd <- align_plots(ab[[2]], two_d, align = "v", axis = "r")
cd <- align_plots(ac[[2]], bd[[2]], align = "h", axis = "bt")

plot_grid(
    ab[[1]], bd[[1]], cd[[1]], cd[[2]],
    ncol = 2, nrow = 2,
    labels = c("(a)", "(b)", "(c)", "(d)"),
    rel_widths=c(5,5)
  ) +
  draw_plot(two_cinset, 0.095, 0.25, 0.22, 0.22)
```

## Table 1: Authors per year

Query for data recorded directly in manuscript:

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

## Figure 3: Publications

### Figure 3a: Publication rate by month

Query recorded to `publication_rate_month.csv`:

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

Panel:

```r
paperframe = read.csv('publication_rate_month.csv')

x <- ggplot(paperframe, aes(x=month, y=rate)) +
  geom_point() +
  labs(x = "Month", y = "Proportion\npublished") +
  theme_bw() +
  theme(
    axis.text.x=element_blank(),
    axis.text.y = element_text(size=big_fontsize, color = themedarktext),
    axis.title.x = element_text(size=big_fontsize, hjust=0.45, vjust=-1.2),
    axis.title.y = element_text(size=big_fontsize),
    plot.margin = unit(c(0.5, 0.5, 0.5, 1), "cm")
  ) +
  geom_hline(yintercept=0.4196, col=themedarkgrey, linetype="dashed", size=1) +
  annotate("text", y=0.48, x=9.1, label="overall: 0.4196")

x <- add_year_x(x, TRUE, -0.075)

monthrate <- ggplot_gtable(ggplot_build(x))
monthrate$layout$clip[monthrate$layout$name == "panel"] <- "off"
```


### Figure 3b: Publication rate by category

Query written to `publications_per_category.csv`:

```sql
SELECT REPLACE(p.collection, '-', ' ') AS collection, p.published, t.total, (p.published::decimal / t.total) AS proportion
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

Panel:

```r
pubframe = read.csv('publications_per_category.csv')
pubframe <- pubframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(collection, published, total, proportion)

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
  geom_hline(yintercept=0.4196, col=themedarkgrey, linetype="dashed", size=1) +
  labs(y="Proportion published\nfrom category") +
  theme_bw() +
  coord_flip(ylim=c(0,0.55)) +
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
  labs(x="", y="Count published\nfrom category") +
  theme_bw() +
  coord_flip(ylim=c(0,2650)) +
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
    rel_widths=c(2,2),
    hjust = c(0,0.25),
    vjust = 1,
    ncol = 2, nrow = 1,
    align = "h"
  ),
  ncol = 1, nrow = 2,
  rel_heights = c(1,3),
  labels = c("(a)", ""),
  hjust = 0
)
```

## Figure 4: Time to publication

Query written to `publication_time_by_year.csv`:
### Figure 4a: Distribution of time to publication
```sql
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS year, REPLACE(a.collection, '-', ' ') AS collection,
	p.date AS published, (p.date-a.posted) AS interval
FROM paper.articles a
INNER JOIN paper.publication_dates p ON a.id=p.article
WHERE p.date > '1900-01-01' --- Dummy value used for unknown values
ORDER BY interval DESC
```

Panel:

```r
distroframe=read.csv('publication_time_by_year.csv')
# Calculate quantile values to be inserted into plot:
quantile(distroframe$interval, c(0.25, 0.50, 0.75, 0.9, 0.95))

percentlabel = 900
hist <- ggplot(distroframe, aes(x=interval)) +
  geom_histogram(
    bins = 150
  ) +
  coord_cartesian(xlim=c(0,700), ylim=c(0,1000)) +
  scale_x_continuous(breaks=seq(0, 1000, 100), expand=c(0,0)) +
  scale_y_continuous(expand=c(0,0)) +
  labs(x="Age of preprint at publication", y="Preprints") +
  theme_bw() +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize, vjust=0),
    plot.margin = unit(c(0.2,1,0,0), "cm")
  ) +
  geom_vline(
    xintercept=104,
    col=themeorange, linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "25%", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = percentlabel, ymax = percentlabel, xmin = 54, xmax = 64
  ) +
  geom_vline(
    xintercept=165,
    col=themeorange, linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "50%", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = percentlabel, ymax = percentlabel, xmin = 115, xmax = 115
  ) +
  geom_vline(
    xintercept=247,
    col=themeorange, linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "75%", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = percentlabel, ymax = percentlabel, xmin = 197, xmax = 197
  ) +
  geom_vline(
    xintercept=346,
    col="red", linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "90%", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = percentlabel, ymax = percentlabel, xmin = 296, xmax = 296
  ) +
  geom_vline(
    xintercept=420,
    col="red", linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "95%", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = percentlabel, ymax = percentlabel, xmin = 370, xmax = 370
  )
```

### Figure 4b: Time to publication by journal

Query written to `publication_interval_journals.csv`:

```sql
SELECT a.id, REPLACE(j.publication,',', ' ') AS journal, (p.date - a.posted) AS interval
FROM paper.articles a
INNER JOIN paper.article_publications j ON a.id=j.article
INNER JOIN paper.publication_dates p ON a.id=p.article
WHERE p.date > '1900-01-01'
AND j.publication IN (
  SELECT publication FROM (
		SELECT publication, COUNT(article) AS tally
		FROM paper.article_publications
		GROUP BY publication
		ORDER BY tally DESC, publication
		LIMIT 30
	) AS ranks
)
ORDER BY 3 DESC
```

Panel:

```r
timeframe = read.csv('publication_interval_journals.csv')
timeframe <- timeframe %>%
  inner_join(capitalized_journals, by=c("journal"="old"))  %>%
  mutate(journal = new) %>%
  select(journal, interval)

by_journal <- ggplot(timeframe, aes(
    x=reorder(journal, interval, FUN=median),
    y=interval,
    group=journal
  )) +
  geom_boxplot(
    outlier.shape = NA, coef=0,
    fill=themepurple
  ) +
  geom_hline(
    yintercept=165,
    col="red", linetype="dashed", size=1
  ) +
  annotation_custom(
    grob = textGrob(label = "overall median: 165", hjust = 0, gp = gpar(fontsize = big_fontsize)),
    ymin = 200, ymax = 200, xmin = 1, xmax = 1
  ) +
  coord_flip(ylim=c(0,350)) +
  scale_y_continuous(breaks=seq(0, 350, 50)) +
  theme_bw() +
  labs(x="Journal", y="Age of preprint at publication") +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize, vjust=0),
    plot.margin = unit(c(0,1,0.2,0), "cm")
  )
```

 ### Figure 4 combined

 ```r
plot_grid(hist, by_journal,
  ncol = 1, nrow = 2,
  labels = c("(a)", "(b)"),
  vjust = 2.5,
  hjust = -0.25,
  rel_heights = c(1,2)
)
 ```

## Figure 5: Preprint publications per journal

### Cleaning data

These queries were used to improve the accuracy of per-journal statistics by combining names that identify the same journal but would have otherwise appeared as different journals.

```sql
UPDATE paper.article_publications SET publication=LOWER(publication)
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the journal', 'journal');
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the american journal', 'american journal');
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '^the international journal', 'international journal');
UPDATE paper.article_publications SET publication=REGEXP_REPLACE(publication, '&', 'and');

UPDATE paper.article_publications
SET publication='acta crystallographica section d'
WHERE publication='acta crystallographica section d structural biology';

UPDATE paper.article_publications
SET publication='american journal of physiology-renal physiology'
WHERE publication='american journal of physiology - renal physiology';

UPDATE paper.article_publications
SET publication='avian research'
WHERE publication='bmc avian research';

UPDATE paper.article_publications
SET publication='bioinformatics'
WHERE publication='bioinformatics '; ---trailing space

UPDATE paper.article_publications
SET publication='cognitive, affective, and behavioral neuroscience'
WHERE publication='cognitive, affective and behavioral neuroscience';

UPDATE paper.article_publications
SET publication='cytometry part a'
WHERE publication='cytometry a';

UPDATE paper.article_publications
SET publication='development'
WHERE publication='development (cambridge, england)';

UPDATE paper.article_publications
SET publication='g3: genes|genomes|genetics'
WHERE publication IN (
  'g3',
  'g3 (bethesda, md.)',
  'g3 genes|genomes|genetics',
  'g3and#58; genes|genomes|genetics',
  'genes|genomes|genetics'
);

UPDATE paper.article_publications
SET publication='genes, brain and behavior'
WHERE publication='genes, brain, and behavior';

UPDATE paper.article_publications
SET publication='integrative biology'
WHERE publication IN (
  'integrative biology : quantitative biosciences from nano to macro',
  'integrrative biology'
);

UPDATE paper.article_publications
SET publication='journal of alzheimer''s disease'
WHERE publication='journal of alzheimer''s disease : jad';

UPDATE paper.article_publications
SET publication='journal of physical chemistry b'
WHERE publication='journal of physical chemistry. b';

UPDATE paper.article_publications
SET publication='journal of physiology'
WHERE publication='journal of physiology-paris';

UPDATE paper.article_publications
SET publication='journal of vegetation science'
WHERE publication='journal of vegitation science';

UPDATE paper.article_publications
SET publication='methods'
WHERE publication='methods (san diego, calif.)';

UPDATE paper.article_publications
SET publication='molecular and cellular proteomics'
WHERE publication='molecular and cellular proteomics : mcp';

UPDATE paper.article_publications
SET publication='philosophical transactions a'
WHERE publication='philosophical transactions of the royal society a: mathematical,				physical and engineering sciences';

UPDATE paper.article_publications
SET publication='philosophical transactions b'
WHERE publication='philosophical transactions of the royal society b: biological sciences';

UPDATE paper.article_publications
SET publication='pnas'
WHERE publication IN (
  'proceedings of the national academy of sciences',
  'proceedings of the national academy of sciences of the united states of america'
);

UPDATE paper.article_publications
SET publication='proceedings of the royal society b: biological sciences'
WHERE publication IN (
  'proceedings. biological sciences',
  'proceedings b'
);

UPDATE paper.article_publications
SET publication='retrovirology'
WHERE publication='bmc retrovirology';

UPDATE paper.article_publications
SET publication='science'
WHERE publication='science (new york, n.y.)';

UPDATE paper.article_publications
SET publication='slas discovery'
WHERE publication='slas discovery: advancing life sciences randd';

UPDATE paper.article_publications
SET publication='slas technology'
WHERE publication='slas technology: translating life sciences innovation';
```

Query written to `publications_per_journal_categorical.csv`:

```sql
SELECT publication, tally, REPLACE(collection, '-', ' ') AS collection
FROM (
	SELECT p.publication, COUNT(p.article) AS tally, a.collection
	FROM paper.article_publications p
	INNER JOIN paper.articles a ON p.article=a.id
	GROUP BY 1,3
	ORDER BY 1,2 DESC
) AS biglist
WHERE publication IN (
	SELECT publication FROM (
		SELECT publication, COUNT(article) AS tally
		FROM paper.article_publications
		GROUP BY publication
		ORDER BY tally DESC, publication
		LIMIT 30
	) AS ranks
)
```

```r
pubframe = read.csv('publications_per_journal_categorical.csv')
pubframe <- pubframe %>%
  inner_join(capitalized_journals, by=c("publication"="old"))  %>%
  mutate(publication = new) %>%
  select(publication, tally, collection)
pubframe <- pubframe %>%
  inner_join(capitalized_cats, by=c("collection"="old"))  %>%
  mutate(collection = new) %>%
  select(publication, tally, collection)

figure <- ggplot(pubframe, aes(x=publication, y=tally, fill=collection)) +
  geom_bar(stat="identity", color="white") +
  aes(x = reorder(publication, tally, sum), y = tally, label = tally, fill = collection) +
  scale_y_continuous(expand=c(0,0)) +
  coord_flip(ylim=c(0,850)) +
  labs(x = "Journal", y = "Preprints published") +
  theme_bw() +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    axis.title.x = element_text(size=big_fontsize),
    axis.title.y = element_text(size=big_fontsize, hjust=0.6),
    legend.position = "none",
    plot.margin = unit(c(0.2,1,0.5,0.2), "cm"),
  )

# The wide x-axis labels (the vertical axis, in this case) mess up the
# alignment of the legend, so it gets added separately
legendplot <- ggplot(pubframe, aes(x=publication, y=tally, fill=collection)) +
  geom_bar(stat="identity", color="white") +
  aes(x = reorder(publication, tally, sum), y = tally, label = tally, fill = collection) +
  coord_flip() +
  theme_bw() +
  theme(
    legend.text = element_text(size=big_fontsize),
    legend.title = element_text(size=big_fontsize),
    legend.margin = margin(b = 20, unit = "pt")
  ) +
  guides(fill=guide_legend(
    ncol = 3,
    title = "Collection"
  ))

plot_grid(figure, get_legend(legendplot),
  ncol = 1, nrow = 2,
  rel_heights = c(2,1)
)
```

## Figure 6: Median bioRxiv downloads per journal

Query written to `downloads_journal.csv`:

```sql
SELECT d.article, d.downloads, p.publication AS journal
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

Panel:

```r
journalframe = read.csv('downloads_journal.csv')
journalframe <- journalframe %>%
  inner_join(capitalized_journals, by=c("journal"="old"))  %>%
  mutate(journal = new) %>%
  select(article, downloads, journal)

impactframe = read.csv('impact_scores.csv')
details <- journalframe %>% left_join(impactframe)

main <- ggplot(data=details, aes(
    x=reorder(journal, downloads, FUN=median),
    y=downloads,
    fill=Access
  )) +
  geom_boxplot(
    outlier.shape = NA, coef=0
  ) +
  theme_bw() +
  coord_flip(ylim=c(0, 3650)) +
  scale_y_continuous(breaks=seq(0, 3500, 500), expand=c(0,0), labels=comma) +
  labs(x="Journal", y="Downloads per preprint") +
  theme(
    axis.title = element_text(size=big_fontsize),
    axis.text= element_text(size=big_fontsize, color = themedarktext),
    legend.text = element_text(size=big_fontsize),
    legend.title = element_text(size=big_fontsize),
    legend.position = "top"
  )
```

### Figure 6 inset: Impact factor vs. median downloads

Query written to `publications_per_journal.csv`:

```sql
SELECT REPLACE(publication, ',', '') AS journal, COUNT(article) AS Papers
FROM paper.article_publications
GROUP BY 1
ORDER BY 2 DESC, 1
```

Panel:

```r
journalonlyframe = filter(journalframe, journal!='(unpublished)')
totals = read.csv('publications_per_journal.csv')
totals <- totals %>%
  inner_join(capitalized_journals, by=c("journal"="old"))  %>%
  mutate(journal = new) %>%
  select(journal, Papers)

medians <- journalonlyframe %>%
  group_by(journal) %>%
  summarize(median = median(downloads))

all <- medians %>% left_join(impactframe)
all <- all %>% left_join(totals)

# Find the regression results for the plot:
summary(lm(impact~median, data=all))

inset <- ggplot(data=all, aes(
    x=median,
    y=impact,
    label=journal,
    color=Access,
    size=Papers,
    alpha=0.5
  )) +
  geom_point() +
  theme_bw() +
  scale_x_continuous(label=comma) +
  coord_cartesian(xlim=c(0,3000)) +
  theme(
    panel.border = element_rect(linetype = "solid", color="black", size=1, fill = NA),
    axis.text = element_text(size=big_fontsize, color = themedarktext),
    axis.title = element_text(size=big_fontsize),
    legend.position = c(0.85, 0.2)
  ) +
  labs(x="Median downloads per preprint", y="Journal impact score, 2017") +
  geom_text_repel(
    data=subset(all, journal %in% c(
      'Nature Genetics',
      'Nature Methods',
      'Genome Biology',
      'Nature Communications',
      'eLife',
      'Bioinformatics'
    )),
    # Separate aesthetic for the labels so they don't
    # scale with dot size:
    aes(median, impact,label=journal),
    size=4,
    max.iter = 5000,
    box.padding = unit(1.5, "lines"),
    point.padding = unit(0.4, "lines"),
    alpha=1
  ) +
  geom_abline(intercept=0.136331, slope=0.013725, color=themedarkgrey, size=1, alpha=0.35) +
  guides(
    color = "none",
    alpha = "none"
  )
```

### Figure 6 combined

```r
plot_grid(main) +
  draw_plot(inset, 0.48, 0.1, 0.51, 0.65)
```

## Table 2: Downloads of published and unpublished papers

Query written to `downloads_publication_status.csv`:
```sql
SELECT d.article, d.downloads, EXTRACT(year FROM a.posted) AS year,
	CASE WHEN COUNT(p.article) > 0 THEN TRUE
    	ELSE FALSE
    END AS published
FROM paper.alltime_ranks d
LEFT JOIN paper.article_publications p ON d.article=p.article
LEFT JOIN paper.articles a ON d.article=a.id
GROUP BY d.article, a.posted
ORDER BY published DESC, d.downloads DESC
```

Analysis and generation of numbers used in table:

```r
paperframe = read.csv('downloads_publication_status.csv')
library(car)
leveneTest(downloads~published, data=paperframe)
library(MASS)
wilcox.test(downloads~published, data=paperframe, alternative="less")

library(canprot)
CLES(filter(paperframe, published=='False')$downloads, filter(paperframe, published=='True')$downloads)

# pre-2018:
wilcox.test(downloads~published, data=filter(paperframe, year<2018), alternative="less")
CLES(filter(paperframe, published=='False', year<2018)$downloads, filter(paperframe, published=='True', year<2018)$downloads)

# Actual numbers for table:
median(filter(paperframe, published=='False', year<2018)$downloads)
median(filter(paperframe, published=='True', year<2018)$downloads)

median(filter(paperframe, published=='False')$downloads)
median(filter(paperframe, published=='True')$downloads)
```


## Figure 2, supplement 1: Downloads over time relative to posting

Query written to `downloads_by_months.csv`:

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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'
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
WHERE a.posted < '2018-01-01'

/* Overall median: */
SELECT median(pdf)
FROM paper.article_traffic
```

Figure:

```r
firstframe = read.csv('downloads_by_months.csv')

ggplot(data=firstframe, aes(
    x=monthnum,
    y=downloads,
    group=monthnum
  )) +
  geom_boxplot(outlier.shape = NA, coef=0) +
  scale_y_continuous(breaks=seq(0, 150, 25)) +
  scale_x_continuous(breaks=seq(0, 12, 1)) +
  coord_cartesian(ylim=c(0,150)) +
  theme_bw() +
  labs(x="Months on bioRxiv", y="Downloads in month") +
  theme(
    legend.position="none",
    axis.title = element_text(size=big_fontsize),
    axis.text = element_text(size=big_fontsize, color=themedarktext),
  ) +
  geom_hline(yintercept=21, col=themedarkgrey, linetype="dashed", size=1)
```

## Figure 2, supplement 2: Proportion of downloads per month on bioRxiv

```r
pre2018 <- filter(firstframe, posted < 2018)
sums <- ddply(pre2018, .(id), summarise, sum = sum(downloads))
combined <- pre2018 %>% left_join(sums)
combined$proportion <- with(combined, downloads/sum)

ggplot(data=combined, aes(
    x=monthnum,
    y=proportion,
    group=monthnum
  )) +
  geom_boxplot() +
  scale_x_continuous(breaks=seq(0, 12, 1)) +
  scale_y_continuous(breaks=seq(0, 1, 0.1)) +
  theme_bw() +
  labs(x="Months on bioRxiv", y="Proportion of downloads in month") +
  theme(
    legend.position="none",
    axis.title = element_text(size=big_fontsize),
    axis.text = element_text(size=big_fontsize, color=themedarktext),
  )
```

## Figure 2, supplement 3: Downloads by year posted

### Figure 2.3a: Downloads in first month on bioRxiv

Query written to `downloads_by_first_month.csv`:

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

Panel:

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

### Figure 2.3b: Best month of downloads

Query written to `downloads_max_by_year_posted.csv`:

```sql
SELECT t.article AS id, EXTRACT(year FROM a.posted) AS year, MAX(t.pdf) AS downloads
FROM paper.article_traffic t
LEFT JOIN paper.articles a ON t.article=a.id
GROUP BY 1,2
ORDER BY 3 desc
```

Panel:

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

### Figure 2.3(c): 2018 downloads, by year posted

Query written to `2018_downloads_by_year_posted.csv`:

```sql
SELECT a.id, EXTRACT(year FROM a.posted) AS year, SUM(t.pdf) AS downloads
FROM paper.articles a
LEFT JOIN paper.article_traffic t ON a.id=t.article
WHERE t.year=2018
GROUP BY a.id
ORDER BY downloads DESC
```

Panel:

```r
latestframe = read.csv('2018_downloads_by_year_posted.csv')

latestplot <- ggplot(data=latestframe, aes(
    x=year,
    y=downloads,
    group=year
  )) +
  geom_boxplot(outlier.shape = NA, coef=0) +
  scale_x_continuous(breaks=seq(2013, 2018, 1)) +
  scale_y_continuous(breaks=seq(0, 325, 50)) +
  coord_cartesian(ylim=c(0,325)) +
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

### Figure 2, supplement 3 combined

```r
plot_grid(firstplot, maxplot, latestplot,
  labels=c("(a)", "(b)", "(c)"),
  hjust=0,
  ncol = 1, nrow = 3,
  align = "v"
)
```

## Figure 2, supplement 4: Median downloads per year

Query written to `downloads_per_year.csv`:

```sql
SELECT d.article, d.downloads, EXTRACT(YEAR FROM a.posted) AS year
FROM paper.alltime_ranks d
INNER JOIN paper.articles a ON d.article=a.id;
```

Figure:

```r
aframe = read.csv('downloads_per_year.csv')
mediandownloads <- aggregate(downloads~year,data=aframe,median)

# Stacked density plot:
ggplot(data=aframe, aes(
    x=downloads, group=year, fill=year
  )) +
  geom_density() +
  scale_x_continuous(trans="log10", labels=comma) +
  scale_y_continuous(breaks=seq(0.5, 1.5, 0.5)) +
  coord_cartesian(xlim=c(8,30000)) +
  theme_bw() +
  labs(x="Total downloads", y="Probability density") +
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
```

## Table S1: Articles per journal, September 2018

Tables of contents:

* [*Cell* 174(6)](https://www.sciencedirect.com/journal/cell/vol/174/issue/6), 6 Sep 2018
* [*Cell* 175(1)](https://www.sciencedirect.com/journal/cell/vol/175/issue/1), 20 Sep 2018
* [*Genetics* 210(1)](http://www.genetics.org/content/210/1), September 2018
* [*The Journal of Biochemistry* 164(3)](https://academic.oup.com/jb/issue/164/3), September 2018
* [*PLOS Biology* 16(9)](https://journals.plos.org/plosbiology/issue?id=10.1371/issue.pbio.v16.i09), September 2018

## Table S2: Papers per author

Query written to `papers_per_author.csv`:

```sql
SELECT a.id, REPLACE(a.name, ',', ' ') AS name, COUNT(DISTINCT p.article) AS papers, COUNT(DISTINCT e.email) AS emails
FROM paper.authors a
INNER JOIN paper.article_authors p
  ON a.id=p.author
LEFT JOIN paper.author_emails e
  ON a.id=e.author
GROUP BY 1
ORDER BY 3 DESC
```

(Top values inserted into table.)

## Table S3: Authors and papers by institution

Query written to `authors_per_institution.csv`:

```sql
SELECT authors.institution, authors.authors, p.papers
FROM (
  SELECT REPLACE(a.institution, ',', '') AS institution, COUNT(a.id) AS authors
  FROM paper.authors a
  WHERE institution NOT IN ('', '-')
  GROUP BY 1
) AS authors
LEFT JOIN (
  SELECT REPLACE(a.institution, ',', '') AS institution, COUNT(DISTINCT p.article) AS papers
  FROM paper.authors a
  INNER JOIN paper.article_authors p
    ON a.id=p.author
  GROUP BY 1
) AS p ON authors.institution=p.institution
ORDER BY 3 DESC, 2 DESC, 1
```

(Top values added to table.)

## Analysis

Total papers: `SELECT COUNT(id) FROM paper.articles`
Total papers in 2018: `SELECT COUNT(id) FROM paper.articles WHERE posted > '2017-12-31'`
Total papers before 2018: `SELECT COUNT(id) FROM paper.articles WHERE posted < '2018-01-01'`

Total neuroscience papers: `SELECT COUNT(id) FROM paper.articles WHERE collection='neuroscience'`

Total papers posted in October 2018: `SELECT COUNT(id) FROM paper.articles WHERE posted >= '2018-10-01' AND posted <= '2018-10-31'`

Comparing neuroscience papers to non-neuroscience:
```r
paperframe = read.csv('downloads_per_category.csv')
paperframe$isneuro <- ifelse(paperframe$collection =='neuroscience',TRUE, FALSE)
ddply(paperframe, .(isneuro), summarise, med = median(downloads))
wilcox.test(downloads~isneuro, data=paperframe)
```

Info from Figure 2, supplement 1:
```r
firstframe = read.csv('downloads_by_months.csv')
median(filter(firstframe, monthnum==1)$downloads)
```

Biggest "debut" month:
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
WHERE a.posted < '2017-12-01'
ORDER BY downloads DESC
LIMIT 1
```

Total authors: `SELECT COUNT(id) FROM paper.authors`


```sql
SELECT publication, COUNT(DISTINCT collection)
FROM (
	SELECT p.publication, a.collection
	FROM paper.article_publications p
	INNER JOIN paper.articles a ON p.article=a.id
) AS biglist
GROUP BY 1
ORDER BY 2 DESC
```

Papers by top 10 percent of authors:
```sql
SELECT COUNT(DISTINCT article)
FROM paper.article_authors
WHERE author IN (
	SELECT id
	FROM (
		SELECT a.id, COUNT(DISTINCT p.article) AS papers
		FROM paper.authors a
		INNER JOIN paper.article_authors p
		  ON a.id=p.author
		GROUP BY a.id
		ORDER BY papers DESC
		LIMIT (SELECT COUNT(id) FROM paper.authors) * 0.10
	) as topauthors
)
```
