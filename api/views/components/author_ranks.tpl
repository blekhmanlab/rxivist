<div class="accordion" id="alltime">
  % for i, result in enumerate(results):
    <div class="card">
      <div class="card-header context" id="heading{{result.id}}"  data-toggle="collapse" data-target="#collapse{{result.id}}" aria-expanded="true" aria-controls="collapse{{result.id}}">
        <strong>{{ result.rank.rank }}{{ " (tie)" if result.rank.tie else "" }}:</strong>
        {{result.full}}

        <br>
        <span class="badge badge-secondary" style="margin-left: 10px;">
          {{ helpers.formatNumber(result.rank.downloads) }} downloads
        </span>
      </div>
      <div id="collapse{{result.id}}" class="collapse" aria-labelledby="heading{{result.id}}" data-parent="#alltime">
        <div class="card-body">
          <div class="float-right">
            <a href="/authors/{{result.id}}" class="btn btn-altcolor " role="button">more details</a>
          </div>
        </div>
      </div>
    </div>
  % end
</div>