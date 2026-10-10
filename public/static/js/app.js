/**
 * Medical Expiry Tracker – Global Application Script
 * Controls 3D tilt effects, mobile menu, toast dismissal, modals, and AJAX operations.
 */

document.addEventListener("DOMContentLoaded", () => {
  initMobileMenu();
  init3DCardTilt();
  initToastAutoDismiss();
  initModalTriggers();
  initGlobalShortcuts();
});

/* --- Mobile Menu & Backdrop --- */
function initMobileMenu() {
  const toggleBtn = document.getElementById("mobileMenuToggle");
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebarBackdrop");

  if (!toggleBtn || !sidebar) return;

  toggleBtn.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    if (backdrop) backdrop.classList.toggle("show");
  });

  if (backdrop) {
    backdrop.addEventListener("click", () => {
      sidebar.classList.remove("open");
      backdrop.classList.remove("show");
    });
  }
}

/* --- 3D Card Hover Tilt Effect --- */
function init3DCardTilt() {
  const cards = document.querySelectorAll(".stat-card-3d");

  cards.forEach(card => {
    card.addEventListener("mousemove", (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -7;
      const rotateY = ((x - centerX) / centerX) * 7;

      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });

    card.addEventListener("mouseleave", () => {
      card.style.transform = "perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)";
    });
  });
}

/* --- Toast Auto Dismissal --- */
function initToastAutoDismiss() {
  const toasts = document.querySelectorAll(".toast");
  toasts.forEach(toast => {
    // Auto-remove after 5.5s
    setTimeout(() => {
      dismissToast(toast);
    }, 5500);

    const closeBtn = toast.querySelector(".toast-close");
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        dismissToast(toast);
      });
    }
  });
}

function dismissToast(toast) {
  if (!toast) return;
  toast.style.opacity = "0";
  toast.style.transform = "translateX(100%)";
  setTimeout(() => {
    toast.remove();
  }, 300);
}

/* --- Modal Engine --- */
function initModalTriggers() {
  // Close buttons inside modals
  document.querySelectorAll("[data-close-modal]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      const modal = e.target.closest(".modal-backdrop");
      if (modal) modal.classList.remove("show");
    });
  });

  // Click outside modal body to close
  document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("show");
      }
    });
  });

  // ESC key to close modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.show").forEach(m => m.classList.remove("show"));
    }
  });
}

