<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>rxivist: Popular biology pre-print papers ranked</title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
  </head>

  <body>
    <div class="container">
      <div class="row">
        <div class="col">
          <img src="/static/rxivist_logo_bad.png">
          <h1>Most popular bioinformatics papers, all-time</h1>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <div class="accordion" id="alltime">
            % for result in rankings:
              <div class="card">
                <div class="card-header" id="heading{{result["id"]}}">
                  <h5 class="mb-0">
                    <button class="btn btn-link" type="button" data-toggle="collapse" data-target="#collapse{{result["id"]}}" aria-expanded="true" aria-controls="collapse{{result["id"]}}">
                      <strong>{{result["rank"]}}:</strong> {{result["title"]}} &ndash; {{result["downloads"]}} downloads
                    </button>
                  </h5>
                </div>
                <div id="collapse{{result["id"]}}" class="collapse" aria-labelledby="heading{{result["id"]}}" data-parent="#alltime">
                  <div class="card-body">
                    <p>
                    % for i, author in enumerate(result["authors"]):
                      {{author}}{{", " if i < (len(result["authors"]) - 1) else ""}}
                    % end
                    <a href="{{result["url"]}}" target="_blank">view paper</a>
                    <p>{{result["abstract"]}}
                  </div>
                </div>
              </div>
            % end
          </div>
        </div>
      </div>

      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
      <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
    </div>
  </body>
</html>