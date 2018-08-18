<!doctype html>
<html ng-app="app">
  <head>
    %include("components/metadata.tpl")
    <title>Rxivist: Popular biology pre-print papers ranked</title>

    <link rel="stylesheet" href="https://cdn.rawgit.com/angular-ui/bower-ui-grid/master/ui-grid.min.css"/>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-touch.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-animate.js"></script>
    <script src="http://ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-aria.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/csv.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/pdfmake.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/vfs_fonts.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/lodash.min.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/jszip.min.js"></script>
    <script src="http://ui-grid.info/docs/grunt-scripts/excel-builder.dist.js"></script>
    <script src="https://cdn.rawgit.com/angular-ui/bower-ui-grid/master/ui-grid.min.js"></script>
    <style>
      .myGrid {
        width: 100%;
        height: 1000px;
      }
    </style>
    <script>
      var app = angular.module('app', ['ngTouch', 'ui.grid', 'ui.grid.resizeColumns'])

      app.controller('MainCtrl', ['uiGridConstants', function(uiGridConstants) {
        var vm = this;

        download_col_max_width = 150;

        vm.gridOptions = {
          enableSorting: true,
          enableFiltering: true,
          columnDefs: [
            {
              field: 'title',
              enableFiltering: false,
              width: '50%'
            },
            {
              field: 'collection',
              enableSorting: false,
              filter: {
                type: uiGridConstants.filter.SELECT,
                selectOptions: [
                  % for cat in category_list:
                    {value: "{{cat}}", label: "{{cat}}"},
                  % end
                ]
              },
              width: '20%',
              maxWidth: 150
            },
            {
              field: 'alltime_downloads',
              enableFiltering: false,
              maxWidth: download_col_max_width
            },
            {
              field: 'ytd_downloads',
              enableFiltering: false,
              maxWidth: download_col_max_width
            },
            {
              field: 'month_downloads',
              enableFiltering: false,
              maxWidth: download_col_max_width
            },
          ],
          onRegisterApi: function( gridApi ) {
            vm.grid1Api = gridApi;
          },
          data: [
            % for result in results:
              {
                title: "{{result.title}}",
                collection: "{{result.collection}}",
                id: {{result.id}},
                url: "{{result.url}}",
                alltime_downloads: {{result.alltime_downloads}},
                ytd_downloads: {{result.ytd_downloads}},
                month_downloads: {{result.month_downloads}}
              },
            % end
          ]
        };
      }]);
    </script>
  </head>
  <body>
    <div class="container-fluid" id="main">

      %include("components/header", stats=stats)

      <div class="row">
        <div class="col">
          <div class="alert alert-danger" role="alert" style="display: {{"none" if error == "" else "block"}}">
            {{error}}
          </div>
          %if len(results) == 0:
            <div><h3>No results found for "{{query}}"</h3></div>
          %else:
            <h2>{{title}}</h2>
          %end
          % if len(results) > 0:
            <div ng-controller="MainCtrl as $ctrl" class="col-sm-12">
              <div id="grid1" ui-grid="$ctrl.gridOptions" class="myGrid" ui-grid-resize-columns></div>
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