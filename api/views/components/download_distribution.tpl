<script>
function findBucket(entity, buckets) {
  for(var i=0; i < buckets.length; i++) {
    if(entity < buckets[i]) {
      return buckets[i];
      // NOTE: The entity isn't put into the i-1 bucket, as it should be, because
      // the line is drawn to the left of the bar in question and ends up looking
      // like it's in the wrong spot.
    }
  }
  return 0;
}

window.onload = function() {
  var ctx1 = document.getElementById("downloadsDistribution").getContext('2d');
  bucket_list = [
    % for entry in download_distribution:
      {{entry[0]}},
    % end
  ];
  // determine which bucket the entity is in:
  entityBucket = findBucket({{ entity.downloads }}, bucket_list)
  meanBucket = findBucket({{ averages["mean"] }}, bucket_list)
  medianBucket = findBucket({{ averages["median"] }}, bucket_list)

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
            },
          },
          /*{
            type: "line",
            mode: "vertical",
            scaleID: "x-axis-0",
            value: meanBucket,
            borderColor: "red",
            label: {
              content: "mean",
              enabled: true,
              position: "top"
            }
          },
          {
            type: "line",
            mode: "vertical",
            scaleID: "x-axis-0",
            value: medianBucket,
            borderColor: "red",
            label: {
              content: "median",
              enabled: true,
              position: "bottom"
            }
          },*/
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