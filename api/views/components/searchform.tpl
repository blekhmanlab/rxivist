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