<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>{{author.full}} author profile – Rxivist</title>
  </head>

  <body>
  <br>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col">
          <h1>Author: {{author.full}}</h1>
          <div>
            <ul>
              <li>All-time downloads: {{author.downloads}} (rank: <strong>{{author.rank.rank}}</strong> out of {{author.rank.out_of}})
            </ul>
          </div>
          <h2>Articles</h2>
          <ul>
            % for result in author.articles:
              <h2 style="font-size: 1.2em; padding-top: 20px; margin-bottom: 0;">{{result.title}}</h2>
              <a href="/?category={{result.collection}}"><span class="badge badge-secondary" style="margin-left: 10px;">{{result.collection}}</span></a>
              <ul>
                <div class="float-right">
                  <a href="/papers/{{result.id}}" class="btn btn-altcolor " role="button">more details</a>
                  <a href="{{result.url}}" target="_blank" class="btn btn-altcolor " role="button">view paper</a>
                </div>
                <li>
                  % for i, coauthor in enumerate(result.authors):
                    <a href="/authors/{{coauthor.id}}">{{coauthor.full}}</a>{{", " if i < (len(result.authors) - 1) else ""}}
                  % end
                </li>
                <li><strong>All-time download rankings:</strong>
                  <ul>
                    <li>Site-wide: <strong>{{result.ranks.alltime.rank}}</strong> out of {{result.ranks.alltime.out_of}}</li>
                    <li>In {{result.collection}}: <strong>{{result.ranks.collection.rank}}</strong> out of {{result.ranks.collection.out_of}}</li>
                  </ul>
                </li>
                <li><strong>Year-to-date downloads rankings</strong>:
                  <ul>
                    <li>Site-wide: <strong>{{result.ranks.ytd.rank}}</strong> out of {{result.ranks.ytd.out_of}}</li>
                  </ul>
                </li>
              </ul>
            % end
          </div>
        </div>
      </div>
    </div>
    %include("components/footer")
  </body>
</html>