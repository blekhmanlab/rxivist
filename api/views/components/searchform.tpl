% if entity == "papers":
  <script>
    function fixForm(changed) {
      metricField = document.getElementById("metric");
      metricOptions = metricField.getElementsByTagName("option");
      metric = metricField.options[metricField.selectedIndex].value;

      timeField = document.getElementById("timeframe");
      timeOptions = timeField.getElementsByTagName("option");
      timeframe = timeField.options[timeField.selectedIndex].value;

      searchField = document.getElementById("basicsearchtext");

      switch(changed) {
        case "metric":
          if(metric == "crossref") {
            timeField.disabled = true;
            timeField.selectedIndex = 3; // daily
          } else { // downloads
            timeField.disabled = false;
            if(timeField.selectedIndex == 3) { // daily
              timeField.selectedIndex = 0;
            }
            timeOptions[0].disabled = false; // all time
            timeOptions[1].disabled = false; // year to date
            timeOptions[2].disabled = false; // last month
            timeOptions[3].disabled = true; // 24 hours
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
        >Tweet count</option>
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
      <select class="form-control  col-sm-3" id="timeframe" name="timeframe" onchange="fixForm('timeframe');"
        %if metric != "downloads":
          disabled
        %end
      >
        <option value="alltime"
        %if timeframe == "alltime":
          selected
        %end
        %if metric != "downloads":
          disabled
        %end
        >all time</option>
        <option value="ytd"
        %if timeframe == "ytd":
          selected
        %end
        %if metric != "downloads":
          disabled
        %end
        >year to date</option>

        <option value="lastmonth"
        %if timeframe == "lastmonth":
          selected
        %end
        %if metric != "downloads":
          disabled
        %end
        >since last month</option>

        <option value="daily"
        %if timeframe == "daily":
          selected
        %end
        %if metric != "crossref":
          disabled
        %end
        >last 24 hours</option>
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
