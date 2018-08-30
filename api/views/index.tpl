% import helpers
<!doctype html>
<html lang="en" ng-app="app">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist: Popular biology pre-print papers ranked</title>
  </head>
  <body>
    <div class="container" id="main">

      %include("components/header", stats=stats)

      <div class="row">
        <div class="col">
          % if view == "news":  # hide the search if we're doing snazzy news display
            <p>
              <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#searchform" aria-expanded="false" aria-controls="searchform">
                Search form
              </button>
            </p>
            <div class="collapse" id="searchform">
          % end
 
          %include("components/searchform", category_list=category_list, view=view, query=query)
          % if view == "news":
            </div>
          % end

          <div class="alert alert-danger" role="alert" style="display: {{"none" if error == "" else "block"}}">
            {{error}}
          </div>
          %if len(results) == 0:
            <div><h3>No results found for "{{ query.replace("&", " ") }}"</h3></div>
            % if metric == "altmetric":
            %  # just adding a new "metric" param at the end of the query string overrides
            %  # any that appear earlier in the query, once bottle gets it
              <div><p>Search was based on articles with Altmetric data&mdash;redo search <a href="/?{{querystring}}&metric=downloads">with download data</a> instead?</p></div>
            % end
          %else:
            % if view == "news":
              <p><em>{{ title }}.</em>
            % else:
              <h2>{{title}}</h2>
            % end
          %end
          %if len(category_filter) > 0:
            <h4 style="padding-left: 20px;">in categor{{ "ies:" if len(category_filter) > 1 else "y" }}
              % for i, cat in enumerate(category_filter):
                {{ helpers.formatCategory(cat) }}{{", " if i < (len(category_filter)-1) else ""}}
              %end
            </h4>
          %end

          % if metric == "altmetric":
            <em>Note: Currently, the only timeframe available for Altmetric searches is "last 24 hours."</em></p>
          % end
          % if len(results) > 0:
            % if view == "table":
              <h3>burps</h3>
              % include("components/results_table", results=results)
            % elif view == "news":
              % include("components/results_news", results=results)
            % else:
              % include("components/results_standard", results=results)
            % end
          % end
        </div>
      </div>
    </div>

    %include("components/footer")
    %include("components/about_modal")

    <script>
      $(function () {
        $('[data-toggle="tooltip"]').tooltip()
      })
    </script>
  </body>
</html>