/* --- Quick Details Modal Loader --- */
window.viewMedicineDetails = function(medicineId) {
  const modal = document.getElementById("medicineDetailsModal");
  if (!modal) return;

  const contentBox = document.getElementById("medicineModalContent");
  contentBox.innerHTML = `
    <div style="text-align:center; padding: 40px;">
      <i class="fas fa-spinner fa-spin" style="font-size: 32px; color: var(--secondary);"></i>
      <p style="margin-top: 12px; color: var(--text-muted);">Loading medicine pharmaceutical data...</p>
    </div>
  `;
  modal.classList.add("show");

  fetch(`/medicines/${medicineId}`, {
    headers: { "X-Requested-With": "XMLHttpRequest" }
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) {
      contentBox.innerHTML = `<div class="empty-state"><p>${data.error}</p></div>`;
      return;
    }

    const med = data.medicine;
    contentBox.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 20px;">
        <div>
          <h2 style="font-size: 22px; font-weight: 700;">${med.name}</h2>
          <p style="color: var(--text-muted); font-size: 13px;">${med.category} • Manufactured by <strong>${med.manufacturer}</strong></p>
        </div>
        <div>
          <span class="badge ${med.badge_class}">${med.badge_text}</span>
          ${med.is_low_stock ? `<span class="badge badge-lowstock" style="margin-left: 6px;"><i class="fas fa-box"></i> LOW STOCK</span>` : ''}
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; margin-bottom: 20px;">
        <div style="background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-glass);">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Batch Number</span>
          <span class="batch-tag" style="font-size: 14px; display:inline-block; margin-top: 4px;">${med.batch_number}</span>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-glass);">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Stock in Inventory</span>
          <span style="font-size: 18px; font-weight: 700; color: ${med.is_low_stock ? 'var(--status-lowstock)' : 'var(--text-main)'};">
            ${med.quantity} units <small style="font-size: 12px; font-weight: 400; color: var(--text-dim);">(Min: ${med.minimum_stock})</small>
          </span>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-glass);">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Manufacturing Date</span>
          <span style="font-size: 14px; font-weight: 500;">${med.manufacturing_date}</span>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 12px 16px; border-radius: 10px; border: 1px solid var(--border-glass);">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Expiry Date</span>
          <span style="font-size: 14px; font-weight: 600; color: ${med.is_expired ? 'var(--status-danger)' : (med.is_expiring_soon ? 'var(--status-warning)' : 'var(--status-safe)')};">
            ${med.expiry_date}
          </span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px;">
        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid var(--border-glass); text-align: center;">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Purchase Cost</span>
          <span style="font-size: 15px; font-weight: 600;">$${med.purchase_price.toFixed(2)}</span>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid var(--border-glass); text-align: center;">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Retail Price</span>
          <span style="font-size: 15px; font-weight: 600; color: var(--status-safe);">$${med.selling_price.toFixed(2)}</span>
        </div>
        <div style="background: rgba(255,255,255,0.03); padding: 12px; border-radius: 10px; border: 1px solid var(--border-glass); text-align: center;">
          <span style="font-size: 11px; text-transform: uppercase; color: var(--text-dim); display:block;">Total Batch Value</span>
          <span style="font-size: 15px; font-weight: 700; color: #38bdf8;">$${(med.quantity * med.purchase_price).toFixed(2)}</span>
        </div>
      </div>

      <div style="background: rgba(255,255,255,0.02); padding: 14px; border-radius: 10px; border: 1px solid var(--border-glass); margin-bottom: 20px;">
        <h4 style="font-size: 12px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Supplier Information</h4>
        <p style="font-size: 14px; color: var(--text-main);">${med.supplier || 'No dedicated supplier recorded.'}</p>
      </div>

      ${med.description ? `
      <div style="background: rgba(255,255,255,0.02); padding: 14px; border-radius: 10px; border: 1px solid var(--border-glass);">
        <h4 style="font-size: 12px; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Clinical Notes & Storage</h4>
        <p style="font-size: 13px; color: var(--text-muted);">${med.description}</p>
      </div>
      ` : ''}

      <div style="display:flex; justify-content: flex-end; gap: 10px; margin-top: 24px;">
        <a href="/medicines/edit/${med.id}" class="btn btn-secondary btn-sm"><i class="fas fa-edit"></i> Edit Medicine</a>
        <button type="button" class="btn btn-primary btn-sm" data-close-modal><i class="fas fa-check"></i> Close</button>
      </div>
    `;

    // Re-bind close modal buttons
    initModalTriggers();
  })
  .catch(err => {
    contentBox.innerHTML = `<div class="empty-state"><p>Failed to load medicine details: ${err.message}</p></div>`;
  });
};

/* --- Global Delete Confirmation Modal --- */
window.confirmDelete = function(formId, medicineName) {
  const modal = document.getElementById("deleteConfirmModal");
  if (!modal) {
    if (confirm(`Are you sure you want to permanently delete '${medicineName}' from inventory?`)) {
      document.getElementById(formId).submit();
    }
    return;
  }

  document.getElementById("deleteTargetName").innerText = medicineName;
  const confirmBtn = document.getElementById("confirmDeleteActionBtn");
  
  // Clone to remove previous listeners
  const newBtn = confirmBtn.cloneNode(true);
  confirmBtn.parentNode.replaceChild(newBtn, confirmBtn);

  newBtn.addEventListener("click", () => {
    document.getElementById(formId).submit();
  });

  modal.classList.add("show");
};

/* --- Alert Quick Actions via AJAX --- */
window.markAlertAsRead = function(alertId, btnElement) {
  fetch(`/alerts/mark-read/${alertId}`, {
    method: "POST",
    headers: { "X-Requested-With": "XMLHttpRequest" }
  })
  .then(res => res.json())
  .then(data => {
    if (data.success) {
      const card = btnElement.closest(".alert-item-card");
      if (card) {
        card.classList.remove("unread");
        btnElement.remove();
      }
      updateAlertBadges(data.unread_count);
    }
  })
  .catch(err => console.error("Error marking alert as read:", err));
};

function updateAlertBadges(count) {
  const navBadge = document.getElementById("navAlertBadge");
  const headerBadge = document.getElementById("headerAlertBadge");
  
  if (navBadge) {
    navBadge.innerText = count;
    if (count === 0) navBadge.style.display = "none";
  }
  if (headerBadge) {
    headerBadge.innerText = count;
    if (count === 0) headerBadge.style.display = "none";
  }
}

/* --- Keyboard Shortcuts --- */
function initGlobalShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Focus search on Ctrl + / or Command + /
    if ((e.ctrlKey || e.metaKey) && e.key === "/") {
      e.preventDefault();
      const searchInput = document.getElementById("quickSearchInput") || document.getElementById("inventorySearchInput");
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
      }
    }
  });
}
