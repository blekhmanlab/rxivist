<div class="accordion" id="alltime">
  % for i, result in enumerate(results):
    <div class="card">
      <div class="card-header context" id="heading{{result.id}}"  data-toggle="collapse" data-target="#collapse{{result.id}}" aria-expanded="true" aria-controls="collapse{{result.id}}">
        <strong>{{i+1 + (page * page_size)}}:</strong>
        % if metric == "altmetric" and result.downloads > 80:
          <i class="fab fa-hotjar text-danger" style="font-size: 2em;"></i>
        % end
        {{result.title}}

        <br>
        <span class="badge badge-secondary" style="margin-left: 10px;">
          % if metric == "downloads":
            {{ helpers.formatNumber(result.downloads) }} downloads
          % elif metric == "altmetric":
            Score today: {{ helpers.formatNumber(result.downloads) }}
          % end
        </span>
        % if len(category_filter) != 1:
          <span class="badge {{ result.collection.replace("-", "") }}" style="margin-left: 10px;">{{ helpers.formatCategory(result.collection) }}</span>
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
% if len(results) == page_size:
  <a href="{{ next_page_link }}" class="btn btn-altcolor">Next {{ page_size }}</a>
% end
