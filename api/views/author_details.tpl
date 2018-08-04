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
              <li>All-time downloads: {{author.downloads}} (rank: <strong>{{author.rank.rank}}</strong>
              %if author.rank.tie:
                (tie)
              %end
              out of {{author.rank.out_of}})
            </ul>
          </div>
          <h2>Articles</h2>
          <ul>
            % for result in author.articles:
              <h2 style="font-size: 1.2em; padding-top: 20px; margin-bottom: 0;">{{result.title}}</h2>
              <a href="/?category={{result.collection}}"><span class="badge btn-secondary" style="margin-left: 10px;">{{result.collection}}</span></a>
              <a href="/papers/{{result.id}}"><span class="badge btn-altcolor">more details</span></a>
              <a href="{{result.url}}" target="_blank"><span class="badge btn-altcolor">view paper</span></a>
              <ul>
                <li>
                  %if len(result.authors) == 1:
                    No coauthors
                  %elif len(result.authors) == 2:
                    1 coauthor
                  %else:
                    {{ len(result.authors)-1 }} coauthors
                  %end
                </li>
                <li>{{result.downloads}} downloads
                  %if result.date.monthname != "":
                    since {{result.date.monthname}} {{result.date.year}}
                  %end
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
                <li><strong>Downloads rankings since beginning of last month</strong>:
                  <ul>
                    <li>Site-wide: <strong>{{result.ranks.lastmonth.rank}}</strong> out of {{result.ranks.lastmonth.out_of}}</li>
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