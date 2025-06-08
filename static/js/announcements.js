document.addEventListener("DOMContentLoaded", function () {
  fetch("/announcements")
    .then(response => response.json())
    .then(data => {
      const container = document.getElementById("announcements");
      if (!container) return;

      if (data.length === 0) {
        container.innerHTML = "<p>No announcements available.</p>";
      } else {
        container.innerHTML = "";
        data.forEach(item => {
          const div = document.createElement("div");
          div.classList.add("mb-2", "text-left", "p-2", "border", "rounded");
          div.innerHTML = `
            <strong>${item.date}</strong><br>
            <em>${item.eventname}</em><br>
            ${item.message}
          `;
          container.appendChild(div);
        });
      }
    })
    .catch(err => {
      const container = document.getElementById("announcements");
      container.innerHTML = "<p>Error loading announcements.</p>";
      console.error("Error fetching announcements:", err);
    });
});
