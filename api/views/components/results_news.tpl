<div class="row">
  <div class="col-sm-2">&nbsp;</div>
  % include("components/results_news_lede", result=results[0], width=8)
</div>
<div class="row">
  % include("components/results_news_lede", result=results[1], width=6)
  % include("components/results_news_lede", result=results[2], width=6)
</div>
<div class="accordion" id="alltime">
  % for i, result in enumerate(results):
    % if i < 3: continue # skip the ones we gave special attention
    % end
    <div class="card">
      <div class="card-header context" id="heading{{result.id}}"  data-toggle="collapse" data-target="#collapse{{result.id}}" aria-expanded="true" aria-controls="collapse{{result.id}}">
        <strong>{{i+1}}:</strong> {{result.title}}
        <br>
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
      </div>
      <div id="collapse{{result.id}}" class="collapse" aria-labelledby="heading{{result.id}}" data-parent="#alltime">
        <div class="card-body">
          <div class="float-right">
            <a href="/papers/{{result.id}}" class="btn btn-altcolor " role="button">more details</a>
            <a href="{{result.url}}" target="_blank" class="btn btn-altcolor " role="button">view paper</a>
          </div>
          <p>
          % for i, author in enumerate(result.authors):
            <a href="/authors/{{author.id}}">{{ author.full }}</a>{{", " if i < (len(result.authors) - 1) else ""}}
          % end

          <p>{{result.abstract}}
        </div>
      </div>
    </div>
  % end
</div>