/**
 * Medical Expiry Tracker – Form Validation Engine
 * Enforces business rules: Expiry > Mfg date, positive quantities and prices.
 */

document.addEventListener("DOMContentLoaded", () => {
  const medicineForm = document.getElementById("medicineForm");
  if (!medicineForm) return;

  const mfgInput = document.getElementById("manufacturing_date");
  const expInput = document.getElementById("expiry_date");
  const qtyInput = document.getElementById("quantity");
  const purchasePriceInput = document.getElementById("purchase_price");
  const sellingPriceInput = document.getElementById("selling_price");
  const minStockInput = document.getElementById("minimum_stock");

  // Live date listener
  if (mfgInput && expInput) {
    mfgInput.addEventListener("change", validateDates);
    expInput.addEventListener("change", validateDates);
  }

  // Live numeric listeners
  if (qtyInput) qtyInput.addEventListener("input", () => validateNonNegative(qtyInput, "Quantity"));
  if (purchasePriceInput) purchasePriceInput.addEventListener("input", () => validateNonNegative(purchasePriceInput, "Purchase Price"));
  if (sellingPriceInput) sellingPriceInput.addEventListener("input", () => validateNonNegative(sellingPriceInput, "Selling Price"));
  if (minStockInput) minStockInput.addEventListener("input", () => validateMinThreshold(minStockInput));

  medicineForm.addEventListener("submit", (e) => {
    let isValid = true;
    clearAllErrors();

    // Check mandatory fields
    const nameInput = document.getElementById("name");
    const batchInput = document.getElementById("batch_number");
    const catInput = document.getElementById("category");
    const mfgInput = document.getElementById("manufacturing_date");

    if (nameInput && !nameInput.value.trim()) {
      showError(nameInput, "Medicine name is required.");
      isValid = false;
    }

    if (batchInput && !batchInput.value.trim()) {
      showError(batchInput, "Batch number is required.");
      isValid = false;
    }

    if (catInput && !catInput.value.trim()) {
      showError(catInput, "Please select a medicine category.");
      isValid = false;
    }

    // Check dates
    if (mfgInput && expInput) {
      if (!mfgInput.value) {
        showError(mfgInput, "Manufacturing date is required.");
        isValid = false;
      }
      if (!expInput.value) {
        showError(expInput, "Expiry date is required.");
        isValid = false;
      } else if (mfgInput.value && expInput.value <= mfgInput.value) {
        showError(expInput, "Expiry date must be strictly after the manufacturing date.");
        isValid = false;
      }
    }

    // Check quantities and prices
    if (qtyInput && parseInt(qtyInput.value) < 0) {
      showError(qtyInput, "Quantity cannot be negative.");
      isValid = false;
    }

    if (purchasePriceInput && parseFloat(purchasePriceInput.value) < 0) {
      showError(purchasePriceInput, "Purchase price cannot be negative.");
      isValid = false;
    }

    if (sellingPriceInput && parseFloat(sellingPriceInput.value) < 0) {
      showError(sellingPriceInput, "Selling price cannot be negative.");
      isValid = false;
    }

    if (minStockInput && parseInt(minStockInput.value) < 1) {
      showError(minStockInput, "Minimum stock level must be at least 1.");
      isValid = false;
    }

    if (!isValid) {
      e.preventDefault();
      // Scroll to first error
      const firstError = document.querySelector(".form-error-msg");
      if (firstError) {
        firstError.closest(".form-group").scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  });

  function validateDates() {
    if (!mfgInput.value || !expInput.value) return;

    if (expInput.value <= mfgInput.value) {
      showError(expInput, "Expiry date must be strictly after the manufacturing date.");
    } else {
      clearError(expInput);
    }
  }

  function validateNonNegative(input, fieldName) {
    if (parseFloat(input.value) < 0) {
      showError(input, `${fieldName} cannot be negative.`);
    } else {
      clearError(input);
    }
  }

  function validateMinThreshold(input) {
    if (parseInt(input.value) < 1) {
      showError(input, "Minimum stock level must be 1 or higher.");
    } else {
      clearError(input);
    }
  }

  function showError(input, message) {
    clearError(input);
    input.style.borderColor = "var(--status-danger)";
    input.style.boxShadow = "0 0 10px var(--status-danger-glow)";
    
    const errDiv = document.createElement("div");
    errDiv.className = "form-error-msg";
    errDiv.style.color = "#f87171";
    errDiv.style.fontSize = "12px";
    errDiv.style.marginTop = "4px";
    errDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    input.closest(".form-group").appendChild(errDiv);
  }

  function clearError(input) {
    input.style.borderColor = "";
    input.style.boxShadow = "";
    const existing = input.closest(".form-group").querySelector(".form-error-msg");
    if (existing) existing.remove();
  }

  function clearAllErrors() {
    document.querySelectorAll(".form-error-msg").forEach(e => e.remove());
    document.querySelectorAll(".form-control").forEach(i => {
      i.style.borderColor = "";
      i.style.boxShadow = "";
    });
  }
});
