% import helpers
<div class="row" id="header">
  <div class="col-md-7" style="padding-bottom: 15px;">
    <a href="/"><img src="/static/rxivist_logo8.png" class="img-fluid" alt="Rxivist logo" title="It's pronounced 'Archivist.'" width="450"></a>

    <!-- <span class="social-logo"><a href="https://www.github.com/rabdill/rxivist"><img src="static/github.png" ></a></span>
	  <span class="social-logo"><a href="https://twitter.com/rxivist"><img src="static/twitter.png"></a></span> -->

  </div>
  %try:
  %  displaystats = stats
  %except:
  %  displaystats = False
  %end
  %if displaystats:
    <div class="col-md-5">
      <ul>
        <li><strong>Rxivist is in development.</strong> If you're here, you're almost definitely lost.
        <li>Currently indexing <strong>{{ helpers.formatNumber(stats.paper_count) }} papers</strong> from <strong>{{ helpers.formatNumber(stats.author_count) }} authors</strong>
        <li><a href="#" data-toggle="modal" data-target="#about">About the project</a>
      </ul>
    </div>
  %end
</div>
