<script>
window.onload = function() {
  var ctx = document.getElementById("downloadsDistribution").getContext('2d');
  var myChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [
        % for entry in download_distribution:
          {{entry[0]}},
        % end
      ],
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
            value: {{ int(entity.downloads / download_distribution[1][0]) * download_distribution[1][0] }},
            borderColor: "red",
            label: {
              content: "THIS {{ entity_name.upper() }}",
              enabled: true,
              position: "top"
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
          },
          type: 'logarithmic'
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
  var ctx2 = document.getElementById("downloadsDistributionNoLog").getContext('2d');
  var myChart2 = new Chart(ctx2, {
    type: 'bar',
    data: {
      labels: [
        % for entry in download_distribution:
          {{entry[0]}},
        % end
      ],
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
            value: {{ int(entity.downloads / download_distribution[1][0]) * download_distribution[1][0] }},
            borderColor: "red",
            label: {
              content: "THIS {{ entity_name.upper() }}",
              enabled: true,
              position: "top"
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