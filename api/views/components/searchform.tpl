<script>
function fixForm(changed) {
  entityField = document.getElementById("entity");
  entity = entityField.options[entityField.selectedIndex].value;

  metricField = document.getElementById("metric");
  metricOptions = metricField.getElementsByTagName("option");
  metric = metricField.options[metricField.selectedIndex].value;

  timeField = document.getElementById("timeframe");
  timeOptions = timeField.getElementsByTagName("option");
  timeframe = timeField.options[timeField.selectedIndex].value;

  searchField = document.getElementById("basicsearchtext");

  switch(changed) {
    case "entity":
      if(entity == "authors") {
        timeField.disabled = true;
        timeField.selectedIndex = 0; // downloads
        metricField.disabled = true;
        metricField.selectedIndex = 0; // all time
        searchField.disabled = true;
      } else { // papers
        timeField.disabled = false;
        timeOptions[0].disabled = false; // all time
        timeOptions[1].disabled = false; // year to date
        timeOptions[2].disabled = false; // last month
        timeOptions[3].disabled = true; // 24 hours
        timeOptions[4].disabled = false; // time-weighted score

        metricField.disabled = false;
        searchField.disabled = false;
      }
      break;
    case "metric":
      if(metric == "altmetric") {
        timeField.disabled = true;
        timeField.selectedIndex = 3; // daily
      } else {
        timeField.disabled = false;
        if(timeField.selectedIndex == 3) { // daily
          timeField.selectedIndex = 0;
        }
        timeOptions[0].disabled = false; // all time
        timeOptions[1].disabled = false; // year to date
        timeOptions[2].disabled = false; // last month
        timeOptions[3].disabled = true; // 24 hours
        timeOptions[4].disabled = false; // time-weighted score
      }
      break;
  }
}
</script>

<div id="searchform">
  <form action="/" method="get">
    <div class="input-group mb-3 col-sm-9">
      <input type="text" class="form-control form-control-lg" id="basicsearchtext" name="q" placeholder="Enter search terms here (optional)" value="{{ query.replace("&", " ") }}">
    </div>
    <div class="input-group mb-3 col-md-9">
     <select class="form-control  col-sm-4" id="entity" name="entity" onchange="fixForm('entity');">
        <option value="papers"
        %if entity == "papers":
          selected
        %end
        >papers</option>
        <option value="authors"
        %if entity == "authors":
          selected
        %end
        >authors</option>
      </select>
      <select class="form-control  col-sm-4" id="metric" name="metric" onchange="fixForm('metric');"
        % if entity == "authors":
          disabled
        % end
      >
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
      <select class="form-control  col-sm-4" id="timeframe" name="timeframe" onchange="fixForm('timeframe');"
        % if entity == "authors":
          disabled
        % end
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
        %if metric != "altmetric":
          disabled
        %end
        >last 24 hours</option>

        <option value="weighted"
        %if timeframe == "weighted":
          selected
        %end
        %if metric != "downloads":
          disabled
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