<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist: Popular biology pre-print papers ranked</title>
  </head>

  <body>
  <br>
    <div class="container" id="main">
      %include("components/header")
      <div class="row">
        <div class="col">
          <h1>404: Page not found</h1>
          <p>Not all those who wander are lost. But you are.
          <p><a href="/">Try the homepage</a>, it's nice over there.
        </div>
      </div>
    </div>

    %include("components/footer")
    %include("components/about_modal")

    <script>
      $(function () {
        $('[data-toggle="tooltip"]').tooltip()
      })
    </script>
  </body>
</html>