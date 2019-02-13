# Rxivist database snapshots

The backup file in this repository is a copy of the production database powering [Rxivist.org](https://rxivist.org), a website that helps readers find interesting preprints by using download and Twitter metrics to sort papers posted to [bioRxiv.org](https://www.biorxiv.org).

## PostgreSQL snapshot restoration

### Using the pre-built Docker container

Beginning with the 2019-02-13 snapshot, all database dumps here should have a corresponding container image hosted on [Docker Hub](https://cloud.docker.com/u/blekhmanlab/repository/docker/blekhmanlab/rxivist_data). If you are unfamiliar with SQL databases, using the most recent image there is likely simpler than loading the data manually from this repository.

1. Download the `docker-compose.yml` file from this repository. You don't need the snapshot itself if you are using the pre-built Docker container; the data is already baked in.
1. Install [Docker](https://www.docker.com/products/docker-desktop), a free containerization platform. Containers are used for all the Rxivist components to limit external dependencies and side-effects from installation of tools such as PostgreSQL.
1. Start the Docker daemon.
1. Open a command terminal and navigate to the directory in which you've stored `docker-compose.yml`. Run the command `docker-compose up`
1. In your browser, navigate to `http://localhost:8080`; this should show you the login screen for pgAdmin, a web application for interacting with SQL databases. (Both this web app and the database are only accessible from your computer.) The username and password are both `postgres`.
1. Once you are logged in, look in the the left-hand toolbar; right-click on "Servers," and select "Create Server." Give this connection a name, then, in the "Connection" tab of the "Create - Server" dialog, enter `rxdb` in the field for "Host name/address." All other fields should be correct. Click "Save."
1. The new server connections should now appear in the "Servers" tree in the left sidebar. Open this, and select the `postgres` database from under the `Databases` category. Right-clicking on the `postgres` database and selecting the "Query Tool..." option will open a window with which you can submit queries to the database. For examples, see below.

### Loading the database backup manually

If you want to load the snapshot directly, rather than trusting the contents of the `rxivist_data` container image, any conventional method of restoring Postgres backups should work properly for these snapshots. The instructions below are for launching a Postgres server on a local workstation and importing the data.

1. Download the database snapshot from this repository. It's the file called `rxivist.backup`.
1. Install [Docker](https://www.docker.com/products/docker-desktop), a free containerization platform. Containers are used for all the Rxivist components to limit external dependencies and side-effects from installation of tools such as PostgreSQL.
1. Start the Docker daemon.
1. Open a command terminal and start a PostgreSQL server as a background process: `docker run --name rxdb -e POSTGRES_PASSWORD=asdf -d -p 127.0.0.1:5432:5432 postgres` This should result in a database server being available on your workstation at `localhost:5432`, the standard Postgres port.
1. While you can use the `psql` tool to interact with the database from within the container, those unfamiliar with SQL databases may have an easier time using [pgAdmin 4](https://www.pgadmin.org/download/), a free tool that adds a browser-based interface with which to run commands. Instead of installing the software on your computer, you can launch it in a container by going to your command line and running `docker run -p 8080:80 -e "PGADMIN_DEFAULT_EMAIL=postgres" -e "PGADMIN_DEFAULT_PASSWORD=postgres" -d dpage/pgadmin4`
1. In your browser, navigate to `http://localhost:8080`. The login page presented here is for the pgAdmin tool itself—_not_ the database. The username and password are both `postgres`.
1. On the left side, right-click on "Servers," and select "Create Server." Give this connection a name, then, in the "Connection" tab of the "Create - Server" dialog, enter the properties of the PostgreSQL database you created in step 4. "Host name/address" should be `localhost`; most other values can remain unchanged. For the "Password" field, enter whatever password you specified in the Docker command in step 4 (in the example, it's `asdf`.) Click "Save."
1. The new server connections should now appear in the "Servers" tree in the left sidebar. Open this, and select the `postgres` database from under the `Databases` category. Right-click on `postgres`, and select the "Restore..." option.
1. This should open the "Restore" dialog. For "Filename," click on the ellipsis on the right side of the box and find the `rxivist.backup` file that you downloaded in step 1.
1. Switch to the "Restore options" tab of this dialog box. Most of these values can remain unchanged, but three values need to be changed from "No" to "Yes": "Pre-data," "Data" and "Owner."
1. Click the blue "Restore" button.
1. Once this process is complete, your "postgres" database should have two schemas: "public," which doesn't have data in it, and "prod," which contains the data presented on Rxivist.org.

(For those looking to create a snapshot of their own, Snapshots are created using the "Backup" dialog with the "Yes" option selected for "Pre-data," "Data," "Blobs," "Owner," "Privilege," "With OID(s)" and "Verbose messages.")

## Example queries

These queries are based on ones used to [generate the figures](https://github.com/blekhmanlab/rxivist/blob/master/paper/figures.md) that appear in our preprint, [Tracking the popularity and outcomes of all bioRxiv preprints](https://www.biorxiv.org/content/10.1101/515643v1).

Total papers: `SELECT COUNT(id) FROM prod.articles`

Total neuroscience papers: `SELECT COUNT(id) FROM prod.articles WHERE collection='neuroscience'`

Total authors: `SELECT COUNT(id) FROM prod.authors`

Submissions per month:
```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS month,
	COUNT(id) AS submissions
FROM prod.articles
GROUP BY 1
ORDER BY 1;
```

Submissions per month, per category:
```sql
SELECT EXTRACT(YEAR FROM posted)||'-'||lpad(EXTRACT(MONTH FROM posted)::text, 2, '0') AS date,
	REPLACE(collection, '-', ' ') AS collection,
	COUNT(id) AS submissions
FROM prod.articles
GROUP BY 1,2
ORDER BY 1,2;
```

Downloads per month, per category:
```sql
SELECT article_traffic.year||'-'||lpad(article_traffic.month::text, 2, '0') AS date,
	SUM(article_traffic.pdf) AS month,
	REPLACE(articles.collection, '-', ' ') AS collection
FROM prod.article_traffic
LEFT JOIN prod.articles ON article_traffic.article=articles.id
GROUP BY 1,3
ORDER BY 1,3;
```

Downloads per month:
```sql
SELECT month, year, sum(pdf) AS downloads
FROM prod.article_traffic
GROUP BY year, month
ORDER BY year, month
```

Publication rate by month:
```sql
SELECT month, posted, published, published::decimal/posted AS rate
FROM (
  SELECT EXTRACT(YEAR FROM a.posted)||'-'||lpad(EXTRACT(MONTH FROM a.posted)::text, 2, '0') AS month,
	COUNT(a.id) AS posted,
  COUNT(p.doi) AS published
  FROM prod.articles a
  LEFT JOIN prod.article_publications p ON a.id=p.article
  GROUP BY month
  ORDER BY month
) AS counts
```


Interval between posting to bioRxiv and date of publication:
```sql
SELECT a.id, EXTRACT(YEAR FROM a.posted) AS year, REPLACE(a.collection, '-', ' ') AS collection,
	p.date AS published, (p.date-a.posted) AS interval
FROM prod.articles a
INNER JOIN prod.publication_dates p ON a.id=p.article
WHERE p.date > '1900-01-01' --- Dummy value used for unknown values
ORDER BY interval DESC
```

Downloads in first month on bioRxiv:

```sql
SELECT a.id, t.month, t.year, t.pdf AS downloads
FROM prod.articles a
LEFT JOIN prod.article_traffic t
  ON a.id=t.article
  AND t.year = (
    SELECT MIN(year)
    FROM prod.article_traffic t
    WHERE t.article = a.id
  )
  AND t.month = (
    SELECT MIN(month)
    FROM prod.article_traffic t
    WHERE a.id=t.article AND
      year = (
        SELECT MIN(year)
        FROM prod.article_traffic t
        WHERE t.article = a.id
      )
  )
ORDER BY id
```


Papers per author:
```sql
SELECT a.id, REPLACE(a.name, ',', ' ') AS name, COUNT(DISTINCT p.article) AS papers, COUNT(DISTINCT e.email) AS emails
FROM prod.authors a
INNER JOIN prod.article_authors p
  ON a.id=p.author
LEFT JOIN prod.author_emails e
  ON a.id=e.author
GROUP BY 1
ORDER BY 3 DESC
```

Preprints published within a week of posting:
```sql
SELECT COUNT(id)
FROM (
	SELECT a.id, EXTRACT(YEAR FROM a.posted) AS year, REPLACE(a.collection, '-', ' ') AS collection,
	p.date AS published, (p.date-a.posted) AS interval
	FROM prod.articles a
	INNER JOIN prod.publication_dates p ON a.id=p.article
	WHERE p.date > '1900-01-01' --- Dummy value used for unknown values
	ORDER BY interval DESC
) AS intervals
WHERE interval >=0 AND interval <= 7
```
