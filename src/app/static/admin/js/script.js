function activeTab(presentation) {
  const aElement = presentation.querySelector("[aria-selected=true]");

  if (aElement) {
    const tab = document.querySelector(
      "[data-tab-id='%s']".replace("%s", aElement.dataset.bsTarget),
    );

    if (tab) {
      const tabContainer = tab.closest("[role=tab-container]");

      tabContainer?.querySelectorAll("[role=tab]").forEach((element) => {
        element.classList.add("d-none");
      });

      tab.classList.remove("d-none");
      tab.classList.add("show");
    }
  }
}

export function transformMovingTab(movingTab, presentation) {
  const presentationRect = presentation.getBoundingClientRect();

  movingTab.style.width = `${presentationRect.width}px`;
  movingTab.style.height = `${presentationRect.height}px`;
  movingTab.style.left = `${presentation.offsetLeft}px`;

  if (presentation) activeTab(presentation);
}

export function transformAllMovingTab() {
  for (const tabElement of document.querySelectorAll("[role=tablist]")) {
    let presentation = tabElement.querySelector(
      "[role=presentation]:has(a[aria-selected=true])",
    );
    let movingTab = tabElement.querySelector(".moving-tab");

    if (presentation && movingTab) {
      transformMovingTab(movingTab, presentation);
      activeTab(presentation);
    }
  }
}

export function createMovingTab(presentation) {
  const divElement = document.createElement("div");

  divElement.style.width = presentation.offsetWidth + "px";
  divElement.style.height = presentation.offsetHeight + "px";
  divElement.style.transition = "0.5s";

  divElement.classList.value =
    "moving-tab position-absolute nav-link bg-gradient-dark";

  return divElement;
}

export function initAllMovingTabs() {
  for (const tabElement of document.querySelectorAll("[role=tablist]")) {
    let presentation = tabElement.querySelector("[role=presentation]");

    if (presentation) {
      let movingTab = createMovingTab(presentation);
      tabElement.append(movingTab);
      transformMovingTab(movingTab, presentation);
      activeTab(presentation);
    }
  }
}

export function createLoader() {
  let divElement = document.createElement("div");

  divElement.classList.value =
    "bg-gradient-dark position-absolute w-100 h-100 z-index-10000 rounded-2";

  divElement.dataset.bsRole = "loader";

  return divElement;
}

export function updateInvoiceModalStats(form) {
  const invoiceTotalSpanElement = form.querySelector(
    "span[data-invoice-total]",
  );

  const invoicePaidSpanElement = form.querySelector("span[data-invoice-paid]");

  const invoiceRemainingSpanElement = form.querySelector(
    "span[data-invoice-remaining]",
  );

  const itemsInput = form.querySelector("input#items");
  const paidAmountInput = form.querySelector("input#paid_amount");

  if (
    !invoiceTotalSpanElement ||
    !invoicePaidSpanElement ||
    !invoiceRemainingSpanElement ||
    !itemsInput ||
    !paidAmountInput
  ) {
    return;
  }

  let items = [];

  try {
    items = JSON.parse(itemsInput.value || "[]");
  } catch {
    items = [];
  }

  const invoiceTotal = items.reduce(
    (total, item) => total + Number(item.total_price || 0),
    0,
  );

  const paidAmount = Number(paidAmountInput.value || 0);

  const remainingAmount = Math.max(invoiceTotal - paidAmount, 0);

  invoiceTotalSpanElement.textContent = invoiceTotal.toFixed(2);
  invoicePaidSpanElement.textContent = paidAmount.toFixed(2);
  invoiceRemainingSpanElement.textContent = remainingAmount.toFixed(2);
}

(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const loaderElement = document.querySelector("div[data-bs-role=loader]");

    setTimeout(() => {
      loaderElement.classList.add("fade");
      setTimeout(() => {
        loaderElement.remove();
      }, 500);
    }, 2000);
  });

  document.addEventListener("click", (event) => {
    const tabListElement = event.target.closest("[role=tablist]");

    if (tabListElement) {
      const presentation = event.target.closest("[role=presentation]");
      const movingTab = tabListElement.querySelector("div.moving-tab");

      if (!movingTab) {
        tabListElement.append(createMovingTab(presentation));
      } else {
        transformMovingTab(movingTab, presentation);
      }
    }
  });

  window.addEventListener("resize", () => {
    transformAllMovingTab();
  });

  document.addEventListener("resize", () => {
    transformAllMovingTab();
  });
}).call();

