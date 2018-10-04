% import helpers
<div class="row" id="header">
  <div class="col-md-7" style="padding-left: 35px;">
    <a href="/"><img src="/static/rxivist_logo.png" class="img-fluid" alt="Rxivist logo" title="It's pronounced 'Archivist.'" width="350"></a>
  </div>
  % try:
  %  entity
  % except:
  %  entity = None
  %  category_filter = [] # if we don't have an entity type, we won't have a category filter
  % end
  % try:
  %  displaystats = stats
  % except:
  %  displaystats = False
  % end
  % if displaystats:
    <div class="col-lg-5">
      <ul>
        <li><strong>Rxivist is in development.</strong> If you're here, you're almost definitely lost.
        <li>Currently indexing <strong>{{ helpers.formatNumber(stats.paper_count) }} bioRxiv papers</strong> from <strong>{{ helpers.formatNumber(stats.author_count) }} authors</strong>
        <li><a href=
          % if entity == "papers":
            "/?entity=authors&category={{"" if len(category_filter) == 0 else category_filter[0]}}">Author leaderboards
          % else:
            "/?category={{"" if len(category_filter) == 0 else category_filter[0]}}">Paper search
          % end
        </a>
        <li><a href="#" data-toggle="modal" data-target="#about">About the project</a><br>
        <span class="social-logo"><a href="https://www.github.com/rabdill/rxivist" target="_blank"><img src="/static/github.png" ></a></span>
        <span class="social-logo"><a href="https://twitter.com/rxivist" target="_blank"><img src="/static/twitter.png"></a></span>
      </ul>
    </div>
  % end
</div>
