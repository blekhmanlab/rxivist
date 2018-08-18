<ul>
  <li>{{paper.downloads}} downloads
          %if paper.date.monthname != "":
            since {{paper.date.monthname}} {{paper.date.year}}
          %end
  <li><strong>Download rankings, all-time:</strong>
    <ul>
      <li>Site-wide: <strong>{{paper.ranks.alltime.rank}}</strong> out of {{paper.ranks.alltime.out_of}}</li>
      <li>In {{paper.collection}}: <strong>{{paper.ranks.collection.rank}}</strong> out of {{paper.ranks.collection.out_of}}</li>
    </ul>
  </li>
  <li><strong>Download rankings, year to date</strong>:
    <ul>
      <li>Site-wide: <strong>{{paper.ranks.ytd.rank}}</strong> out of {{paper.ranks.ytd.out_of}}</li>
    </ul>
  </li>
  <li><strong>Download rankings since beginning of last month</strong>:
    <ul>
      <li>Site-wide: <strong>{{paper.ranks.lastmonth.rank}}</strong> out of {{paper.ranks.lastmonth.out_of}}</li>
    </ul>
  </li>
</ul>