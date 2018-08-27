% import helpers
<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>{{author.full}} author profile – Rxivist</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.5.0/Chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/0.5.5/chartjs-plugin-annotation.js"></script>
    <script src="https://cdn.rawgit.com/chartjs/Chart.js/master/samples/utils.js"></script>
  </head>

  <body>
  <br>
    <div class="container" id="main">
      %include("components/header")

      <div class="row">
        <div class="col-sm-12">
          <h1>Author: {{author.full}}</h1>
          <ul>
            <li>All-time downloads: {{ helpers.formatNumber(author.downloads) }} (rank: <strong>{{ helpers.formatNumber(author.rank.rank) }}</strong>
            %if author.rank.tie:
              (tie)
            %end
            out of {{ helpers.formatNumber(author.rank.out_of) }})
          </ul>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          <h2>Articles</h2>
        </div>
        % for result in author.articles:
          <div class="col-md-6">
            <h2 style="font-size: 1.2em; padding-top: 20px; margin-bottom: 0;">{{result.title}}</h2>
            <a href="/?metric=downloads&category={{result.collection}}"><span class="badge btn-secondary" style="margin-left: 10px;">{{ helpers.formatCategory(result.collection) }}</span></a>
            <a href="/papers/{{result.id}}"><span class="badge btn-altcolor">more details</span></a>
            <a href="{{result.url}}" target="_blank"><span class="badge btn-altcolor">view paper</span></a>
            <ul>
              <li>
                %if len(result.authors) == 1:
                  No coauthors
                %elif len(result.authors) == 2:
                  1 coauthor
                %else:
                  {{ helpers.formatNumber(len(result.authors)-1) }} coauthors
                %end
              </li>
            </ul>

            %include("components/paper_stats", paper=result)
          </div>
        % end
      </div>
      <div class="row">
        <div class="col-md-8 offset-md-2">
          <h3>Downloads per author, site-wide</h3>
          <canvas id="downloadsDistribution"></canvas>
        </div>
        %include("components/download_distribution", entity=author, entity_name="author", download_distribution=download_distribution)
      </div>
    </div>
    %include("components/footer")

  </body>
</html>