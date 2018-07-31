<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist details – {{paper.title}}</title>
  </head>

  <body>
  <br>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col">
          <h1>{{paper.title}}</h1>
          <div>
            <a href="/?category={{paper.collection}}" class="btn btn-secondary " role="button">{{paper.collection}}</a>
            <a href="{{paper.url}}" target="_blank" class="btn btn-altcolor " role="button">view paper</a>
          </div>
          <p>By
          % for i, coauthor in enumerate(paper.authors):
            <a href="/authors/{{coauthor.id}}">{{coauthor.full}}</a>{{", " if i < (len(paper.authors) - 1) else ""}}
          % end
          <ul>
            <li>{{paper.downloads}} downloads
                    %if paper.date.monthname != "":
                      since {{paper.date.monthname}} {{paper.date.year}}
                    %end
            <li><strong>All-time download rankings:</strong>
              <ul>
                <li>Site-wide: <strong>{{paper.ranks.alltime.rank}}</strong> out of {{paper.ranks.alltime.out_of}}</li>
                <li>In {{paper.collection}}: <strong>{{paper.ranks.collection.rank}}</strong> out of {{paper.ranks.collection.out_of}}</li>
              </ul>
            </li>
            <li><strong>Year-to-date downloads rankings</strong>:
              <ul>
                <li>Site-wide: <strong>{{paper.ranks.ytd.rank}}</strong> out of {{paper.ranks.ytd.out_of}}</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </div>
    %include("components/footer")
  </body>
</html>