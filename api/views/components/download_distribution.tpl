<script>
window.onload = function() {
  var ctx1 = document.getElementById("downloadsDistribution").getContext('2d');

  // determine which bucket the entity is in:
  downloads = {{ entity.downloads }};
  bucket_list = [
    % for entry in download_distribution:
      {{entry[0]}},
    % end
  ];
  entityBucket = 0;
  for(var i=0; i < bucket_list.length; i++) {
    if(downloads < bucket_list[i]) {
      entityBucket = bucket_list[i];
      // NOTE: The entity isn't put into the i-1 bucket, as it should be, because
      // the line is drawn to the left of the bar in question and ends up looking
      // like it's in the wrong spot.
      break;
    }
  }

  var myChart = new Chart(ctx1, {
    type: 'bar',
    data: {
      labels: bucket_list,
      datasets: [
        {
          type: 'bar',
          label: "{{entity_name}}s",
          backgroundColor: "#2f69bf",
          data: [
            % for entry in download_distribution:
              {{entry[1]}},
            % end
          ],
          lineAtIndex: [
            100
          ],
        }
      ]
    },
    options: {
      responsive: true,
      legend: {
        display: false
      },
      annotation: {
        annotations: [
          {
            type: "line",
            mode: "vertical",
            scaleID: "x-axis-0",
            value: entityBucket,
            borderColor: "red",
            label: {
              content: "THIS {{ entity_name.upper() }}",
              enabled: true,
              position: "top"
            }
          },
          {
            type: "line",
            mode: "vertical",
            scaleID: "x-axis-0",
            value: entityBucket,
            borderColor: "none",
            label: {
              content: "{{ helpers.formatNumber(entity.downloads) }}",
              enabled: true,
              position: "middle"
            }
          }
        ]
      },
      scales: {
        yAxes: [{
          display: true,
          position: 'left',
          scaleLabel: {
            display: true,
            labelString: '{{entity_name}} count'
          }
        }],
        xAxes: [{
          scaleLabel: {
            display: true,
            labelString: 'Downloads, all-time'
          }
        }],
      }
    }
  });
}

</script>