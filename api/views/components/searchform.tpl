<script>
function fixForm(changed) {
  entityField = document.getElementById("entity");
  metricField = document.getElementById("metric");
  timeField = document.getElementById("timeframe");
  searchField = document.getElementById("basicsearchtext");
  entity = entityField.options[entityField.selectedIndex].value;
  metric = metricField.options[metricField.selectedIndex].value;
  timeframe = timeField.options[timeField.selectedIndex].value;

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
        metricField.disabled = false;
        searchField.disabled = false;
      }
      break;
    case "metric":
      if(metric == "altmetric") {
        timeField.disabled = true;
        timeField.selectedIndex = 0; // all time
      } else {
        timeField.disabled = false;
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
      <select class="form-control  col-sm-4" id="metric" name="metric" onchange="fixForm('metric');">
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
      <select class="form-control  col-sm-4" id="timeframe" name="timeframe" onchange="fixForm('timeframe');">
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