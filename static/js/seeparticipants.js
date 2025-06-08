

document.addEventListener("DOMContentLoaded", () => {
  console.log("✅ JS Loaded");

  const tbody = document.getElementById("participants-body");

  if (!tbody) {
    console.error("❌ Table body with id 'participants-body' not found");
    return;
  }

  fetch("/seeparticipants")
    .then((res) => {
      if (!res.ok) throw new Error("Failed to fetch participants");
      return res.json();
    })
    .then((data) => {
      console.log("✅ Data fetched:", data);
      if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8">No participants found.</td></tr>`;
        return;
      }

      tbody.innerHTML = data.map((p) => `
        <tr>
          <td>${p.name}</td>
          <td>${p.sub_event}</td>
          <td>${p.amount_paid}</td>
          <td>${p.email}</td>
          <td>${p.contact}</td>
          <td>${p.team_size}</td>
          <td>${p.roll_no}</td>
          <td>${p.branch}</td>
        </tr>
      `).join("");
    })
    .catch((err) => {
      console.error("❌ Fetch error:", err);
      tbody.innerHTML = `<tr><td colspan="8">Failed to load participants</td></tr>`;
    });
});
