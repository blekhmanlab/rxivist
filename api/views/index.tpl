<!doctype html>
<html lang="en">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist: Popular biology pre-print papers ranked</title>
  </head>
  <body>
    <div class="container" id="main">

      %include("components/header", stats=stats) # TODO: Figure out how this works

      <div class="row">
        <div class="col">
          <div id="searchform">
            <form action="/" method="get">
              <div class="input-group mb-3 col-sm-9">
                <input type="text" class="form-control form-control-lg" id="basicsearchtext" name="q" placeholder="Enter search terms here (optional)" value="{{query}}">
              </div>
              <div class="input-group mb-3 col-md-6">
                <select class="form-control col-sm-6" id="category" name="category">
                  <option value="">all categories</option>
                  % for cat in category_list:
                    <option
                    % if cat in category_filter:
                      selected
                    % end
                    >{{cat}}</option>
                  %end
                </select>
                <select class="form-control  col-sm-6" id="timeframe" name="timeframe">
                  <option value="alltime" 
                  %if timeframe == "alltime":
                    selected
                  %end
                  >all time</option>
                  <option value="ytd"
                  %if timeframe == "ytd":
                    selected
                  %end
                  >year to date</option>
                </select>
                <div class="input-group-append">
                  <button type="submit" class="btn btn-altcolor">Search</button>
                </div>
              </div>
            </form>
          </div>
          
          <div class="alert alert-danger" role="alert" style="display: {{"none" if error == "" else "block"}}">
            {{error}}
          </div>
          %if len(results) == 0:
            <div><h3>No results found for "{{query}}"</h3></div>
          %else:
            <h2>{{title}}</h2>
          %end
          %if len(category_filter) > 0:
            <h4 style="padding-left: 20px;">in categor{{ "ies:" if len(category_filter) > 1 else "y" }}
              % for i, cat in enumerate(category_filter):
                {{ cat }}{{", " if i < (len(category_filter)-1) else ""}}
              %end
            </h4>
          %end 
          % if len(results) > 0:
            <div class="accordion" id="alltime">
              % for i, result in enumerate(results):
                <div class="card">
                  <div class="card-header context" id="heading{{result.id}}"  data-toggle="collapse" data-target="#collapse{{result.id}}" aria-expanded="true" aria-controls="collapse{{result.id}}">
                    <strong>{{i+1}}:</strong> {{result.title}}
                    <br>
                    <span class="badge badge-secondary" style="margin-left: 10px;">{{result.downloads}} downloads</span>
                    % if len(category_filter) != 1:
                      <span class="badge badge-secondary" style="margin-left: 10px;">{{result.collection}}</span>
                    % end
                    % if result.date.month is not None:
                      <span class="badge badge-secondary" style="margin-left: 10px;">{{result.date.monthname}} {{result.date.year}}</span>
                    % end
                  </div>
                  <div id="collapse{{result.id}}" class="collapse" aria-labelledby="heading{{result.id}}" data-parent="#alltime">
                    <div class="card-body">
                      <p>
                      % for i, author in enumerate(result.authors):
                        <a href="/authors/{{author.id}}">{{ author.full }}</a>{{", " if i < (len(result.authors) - 1) else ""}}
                      % end
                      <a href="{{result.url}}" target="_blank" class="btn btn-altcolor float-right" role="button">view paper</a>
                      <p>{{result.abstract}}
                    </div>
                  </div>
                </div>
              % end
            </div>
          % end
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