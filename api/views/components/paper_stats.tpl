{{ format(paper.downloads, ",d") }} downloads
  %if paper.date.monthname != "":
    since {{paper.date.monthname}} {{paper.date.year}}
  %end

<ul>
  <li><strong>Download rankings, all-time:</strong>
    <ul>
      <li>Site-wide: <strong>{{ format(paper.ranks.alltime.rank, ",d") }}</strong> out of {{ format(paper.ranks.alltime.out_of, ",d") }}</li>
      <li>In {{paper.collection}}: <strong>{{ format(paper.ranks.collection.rank, ",d") }}</strong> out of {{ format(paper.ranks.collection.out_of, ",d") }}</li>
    </ul>
  </li>
  <li><strong>Download rankings, year to date</strong>:
    <ul>
      <li>Site-wide: <strong>{{ format(paper.ranks.ytd.rank, ",d") }}</strong> out of {{ format(paper.ranks.ytd.out_of, ",d") }}</li>
    </ul>
  </li>
  <li><strong>Download rankings since beginning of last month</strong>:
    <ul>
      <li>Site-wide: <strong>{{ format(paper.ranks.lastmonth.rank, ",d") }}</strong> out of {{ format(paper.ranks.lastmonth.out_of, ",d") }}</li>
    </ul>
  </li>
</ul>