(function () {
  if (getComputedStyle(document.body).direction === "rtl") {
    const $inputs = $("input.form-control[type=date]");

    $inputs.each(function () {
      const $input = $(this);

      $input.persianDatepicker({
        months: [
          "حمل",
          "ثور",
          "جوزا",
          "سرطان",
          "اسد",
          "سنبله",
          "میزان",
          "عقرب",
          "قوس",
          "جدی",
          "دلو",
          "حوت",
        ],
        dowTitle: [
          "شنبه",
          "یکشنبه",
          "دوشنبه",
          "سه شنبه",
          "چهارشنبه",
          "پنج شنبه",
          "جمعه",
        ],
        shortDowTitle: ["ش", "ی", "د", "س", "چ", "پ", "ج"],
        showGregorianDate: false,
        persianNumbers: true,
        formatDate: "YYYY/MM/DD",
        selectedBefore: false,
        selectedDate: null,
        startDate: null,
        endDate: null,
        prevArrow: "◄",
        nextArrow: "►",
        theme: "default",
        alwaysShow: false,
        selectableYears: null,
        selectableMonths: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        cellWidth: 25,
        cellHeight: 20,
        fontSize: 13,
        isRTL: true,
        calendarPosition: {
          x: 0,
          y: 0,
        },
        onShow: function () {},
        onHide: function () {},
        onSelect: function () {
          const d = new Date($input.context.dataset.gdate);
          $input.context.value =
            d.getFullYear() +
            "-" +
            String(d.getMonth() + 1).padStart(2, "0") +
            "-" +
            String(d.getDate()).padStart(2, "0");
        },
        onRender: function () {},
      });
    });
  }
}).call(this);

(function () {
  const sideNavElement = document.querySelector("#sidenav-collapse-main");
  new PerfectScrollbar(sideNavElement, {
    suppressScrollX: true,
  });
}).call(this);

(function () {
  $(document).ready(function () {
    $("select").selectpicker();
  });
}).call(this);

(function () {
  let addInvoiceModalElement = document.querySelector("#AddInvoiceModal");

  if (addInvoiceModalElement) {
    $(document).on("change", "select#invoice_type", function () {
      let input = document.querySelector("input[type=hidden]#invoice_type");
      input.value = this.value;

      let batch_number = document.querySelector("div#AddItemModal input#batch_number")
      let row = batch_number.closest(".row")

      if (this.value === "SALE_RETURN") {
        row.classList.remove("d-none")
      } else {
        row.classList.add("d-none")
      }
    });

    let itemsInput = addInvoiceModalElement.querySelector("input#items");

    addInvoiceModalElement.addEventListener("click", (event) => {
      const target = event.target;

      let items = JSON.parse(itemsInput.value || "[]");

      if (target.closest("[data-bs-role='multiple-remove']")) {
        let trElement;
        let dataId;
        let index;

        for (const checkedElement of addInvoiceModalElement.querySelectorAll(
          'tbody input[type="checkbox"]:checked',
        )) {
          trElement = checkedElement.closest("tr[data-id]");
          dataId = trElement.dataset.id;

          index = items.findIndex((item) => item.medicine_id === +dataId);

          if (index !== -1) {
            items.splice(index, 1);

            trElement.remove();
          }
        }
      } else if (target.closest("[data-bs-role=remove]")) {
        let trElement = target.closest("tr[data-id]");
        let dataId = trElement.dataset.id;

        const index = items.findIndex((item) => item.medicine_id === +dataId);

        if (index !== -1) {
          items.splice(index, 1);

          trElement.remove();
        }

        itemsInput.value = JSON.stringify(items);
      }
    });
  }

  document.addEventListener("keyup", (event) => {
    const target = event.target;
    const input = target.closest("input#paid_amount");

    if (input) {
      let form = input.closest("form");
      updateInvoiceModalStats(form);
    }
  });
}).call(this);
