<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Rxivist: Popular biology pre-print papers ranked</title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:700" rel="stylesheet">
    <link rel="stylesheet" href="/static/rxivist.css">
  </head>

  <body>
  <br>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col">
          <h1>Articles by {{author.full}}</h1>
          <ul>
            % for result in author.articles:
              <h2 style="font-size: 1.2em; padding-top: 20px; margin-bottom: 0;">{{result.title}}</h2>
              <a href="/?category={{result.collection}}"><span class="badge badge-secondary" style="margin-left: 10px;">{{result.collection}}</span></a>
              <ul>
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