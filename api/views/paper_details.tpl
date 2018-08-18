<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist details – {{paper.title}}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.4.0/Chart.min.js"></script>
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

          %include("components/paper_stats", paper=paper)

          <div class="row">
            <div class="col-md-6">
              <canvas id="myChart"></canvas>
            </div>
          </div>
          %include("components/download_graph", paper=paper)

        </div>
      </div>
    </div>

    %include("components/footer")

  </body>
</html>