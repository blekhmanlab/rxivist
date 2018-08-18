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
          label: "Papers",
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
            value: {{ int(paper.downloads / download_distribution[1][0]) * download_distribution[1][0] }},
            borderColor: "red",
            label: {
              content: "THIS PAPER",
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
            labelString: 'paper count'
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