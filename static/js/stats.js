function loadStatsCharts() {
  fetch("/api/stats-data")
    .then(response => response.json())
    .then(data => {
      console.log("Fetched stats data:", data);

      const regCtx = document.getElementById("registrationChart").getContext("2d");
      new Chart(regCtx, {
        type: "bar",
        data: {
          labels: data.dates,
          datasets: [{
            label: "Registrations",
            data: data.registrations,
            backgroundColor: "#3498db"
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });

      const amtCtx = document.getElementById("amountChart").getContext("2d");
      new Chart(amtCtx, {
        type: "bar",
        data: {
          labels: data.dates,
          datasets: [{
            label: "Amount Collected",
            data: data.amounts,
            backgroundColor: "#2ecc71"
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    });
}
