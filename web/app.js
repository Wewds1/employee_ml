const state = {
  dashboard: null,
};

function money(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function pct(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function bandClass(band) {
  return String(band).toLowerCase();
}

function renderSummary(summary) {
  const profile = summary.profile;
  const heroMetrics = [
    { label: "Employees", value: profile.rows.toLocaleString() },
    { label: "Attrition rate", value: pct(profile.attrition_rate) },
    { label: "Average salary", value: money(profile.average_salary) },
    { label: "Average tenure", value: `${profile.average_tenure.toFixed(1)} yrs` },
  ];

  document.getElementById("heroMetrics").innerHTML = heroMetrics
    .map(
      (item) => `
        <div class="metric">
          <div class="label">${item.label}</div>
          <div class="value">${item.value}</div>
        </div>
      `
    )
    .join("");

  document.getElementById("riskSummary").innerHTML = [
    ["Critical", summary.critical_count],
    ["Elevated", summary.elevated_count],
    ["Stable", summary.stable_count],
  ]
    .map(
      ([label, value]) => `
        <div class="risk-card">
          <div class="label">${label}</div>
          <div class="value">${value}</div>
        </div>
      `
    )
    .join("");

  const metrics = summary.model_metrics;
  document.getElementById("modelStats").innerHTML = [
    ["Accuracy", pct(metrics.accuracy)],
    ["Precision", pct(metrics.precision)],
    ["Recall", pct(metrics.recall)],
    ["F1 score", pct(metrics.f1_score)],
  ]
    .map(
      ([label, value]) => `
        <div class="risk-card">
          <div class="label">${label}</div>
          <div class="value">${value}</div>
        </div>
      `
    )
    .join("");
}

function renderDepartmentHeat(rows) {
  const maxRisk = Math.max(...rows.map((row) => row.avg_risk));
  document.getElementById("departmentHeat").innerHTML = rows
    .map(
      (row) => `
        <div class="heat-row">
          <div>${row.department}</div>
          <div class="heat-track">
            <div class="heat-fill" style="width:${(row.avg_risk / maxRisk) * 100}%"></div>
          </div>
          <div>${pct(row.avg_risk)}</div>
        </div>
      `
    )
    .join("");
}

function renderDepartmentTable(rows) {
  document.getElementById("departmentTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Department</th>
          <th>Headcount</th>
          <th>Avg risk</th>
          <th>Attrition</th>
          <th>Avg salary</th>
          <th>Avg tenure</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr>
                <td>${row.department}</td>
                <td>${row.headcount}</td>
                <td>${pct(row.avg_risk)}</td>
                <td>${pct(row.attrition_rate)}</td>
                <td>${money(row.avg_salary)}</td>
                <td>${row.avg_tenure.toFixed(1)} yrs</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderDrivers(rows) {
  document.getElementById("driverList").innerHTML = rows
    .map(
      (row) => `
        <div class="driver-item">
          <div>
            <strong>${row.feature}</strong>
            <div class="driver-meta">${row.direction}</div>
          </div>
          <div>${row.weight > 0 ? "+" : ""}${row.weight.toFixed(3)}</div>
        </div>
      `
    )
    .join("");
}

function renderEmployeeTable(rows) {
  document.getElementById("employeeTable").innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Employee</th>
          <th>Department</th>
          <th>Risk</th>
          <th>Band</th>
          <th>Salary</th>
          <th>Tenure</th>
        </tr>
      </thead>
      <tbody>
        ${rows
          .map(
            (row) => `
              <tr>
                <td>${row.employee_id}</td>
                <td>${row.department}</td>
                <td>${pct(row.attrition_risk)}</td>
                <td><span class="badge ${bandClass(row.risk_band)}">${row.risk_band}</span></td>
                <td>${money(row.salary)}</td>
                <td>${row.tenure_years.toFixed(1)} yrs</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function renderScatter(rows) {
  const width = 820;
  const height = 320;
  const pad = 38;
  const xMax = Math.max(...rows.map((row) => row.tenure_years));
  const yMax = 1;
  const points = rows.slice(0, 140).map((row) => {
    const x = pad + (row.tenure_years / xMax) * (width - pad * 2);
    const y = height - pad - (row.attrition_risk / yMax) * (height - pad * 2);
    const color =
      row.risk_band === "critical" ? "#ff7f8a" : row.risk_band === "elevated" ? "#ffbc58" : "#46c59c";
    return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="4.5" fill="${color}">
      <title>${row.employee_id} | ${row.department} | ${pct(row.attrition_risk)}</title>
    </circle>`;
  });

  document.getElementById("scatterPlot").innerHTML = `
    <svg class="scatter" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
      <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"></rect>
      <line x1="${pad}" y1="${height - pad}" x2="${width - pad}" y2="${height - pad}" stroke="rgba(136,164,194,0.3)" />
      <line x1="${pad}" y1="${pad}" x2="${pad}" y2="${height - pad}" stroke="rgba(136,164,194,0.3)" />
      <text x="${width / 2}" y="${height - 8}" text-anchor="middle" fill="#8b9ab1" font-size="12">Tenure years</text>
      <text x="18" y="${height / 2}" text-anchor="middle" fill="#8b9ab1" font-size="12" transform="rotate(-90 18 ${height / 2})">Attrition risk</text>
      ${points.join("")}
    </svg>
  `;
}

function renderPrediction(prediction) {
  document.getElementById("predictionCard").innerHTML = `
    <div class="label">Projected attrition risk</div>
    <div class="prediction-score">${pct(prediction.attrition_risk)}</div>
    <div class="prediction-band ${bandClass(prediction.risk_band)}">${prediction.risk_band}</div>
    <div class="driver-list" style="margin-top:14px;">
      ${prediction.drivers
        .map(
          (item) => `
            <div class="driver-item">
              <div>
                <strong>${item.feature}</strong>
                <div class="driver-meta">impact on this scenario</div>
              </div>
              <div>${item.impact > 0 ? "+" : ""}${item.impact.toFixed(3)}</div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard");
  const payload = await response.json();
  state.dashboard = payload;

  renderSummary(payload.summary);
  renderDepartmentHeat(payload.department_breakdown);
  renderDepartmentTable(payload.department_breakdown);
  renderDrivers(payload.driver_summary);
  renderEmployeeTable(payload.top_employees);
  renderScatter(payload.risk_vs_tenure);
  renderPrediction({
    attrition_risk: payload.top_employees[0].attrition_risk,
    risk_band: payload.top_employees[0].risk_band,
    drivers: payload.top_employees[0].drivers,
  });
}

document.getElementById("predictForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(event.target);
  const payload = Object.fromEntries(formData.entries());
  ["age", "salary", "tenure_years", "performance_score"].forEach((key) => {
    payload[key] = Number(payload[key]);
  });
  payload.perf_was_missing = Number(payload.perf_was_missing);

  const response = await fetch("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const prediction = await response.json();
  renderPrediction(prediction);
});

loadDashboard();
