<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist details – {{paper.title}}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.5.0/Chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-annotation/0.5.5/chartjs-plugin-annotation.js"></script>
    <script src="https://cdn.rawgit.com/chartjs/Chart.js/master/samples/utils.js"></script>
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
        </div>
      </div>
      <div class="row">
        <div class="col-md-6">
          <p>{{paper.abstract}}
        </div>
        <div class="col-md-6">
          %include("components/paper_stats", paper=paper)
        </div>
      </div>
      <div class="row">
        <div class="col-md-6">
          <h3>Downloads over time</h3>
          <canvas id="downloadsOverTime"></canvas>
        </div>
        % if paper.downloads is not None:
          <div class="col-md-6">
            <h3>Distribution of downloads per paper, site-wide</h3>
            <canvas id="downloadsDistribution"></canvas>
            <br>
            <canvas id="downloadsDistributionNoLog"></canvas>
          </div>
          %include("components/download_distribution", entity=paper,  entity_name="paper", download_distribution=download_distribution)
        % end
      </div>
      %include("components/download_graph", paper=paper)

    </div>

    %include("components/footer")

  </body>
</html>