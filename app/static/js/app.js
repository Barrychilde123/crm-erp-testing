function addLine() {
  const tbody = document.querySelector("#line-table tbody");
  if (!tbody) return;
  const first = tbody.querySelector(".line-row");
  const row = first.cloneNode(true);
  row.querySelectorAll("input").forEach((input) => {
    if (input.name === "qty") input.value = 1;
    if (input.name === "price") input.value = 0;
  });
  const select = row.querySelector("select");
  if (select) select.selectedIndex = 0;
  tbody.appendChild(row);
  updateTotal();
}

function removeLine(button) {
  const rows = document.querySelectorAll("#line-table tbody .line-row");
  if (rows.length > 1) {
    button.closest("tr").remove();
    updateTotal();
  }
}

function fillPrice(select) {
  const option = select.selectedOptions[0];
  const row = select.closest("tr");
  const price = row.querySelector('input[name="price"]');
  if (option && option.dataset.price && price) {
    price.value = option.dataset.price;
  }
  updateTotal();
}

function updateTotal() {
  let total = 0;
  document.querySelectorAll("#line-table tbody .line-row").forEach((row) => {
    const qty = parseFloat(row.querySelector('input[name="qty"]').value) || 0;
    const price = parseFloat(row.querySelector('input[name="price"]').value) || 0;
    const subtotal = qty * price;
    const cell = row.querySelector(".line-subtotal");
    if (cell) cell.textContent = subtotal.toFixed(2);
    total += subtotal;
  });
  const el = document.getElementById("order-total");
  if (el) el.textContent = total.toFixed(2);
}

document.addEventListener("DOMContentLoaded", () => {
  updateTotal();
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity .3s";
      flash.style.opacity = "0";
      setTimeout(() => (flash.style.display = "none"), 320);
    }, 4200);
  });
});
