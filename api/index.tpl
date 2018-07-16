<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Rxivist: Popular biology pre-print papers ranked</title>

    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/css/bootstrap.min.css" integrity="sha384-WskhaSGFgHYWDcbwN70/dfYBj47jz9qbsMId/iRN3ewGhXQFZCSftd1LZCfmhktB" crossorigin="anonymous">
    <link href="https://fonts.googleapis.com/css?family=Open+Sans:700" rel="stylesheet">
    <link rel="stylesheet" href="/static/rxivist.css">
  </head>

  <body>
  <br>
    <div class="container" id="main">
      <div class="row" id="header">
        <div class="col col-md-7 col-sm-12" style="padding-bottom: 15px;">
            <a href="/"><img src="/static/rxivist_logo_bad.png"></a>
          <div><em>Read the trending bioRxiv papers</em></div>
        </div>
        <div class="col col-md-5 col-sm-12">
          <ul>
            <li><strong>Rxivist is in development.</strong> If you're here, you're almost definitely lost.
            <li>Currently indexing <strong>{{stats["paper_count"]}} papers</strong> from <strong>{{stats["author_count"]}} authors</strong>
            <li><a href="#" data-toggle="modal" data-target="#about">About the project</a>
          </ul>
        </div>
      </div>
      <div class="row">
        <div class="col">
          <div id="searchform">
            <form action="/" method="get">
              <div class="input-group mb-3 col-sm-7">
                <input type="text" class="form-control form-control-lg" id="basicsearchtext" name="q" placeholder="Enter search terms here" value="{{query}}">
                <div class="input-group-append">
                  <button type="submit" class="btn btn-altcolor">Search</button>
                </div>
                <div class="col-md-12">
                  <small class="form-text text-muted"><a href="#" data-toggle="modal" data-target="#search">Advanced search</a></small>
                </div>
              </div>
            </form>
          </div>
          
          <div class="alert alert-danger" role="alert" style="display: {{"none" if error == "" else "block"}}">
            {{error}}
          </div>
          % if len(results) == 0:
            <div><h3>No results found for "{{query}}"</h3></div>
          % else:
            <h2>{{title}}</h2>
            % if len(category_filter) > 0:
              <h4 style="padding-left: 20px;">in categor{{ "ies:" if len(category_filter) > 1 else "y" }}
                % for i, cat in enumerate(category_filter):
                  {{ cat }}{{", " if i < (len(category_filter)-1) else ""}}
                %end
              </h4>
            %end 
            <div class="accordion" id="alltime">
              % for i, result in enumerate(results):
                <div class="card">
                  <div class="card-header context" id="heading{{result["id"]}}"  data-toggle="collapse" data-target="#collapse{{result["id"]}}" aria-expanded="true" aria-controls="collapse{{result["id"]}}">
                    <strong>{{i+1}}:</strong> {{result["title"]}}
                    <br>
                    <span class="badge badge-secondary" style="margin-left: 10px;">{{result["downloads"]}} downloads</span>
                  </div>
                  <div id="collapse{{result["id"]}}" class="collapse" aria-labelledby="heading{{result["id"]}}" data-parent="#alltime">
                    <div class="card-body">
                      <p>
                      % for i, author in enumerate(result["authors"]):
                        <a href="/authors/{{author["id"]}}">{{ author["name"] }}</a>{{", " if i < (len(result["authors"]) - 1) else ""}}
                      % end
                      <a href="{{result["url"]}}" target="_blank" class="btn btn-altcolor float-right" role="button">view paper</a>
                      <p>{{result["abstract"]}}
                    </div>
                  </div>
                </div>
              % end
            </div>
          % end
        </div>
      </div>

      <!-- ADVANCED SEARCH MODAL -->
      <div class="modal fade" id="search" tabindex="-1" role="dialog" aria-labelledby="searchLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <form action="/" method="get">
              <div class="modal-header">
                <h5 class="modal-title" id="searchLabel">Advanced search</h5>
                <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                  <span aria-hidden="true">&times;</span>
                </button>
              </div>
              <div class="modal-body">
                  <div id="searchform">
                    <div class="form-group">
                      <label for="searchtext">Show papers related to...</label>
                      <input type="text" class="form-control" id="searchtext" name="q" value="{{query}}">
                    </div>
                    <div class="form-group">
                      <label for="categoryselect">from bioRxiv categories...</label>
                      <select multiple class="form-control" id="categoryselect" name="category">
                        % for cat in category_list:
                          <option>{{cat}}</option>
                        %end
                      </select>
                      <div class="text-right">
                          <span class="badge badge-secondary" data-toggle="tooltip" data-placement="top" data-html="true" title="<strong>Category filter</strong><br>Use the Cmd (on Mac) or Ctrl (on Windows) key to toggle multiple choices.<br>To show papers from all categories, select none or all of the options.">?</span>
                      </div>
                    </div>
                  </div>
              </div>
              <div class="modal-footer">
                <button type="submit" class="btn btn-altcolor">Search</button>
              </div>
            </form>
          </div>
        </div>
      </div>

      <!-- ABOUT -->
      <div class="modal fade" id="about" tabindex="-1" role="dialog" aria-labelledby="aboutLabel" aria-hidden="true">
        <div class="modal-dialog" role="document">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="aboutLabel">About</h5>
              <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body">
              <p>Rxivist indexes and sorts metadata from <a href="https://www.biorxiv.org/">bioRxiv</a>, a <a href="http://www.sciencemag.org/news/2017/09/are-preprints-future-biology-survival-guide-scientists">preprint</a> server operated by Cold Spring Harbor Laboratory. There is absolutely no official association between bioRxiv and this project.
              
              <p>Rxivist was developed in 2018 by Rich Abdill, of the <a href="http://blekhmanlab.org">Blekhman Lab</a> at the University of Minnesota. Its source code is <a href="https://github.com/rabdill/rxivist">available on GitHub</a>.
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
            </div>
          </div>
        </div>
      </div>

      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js" integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo" crossorigin="anonymous"></script>
      <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js" integrity="sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49" crossorigin="anonymous"></script>
      <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.1.1/js/bootstrap.min.js" integrity="sha384-smHYKdLADwkXOn1EmN1qk/HfnUcbVRZyYmZ4qpPea6sjB/pTJ0euyQp0Mk8ck+5T" crossorigin="anonymous"></script>
      <script>
        $(function () {
          $('[data-toggle="tooltip"]').tooltip()
        })
      </script>
    </div>
    <div class="container">
      <div class="row">
        <div id="footer" class="col-sm-12">
          <p class="pull-right"><a href="http://blekhmanlab.org/">Blekhman<span class="footer-altcolor">Lab</span></a>
        </div>
      </div>
    </div>
  </body>
</html>