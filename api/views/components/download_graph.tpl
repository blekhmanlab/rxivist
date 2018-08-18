<script>
var ctx = document.getElementById('myChart').getContext('2d');
var chart = new Chart(ctx, {
  // The type of chart we want to create
  type: 'line',

  // The data for our dataset
  data: {
    labels: [
      % for entry in paper.traffic:
        "{{entry.month}}/{{entry.year}}",
      % end
    ],
    datasets: [{
      label: "Downloads",
      backgroundColor: '#468847',
      borderColor: '#468847',
      data: [
        % for entry in paper.traffic:
          {{entry.downloads}},
        % end
      ],
    }]
  },

  // Configuration options go here
  options: {}
});
</script>