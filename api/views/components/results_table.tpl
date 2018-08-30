
<link rel="stylesheet" href="//cdn.rawgit.com/angular-ui/bower-ui-grid/master/ui-grid.min.css"/>
<script src="//ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular.js"></script>
<script src="//ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-touch.js"></script>
<script src="//ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-animate.js"></script>
<script src="//ajax.googleapis.com/ajax/libs/angularjs/1.7.0/angular-aria.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/csv.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/pdfmake.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/vfs_fonts.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/lodash.min.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/jszip.min.js"></script>
<script src="//ui-grid.info/docs/grunt-scripts/excel-builder.dist.js"></script>
<script src="//cdn.rawgit.com/angular-ui/bower-ui-grid/master/ui-grid.min.js"></script>
<style>
  .myGrid {
    width: 100%;
    /* height: 70%; */
  }
</style>
<script>
  var app = angular.module('app', ['ngTouch', 'ui.grid', 'ui.grid.resizeColumns'])//, 'ui.grid.pagination'])

  app.controller('MainCtrl', ['uiGridConstants', function(uiGridConstants) {
    var vm = this;

    download_col_max_width = 150;

    vm.gridOptions = {
      enableSorting: true,
      enableFiltering: true,
      paginationPageSize: 25,
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
          maxWidth: download_col_max_width,
          defaultSort: {
            direction: uiGridConstants.DESC,
            priority: 0
          },
          sortDirectionCycle: [null, uiGridConstants.DESC, uiGridConstants.ASC]
        },
        {
          field: 'ytd_downloads',
          enableFiltering: false,
          maxWidth: download_col_max_width,
          sortDirectionCycle: [null, uiGridConstants.DESC, uiGridConstants.ASC]
        },
        {
          field: 'month_downloads',
          enableFiltering: false,
          maxWidth: download_col_max_width,
          sortDirectionCycle: [null, uiGridConstants.DESC, uiGridConstants.ASC]
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

<div ng-controller="MainCtrl as $ctrl" class="col-sm-12">
  <div id="grid1" ui-grid="$ctrl.gridOptions" class="myGrid" ui-grid-resize-columns></div>
</div>