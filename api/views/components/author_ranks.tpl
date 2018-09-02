<div class="accordion" id="alltime">
  <ul>
  % for i, result in enumerate(results):
    % print_download = True if (not result.rank.tie) or (result.rank.tie and (results[i-1].rank.rank != result.rank.rank)) else False
    <li><strong>{{ result.rank.rank }}{{ " (tie)" if result.rank.tie else "" }}:</strong>
      <a href="/authors/{{result.id}}">{{result.full}}</a>{{ "—"+helpers.formatNumber(result.rank.downloads)+" downloads" if print_download else "" }}
    </li>
  % end
  </ul>
</div>