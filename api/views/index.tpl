% import helpers
<!doctype html>
<html lang="en" ng-app="app">
  <head>
    %include("components/metadata.tpl", google_tag=google_tag)
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

          %include("components/searchform")
          % if view == "news":
            </div>
          % end

          % if error != "":
            <div class="alert alert-danger" role="alert" style="display: {{"none" if error == "" else "block"}}">
              {{error}}
            </div>
          % else:
            %if len(results) == 0:
              <div><h3>No results found for "{{ query.replace("&", " ") }}"</h3></div>
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
            % if len(results) == 0 and metric == "twitter":
            %  # just adding a new "metric" param at the end of the query string overrides
            %  # any that appear earlier in the query, once bottle gets it
              <div><p>Search was based on articles with Twitter activity data&mdash;redo search <a href="/?{{querystring}}&timeframe=alltime&metric=downloads">with download data</a> instead?</p></div>
            % end

            % if len(results) > 0:
              % if entity == "authors":
                  % include("components/author_ranks", results=results)
              % elif entity == "papers":
                % if view == "table":
                  % include("components/results_table", results=results)
                % elif view == "news":
                  % include("components/results_news", results=results)
                % else:
                  % include("components/results_standard", results=results)
                % end
              % end
            % end
          % end  # end of conditional for "display this if there's no error"
        </div>
      </div>
    </div>

    %include("components/footer")

    <script>
      $(function () {
        $('[data-toggle="tooltip"]').tooltip()
      })
    </script>
  </body>
</html>