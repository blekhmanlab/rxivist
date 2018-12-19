Check if all papers have a collection (or are too old to deal with)
```sql
SELECT * FROM prod.articles WHERE collection IS NULL;
```

Check the papers that don't have "posted on" dates
```sql
SELECT * FROM prod.articles
WHERE posted IS NULL
```

Make sure all the authors associated with papers are real
```sql
SELECT p.id, a.name
FROM prod.article_authors p
LEFT JOIN prod.authors a ON p.author=a.id
WHERE name IS NULL
```

Check if there are any authors that don't have ANY papers, somehow
(Maybe caused by them being on a paper, then removed from the author list in a future revision?)
```sql
DELETE FROM prod.authors
WHERE id IN (
	SELECT id
	FROM (
		SELECT a.id, COUNT(DISTINCT p.article) AS papers
		FROM prod.authors a
		LEFT JOIN prod.article_authors p
		  ON a.id=p.author
		GROUP BY a.id
		ORDER BY papers DESC
	) as topauthors
	WHERE papers=0
)
```

Make sure all email addresses are associated with actual authors
```sql
DELETE FROM prod.author_emails
WHERE author IN (
	SELECT e.author
	FROM prod.author_emails e
	LEFT JOIN prod.authors a ON e.author=a.id
	WHERE a.name IS NULL
)
```

Make sure all articles have at least one author
```sql
SELECT COUNT(id)
FROM (
	SELECT a.id, a.title, COUNT(w.author) AS authors
	FROM prod.articles a
	LEFT JOIN prod.article_authors w ON a.id=w.article
	GROUP BY 1,2
) AS authorcount
WHERE authors=0
```



Cloning function:
```sql
CREATE OR REPLACE FUNCTION clone_schema(source_schema text, dest_schema text) RETURNS void AS
$BODY$
DECLARE
  objeto text;
  buffer text;
BEGIN
    EXECUTE 'CREATE SCHEMA ' || dest_schema ;

    FOR objeto IN
        SELECT TABLE_NAME::text FROM information_schema.TABLES WHERE table_schema = source_schema
    LOOP
        buffer := dest_schema || '.' || objeto;
        EXECUTE 'CREATE TABLE ' || buffer || ' (LIKE ' || source_schema || '.' || objeto || ' INCLUDING CONSTRAINTS INCLUDING INDEXES INCLUDING DEFAULTS)';
        EXECUTE 'INSERT INTO ' || buffer || '(SELECT * FROM ' || source_schema || '.' || objeto || ')';
    END LOOP;

END;
$BODY$
LANGUAGE plpgsql VOLATILE;
```

Clean out old data
```sql
DROP SCHEMA paper CASCADE
```

Copy the schema
```sql
SELECT clone_schema('prod','paper');
```

Remove author associations from new papers
```sql
DELETE FROM paper.article_authors WHERE article IN (
	SELECT id FROM paper.articles
  WHERE posted >= '2018-12-01'
  OR collection IS NULL
)
```

Remove new papers
```sql
DELETE FROM paper.articles
WHERE posted > '2018-11-30'
OR collection IS NULL;
```

Delete emails of authors about to be removed
```sql
DELETE FROM paper.author_emails
WHERE author IN (
  SELECT id
  FROM (
    SELECT a.id, COUNT(p.article) AS papers
    FROM paper.authors a
    LEFT JOIN paper.article_authors p ON a.id=p.author
    GROUP BY 1
  ) AS papercount
  WHERE papers=0
)
```

Delete new authors
```sql
DELETE FROM paper.authors
WHERE id IN (
  SELECT id
  FROM (
    SELECT a.id, COUNT(p.article) AS papers
    FROM paper.authors a
    LEFT JOIN paper.article_authors p ON a.id=p.author
    GROUP BY 1
  ) AS papercount
  WHERE papers=0
)
```

Remove new download stats
```sql
DELETE FROM paper.article_traffic WHERE year=2018 AND month>11
```

Delete traffic stats for papers we deleted
(Should only apply at this point to traffic stats for papers that didn't have categories)
```sql
DELETE FROM paper.article_traffic
WHERE id IN (
  SELECT t.id
  FROM paper.article_traffic t
  LEFT JOIN paper.articles a ON t.article=a.id
  WHERE a.collection IS NULL
)
```

Delete publication data for papers we deleted
```sql
DELETE FROM paper.article_publications
WHERE id IN (
  SELECT p.article
  FROM paper.article_publications p
  LEFT JOIN paper.articles a ON p.article=a.id
  WHERE a.title IS NULL
)
```
