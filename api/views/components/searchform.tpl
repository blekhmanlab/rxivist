% if entity == "papers":
  <script>
    function createOptions(template) {
      options = [];
      for (let x of template) {
        var option = document.createElement("option");
        option.text = x[0];
        option.value = x[1];
        options.push(option);
      }
      return options;
    }
    function fixForm(changed) {
      metricField = document.getElementById("metric");
      metric = metricField.options[metricField.selectedIndex].value;
      timeField = document.getElementById("timeframe");
      searchField = document.getElementById("basicsearchtext");

      crossref_options = createOptions([
        ["Since yesterday", "day"],
        ["Last 7 days", "week"],
        ["Last 30 days", "month"],
        ["Last 365 days", "year"],
        ["All time", "alltime"]
      ]);
      download_options = createOptions([
        ["Since last month", "lastmonth"],
        ["Year to date", "ytd"],
        ["All time", "alltime"]
      ]);

      switch(changed) {
        case "metric":
          // clear out old values:
          for(i = timeField.options.length - 1 ; i >= 0 ; i--) {
            timeField.remove(i);
          }
          if(metric == "crossref") {
            for (let x of crossref_options) {
              timeField.add(x);
            }
            switch("{{ timeframe }}") {
              case "day":
                timeField.selectedIndex = 0;
                break;
              case "week":
                timeField.selectedIndex = 1;
                break;
              case "month":
                timeField.selectedIndex = 2;
                break;
              case "year":
                timeField.selectedIndex = 3;
                break;
              case "alltime":
                timeField.selectedIndex = 4;
                break;
              default:
                timeField.selectedIndex = 4;
            }
          } else {
            // download metric is selected:
            for (let x of download_options) {
              timeField.add(x);
            }
            switch("{{ timeframe }}") {
              case "lastmonth":
                timeField.selectedIndex = 0;
                break;
              case "ytd":
                timeField.selectedIndex = 1;
                break;
              case "alltime":
                timeField.selectedIndex = 2;
                break;
              default:
                timeField.selectedIndex = 2;
            }
          }
          break;
      }
    }
    </script>
% end

<div id="searchform">
  <form action="/" method="get">
  % if entity == "papers":
    <div class="input-group mb-3 col-sm-9">
      <input type="text" class="form-control form-control-lg" id="basicsearchtext" name="q" placeholder="Enter search terms here (optional)" value="{{ query.replace("&", " ") }}">
      <a href="#" data-toggle="modal" data-target="#textsearch" style="margin-top: 10px;">
        <i class="far fa-question-circle" font-size: 1.5em;"></i>
      </a>
    </div>
    <div class="input-group mb-3 col-md-9">
      <select class="form-control  col-sm-3" id="metric" name="metric" onchange="fixForm('metric');">
        <option value="downloads"
        %if metric == "downloads":
          selected
        %end
        >downloads</option>
        <option value="crossref"
        %if metric == "crossref":
          selected
        %end
        >Twitter activity</option>
      </select>
      <select class="form-control col-sm-3" id="category" name="category">
        <option value="">all categories</option>
        % for cat in category_list:
          <option value="{{cat}}"
          % if cat in category_filter:
            selected
          % end
          >{{ helpers.formatCategory(cat) }}</option>
        %end
      </select>
      <select class="form-control  col-sm-3" id="timeframe" name="timeframe" onchange="fixForm('timeframe');">

      </select>
      <select class="form-control  col-sm-3" id="page_size" name="page_size">
        <option value="20"
          %if page_size == 20:
            selected
          %end
        >20 results per page</option>
        <option value="50"
          %if page_size == 50:
            selected
          %end
        >50 results per page</option>
        <option value="75"
          %if page_size == 75:
            selected
          %end
        >75 results per page</option>
        <option value="100"
          %if page_size == 100:
            selected
          %end
        >100 results per page</option>
      </select>
      <input type="hidden" name="view" value="{{ view }}"></input>
      <div class="input-group-append">
        <button type="submit" class="btn btn-altcolor">Search</button>
      </div>
    </div>

  % else:   # if it's a search form for authors, not papers
    <div class="input-group mb-3 col-md-9">
      <select class="form-control col-sm-4" id="category" name="category" onchange="this.form.submit()">
        <option value="">all categories</option>
        % for cat in category_list:
          <option value="{{cat}}"
          % if cat in category_filter:
            selected
          % end
          >{{ helpers.formatCategory(cat) }}</option>
        %end
      </select>
      <input type="hidden" name="view" value="{{ view }}"></input>
      <input type="hidden" name="entity" value="authors"></input>
      <div class="input-group-append">
        <button type="submit" class="btn btn-altcolor">Search</button>
      </div>
    </div>
  % end

  </form>
</div>

%include("components/modal_textsearch")

% if entity == "papers":
  <script>
    fixForm("metric");
  </script>
% end