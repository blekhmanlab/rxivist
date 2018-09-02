% import helpers

% if paper.downloads is None:
<p><em>No bioRxiv download data for this paper yet.</em></p>
% else:

{{ helpers.formatNumber(paper.downloads) }} downloads
  %if paper.date.monthname != "":
    since {{paper.date.monthname}} {{paper.date.year}}
  %end

<ul>
  <li><strong>Download rankings, all-time:</strong>
    <ul>
      <li>Site-wide: <strong>{{ helpers.formatNumber(paper.ranks.alltime.rank) }}</strong> out of {{ helpers.formatNumber(paper.ranks.alltime.out_of) }}</li>
      <li>In {{ helpers.formatCategory(paper.collection) }}: <strong>{{ helpers.formatNumber(paper.ranks.collection.rank) }}</strong> out of {{ helpers.formatNumber(paper.ranks.collection.out_of) }}</li>
    </ul>
  </li>
  <li><strong>Download rankings, year to date</strong>:
    <ul>
      <li>Site-wide: <strong>{{ helpers.formatNumber(paper.ranks.ytd.rank) }}</strong> out of {{ helpers.formatNumber(paper.ranks.ytd.out_of) }}</li>
    </ul>
  </li>
  <li><strong>Download rankings since beginning of last month</strong>:
    <ul>
      <li>Site-wide: <strong>{{ helpers.formatNumber(paper.ranks.lastmonth.rank) }}</strong> out of {{ helpers.formatNumber(paper.ranks.lastmonth.out_of) }}</li>
    </ul>
  </li>
</ul>
% end