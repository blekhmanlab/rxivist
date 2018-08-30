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
          <div id="searchform">
            <form action="/" method="get">
              <div class="input-group mb-3 col-sm-9">
                <input type="text" class="form-control form-control-lg" id="basicsearchtext" name="q" placeholder="Enter search terms here (optional)" value="{{ query.replace("&", " ") }}">
              </div>
              <div class="input-group mb-3 col-md-9">
                <select class="form-control  col-sm-4" id="metric" name="metric">
                  <option value="downloads"
                  %if metric == "downloads":
                    selected
                  %end
                  >downloads</option>
                  <option value="altmetric"
                  %if metric == "altmetric":
                    selected
                  %end
                  >Altmetric score</option>
                </select>
                <select class="form-control col-sm-4" id="category" name="category">
                  <option value="">all categories</option>
                  % for cat in category_list:
                    <option value="{{cat}}"
                    % if cat in category_filter:
                      selected
                    % end
                    >{{ helpers.formatCategory(cat) }}</option>
                  %end
                </select>
                <select class="form-control  col-sm-4" id="timeframe" name="timeframe">
                  <option value="alltime"
                  %if timeframe == "alltime":
                    selected
                  %end
                  >all time</option>
                  <option value="ytd"
                  %if timeframe == "ytd":
                    selected
                  %end
                  >year to date</option>

                  <option value="lastmonth"
                  %if timeframe == "lastmonth":
                    selected
                  %end
                  >since last month</option>

                  <option value="weighted"
                  %if timeframe == "weighted":
                    selected
                  %end
                  >time-weighted score</option>
                </select>
                <input type="hidden" name="view" value="{{ view }}"></input>
                <div class="input-group-append">
                  <button type="submit" class="btn btn-altcolor">Search</button>
                </div>
              </div>
            </form>
          </div>

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