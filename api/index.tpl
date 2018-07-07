<img src="/static/rxivist_logo_bad.png">
<h1>Most popular bioinformatics papers, all-time</h1>

<ul>
  % for result in rankings:
    <li><strong>{{result["rank"]}}:</strong> <a href="/papers/{{result["id"]}}">{{result["title"]}}</a> &ndash; {{result["downloads"]}} downloads</li>
  % end
</ul>
