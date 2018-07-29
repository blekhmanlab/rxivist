<div class="row" id="header">
  <div class="col col-md-7 col-sm-12" style="padding-bottom: 15px;">
      <a href="/"><img src="/static/rxivist_logo_bad.png" alt="Rxivist logo" title="It's pronounced 'Archivist.'"></a>
    <div><em>Read the trending bioRxiv papers</em></div>
  </div>
  %try:
  %  displaystats = stats
  %except:
  %  displaystats = False
  %if displaystats:
    <div class="col col-md-5 col-sm-12">
      <ul>
        <li><strong>Rxivist is in development.</strong> If you're here, you're almost definitely lost.
        <li>Currently indexing <strong>{{stats.paper_count}} papers</strong> from <strong>{{stats.author_count}} authors</strong>
        <li><a href="#" data-toggle="modal" data-target="#about">About the project</a>
      </ul>
    </div>
  %end
</div>
