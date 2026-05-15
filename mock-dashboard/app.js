(function () {
  const data = window.FLOW2API_DATA;
  const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

  function setActiveNav() {
    const path = window.location.pathname.split("/").pop() || "dashboard.html";
    document.querySelectorAll(".nav a").forEach((link) => {
      const href = link.getAttribute("href");
      link.classList.toggle("active", href === path);
    });
  }

  function statusClass(status) {
    if (status === "Verified" || status === "Approved") {
      return "status-verified";
    }
    if (status === "Rejected") {
      return "status-rejected";
    }
    return "status-review";
  }

  function setupSupplierDashboard() {
    const input = document.querySelector("[data-testid='supplier-id-input']");
    const button = document.querySelector("[data-testid='search-btn']");
    const resultsArea = document.querySelector("[data-testid='results-area']");
    const message = document.querySelector("[data-testid='supplier-message']");
    const name = document.querySelector("[data-testid='supplier-name']");
    const status = document.querySelector("[data-testid='verification-status']");
    const lastVerified = document.querySelector("[data-testid='last-verified']");
    const email = document.querySelector("[data-testid='contact-email']");

    async function searchSupplier() {
      const supplierId = input.value.trim().toUpperCase();
      button.disabled = true;
      message.textContent = "Searching supplier records...";
      resultsArea.hidden = false;
      await wait(420);

      const supplier = data.suppliers[supplierId];
      if (!supplier) {
        name.textContent = "";
        status.textContent = "";
        status.className = "metric-value";
        lastVerified.textContent = "";
        email.textContent = "";
        message.textContent = "No supplier found.";
        button.disabled = false;
        return;
      }

      name.textContent = supplier.name;
      status.textContent = supplier.status;
      status.className = `metric-value ${statusClass(supplier.status)}`;
      lastVerified.textContent = supplier.lastVerified;
      email.textContent = supplier.email;
      message.textContent = `Record found for ${supplierId}.`;
      button.disabled = false;
    }

    button.addEventListener("click", searchSupplier);
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        searchSupplier();
      }
    });
  }

  function setupApiScores() {
    const select = document.querySelector("[data-testid='api-select']");
    const button = document.querySelector("[data-testid='check-btn']");
    const resultsArea = document.querySelector("[data-testid='score-results-area']");
    const message = document.querySelector("[data-testid='score-message']");
    const score = document.querySelector("[data-testid='api-score']");
    const issues = document.querySelector("[data-testid='issues-count']");
    const lastChecked = document.querySelector("[data-testid='last-checked']");

    Object.entries(data.apiScores).forEach(([value, api]) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = api.name;
      select.appendChild(option);
    });

    async function checkScore() {
      const selected = data.apiScores[select.value];
      button.disabled = true;
      message.textContent = "Checking documentation quality...";
      resultsArea.hidden = false;
      await wait(380);

      score.textContent = `${selected.score}/100`;
      issues.textContent = selected.issues;
      lastChecked.textContent = selected.lastChecked;
      message.textContent = `Latest score loaded for ${selected.name}.`;
      button.disabled = false;
    }

    button.addEventListener("click", checkScore);
  }

  function setupReports() {
    const tbody = document.querySelector("[data-testid='reports-table'] tbody");
    const detail = document.querySelector("[data-testid='report-detail']");
    const fields = {
      name: detail.querySelector("[data-field='name']"),
      department: detail.querySelector("[data-field='department']"),
      date: detail.querySelector("[data-field='date']"),
      status: detail.querySelector("[data-field='status']"),
      owner: detail.querySelector("[data-field='owner']"),
      notes: detail.querySelector("[data-field='notes']")
    };

    function openReport(report, row) {
      tbody.querySelectorAll("tr").forEach((item) => item.classList.remove("active"));
      row.classList.add("active");
      fields.name.textContent = report.name;
      fields.department.textContent = report.department;
      fields.date.textContent = report.date;
      fields.status.textContent = report.status;
      fields.owner.textContent = report.owner;
      fields.notes.textContent = report.notes;
      detail.hidden = false;
    }

    data.reports.forEach((report, index) => {
      const row = document.createElement("tr");
      row.tabIndex = 0;
      row.setAttribute("data-testid", `report-row-${index + 1}`);
      row.innerHTML = `
        <td>${report.name}</td>
        <td>${report.department}</td>
        <td>${report.date}</td>
        <td><span class="${statusClass(report.status)}">${report.status}</span></td>
      `;
      row.addEventListener("click", () => openReport(report, row));
      row.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openReport(report, row);
        }
      });
      tbody.appendChild(row);
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setActiveNav();
    const page = document.body.dataset.page;
    if (page === "dashboard") {
      setupSupplierDashboard();
    } else if (page === "api-scores") {
      setupApiScores();
    } else if (page === "reports") {
      setupReports();
    }
  });
})();
