% import helpers
<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl", google_tag=google_tag)
    <title>Rxivist privacy policy</title>
  </head>

  <body>
    <div class="container" id="main">

      %include("components/header")

      <div class="row">
        <div class="col">
          <h1>Privacy Policy</h1>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          <h2>Visitor data</h2>
            <p>Rxivist.org does not collect any information about its users that is not incidentally captured by server access logs, which are limited to URLs and timestamps.
            <p>We do use Google Analytics (with all demographic collection features disabled) to better understand how visitors use our site. Google has published details of <a href="https://policies.google.com/privacy">how they use this data</a> if you would like to review details of their privacy and compliance measures.

          <h2>Content</h2>
            Rxivist builds profiles of papers and authors using only content pulled directly from <a href="https://biorxiv.org">bioRxiv</a>. If we have erroneously interpreted the data, or have problematically outdated information about a paper or author, please contact Richard Abdill at <strong>rabdill@umn.edu</strong>.
        </div>
      </div>
    </div>

    %include("components/footer")

  </body>
</html>