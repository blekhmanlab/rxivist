<p class="text-right"><em><strong>{{ "{:,}".format(totalcount) }} results found.</strong> For more information, click each entry to expand.</em></p>
<div class="accordion" id="alltime">
  % for i, result in enumerate(results):
    <div class="card">
      <div class="card-header context" id="heading{{result.id}}"  data-toggle="collapse" data-target="#collapse{{result.id}}" aria-expanded="true" aria-controls="collapse{{result.id}}">
        <strong>{{i+1 + (page * page_size)}}:</strong>
        % if metric == "crossref" and timeframe == "day" and result.downloads > 80:
          <i class="fab fa-hotjar text-danger" style="font-size: 2em;"></i>
        % end
        {{result.title}}

        <br>
          <strong>{{ helpers.formatNumber(result.downloads) }}</strong>
          % if metric == "downloads":
            <small>{{ "downloads" if result.downloads > 1 else "download" }}</small>
          % elif metric == "crossref":
            <small>{{ "tweets" if result.downloads > 1 else "tweet" }}</small>
          % end
        <span class="badge {{ result.collection.replace("-", "") }}" style="margin-left: 10px;">{{ helpers.formatCategory(result.collection) }}</span>
        <p class="text-right" style="margin-top: -1.5em; margin-bottom: 0;"><small>Posted to bioRxiv
          % if result.posted is not None:
            {{ result.posted.strftime('%-d %b %Y') }}
          % else:
            % if result.date.month is not None:
              {{result.date.monthname}} {{result.date.year}}
            % else:
              very recently
            % end
          % end
        </small></p>
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

%include("components/pagination")
