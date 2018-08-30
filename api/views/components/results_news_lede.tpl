<div class="col-md-{{width}}">
  <h3>{{result.title}}</h3>
  <div>
    <p><em>
      % if len(result.authors) > 1:
        {{ result.authors[0].full }}, {{ result.authors[1].full }}
      % end
      % if len(result.authors) > 2:
        , et al.
      % end
    </em></p>
    <span class="badge badge-secondary" style="margin-left: 10px;">
      % if metric == "downloads":
        {{ helpers.formatNumber(result.downloads) }} downloads
      % elif metric == "altmetric":
        Score today: {{ helpers.formatNumber(result.downloads) }}
      % end
    </span>
    % if len(category_filter) != 1:
      <span class="badge badge-secondary" style="margin-left: 10px;">{{ helpers.formatCategory(result.collection) }}</span>
    % end
    % if result.date.month is not None:
      <span class="badge badge-secondary" style="margin-left: 10px;">{{result.date.monthname}} {{result.date.year}}</span>
    % end
    <p>{{ (result.abstract[:525] + "...") if len(result.abstract) > 525 else result.abstract }}
    <p><a href="/papers/{{result.id}}" class="btn btn-altcolor " role="button">more details</a>
        <a href="{{result.url}}" target="_blank" class="btn btn-altcolor " role="button">view paper</a>
  </div>
</div>