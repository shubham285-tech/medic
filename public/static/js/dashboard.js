/**
 * Medical Expiry Tracker – Dashboard Analytics & Interactive Charts
 * Visualizes expiry status, timelines, and category stock using Chart.js.
 */

document.addEventListener("DOMContentLoaded", () => {
  initDashboardCharts();
});

function initDashboardCharts() {
  const statusCtx = document.getElementById("expiryStatusChart");
  const trendCtx = document.getElementById("monthlyTrendChart");
  const categoryCtx = document.getElementById("categoryDistributionChart");

  if (!statusCtx || !trendCtx) return;

  // Configure Chart.js global defaults for glassmorphic dark theme
  if (window.Chart) {
    Chart.defaults.color = "#94a3b8";
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
  }

  fetch("/api/dashboard/charts")
    .then(res => res.json())
    .then(data => {
      // 1. Expiry Status Donut Chart
      if (statusCtx) {
        new Chart(statusCtx, {
          type: "doughnut",
          data: {
            labels: data.status_doughnut.labels,
            datasets: [{
              data: data.status_doughnut.data,
              backgroundColor: [
                "rgba(16, 185, 129, 0.85)",  // Safe
                "rgba(245, 158, 11, 0.85)",   // Expiring Soon
                "rgba(239, 68, 68, 0.85)"     // Expired
              ],
              borderColor: [
                "#10b981",
                "#f59e0b",
                "#ef4444"
              ],
              borderWidth: 2,
              hoverOffset: 6
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "70%",
            plugins: {
              legend: {
                position: "bottom",
                labels: {
                  boxWidth: 12,
                  padding: 16,
                  color: "#cbd5e1",
                  font: { weight: "600" }
                }
              },
              tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.95)",
                titleColor: "#f8fafc",
                bodyColor: "#cbd5e1",
                borderColor: "rgba(255, 255, 255, 0.15)",
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8
              }
            },
            animation: {
              animateScale: true,
              animateRotate: true,
              duration: 900
            }
          }
        });
      }

      // 2. Monthly Expiry Trend Bar Chart
      if (trendCtx) {
        new Chart(trendCtx, {
          type: "bar",
          data: {
            labels: data.monthly_trend.labels,
            datasets: [{
              label: "Medicines Expiring",
              data: data.monthly_trend.data,
              backgroundColor: "rgba(6, 182, 212, 0.65)",
              borderColor: "#06b6d4",
              borderWidth: 1.5,
              borderRadius: 6,
              hoverBackgroundColor: "rgba(37, 99, 235, 0.8)"
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: {
                grid: {
                  color: "rgba(255, 255, 255, 0.05)",
                  drawBorder: false
                },
                ticks: {
                  color: "#94a3b8"
                }
              },
              y: {
                beginAtZero: true,
                ticks: {
                  stepSize: 1,
                  color: "#94a3b8"
                },
                grid: {
                  color: "rgba(255, 255, 255, 0.05)",
                  drawBorder: false
                }
              }
            },
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.95)",
                borderColor: "rgba(255, 255, 255, 0.15)",
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                callbacks: {
                  label: function(context) {
                    return ` ${context.parsed.y} medicine batch(es) expiring`;
                  }
                }
              }
            }
          }
        });
      }

      // 3. Category Stock Distribution Chart
      if (categoryCtx && data.category_polar) {
        new Chart(categoryCtx, {
          type: "polarArea",
          data: {
            labels: data.category_polar.labels,
            datasets: [{
              data: data.category_polar.data,
              backgroundColor: [
                "rgba(37, 99, 235, 0.7)",
                "rgba(6, 182, 212, 0.7)",
                "rgba(16, 185, 129, 0.7)",
                "rgba(245, 158, 11, 0.7)",
                "rgba(168, 85, 247, 0.7)",
                "rgba(236, 72, 153, 0.7)"
              ],
              borderColor: "rgba(15, 23, 42, 0.8)",
              borderWidth: 2
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              r: {
                ticks: { display: false },
                grid: { color: "rgba(255, 255, 255, 0.05)" }
              }
            },
            plugins: {
              legend: {
                position: "right",
                labels: {
                  boxWidth: 10,
                  padding: 10,
                  color: "#cbd5e1"
                }
              }
            }
          }
        });
      }
    })
    .catch(err => console.error("Error loading dashboard chart data:", err));
}
