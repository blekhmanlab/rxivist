<div class="row">
  <div class="col-md-6">
    <ul>
      % current_list = 0
      % for i, result in enumerate(results):
        % print_download = True if (not result.rank.tie) or (result.rank.tie and (results[i-1].rank.rank != result.rank.rank)) or current_list == 0 else False
        <li><strong>{{ result.rank.rank }}{{ " (tie)" if result.rank.tie else "" }}:</strong>
          <a href="/authors/{{result.id}}">{{result.full}}</a>{{ "—"+helpers.formatNumber(result.rank.downloads)+" downloads" if print_download else "" }}
        </li>
        % current_list += 1
        % if current_list >= (len(results) / 2):
          %   current_list = 0
          </ul></div><div class="col-md-6"><ul>
        % end
      % end
    </ul>
  </div>
</div>
