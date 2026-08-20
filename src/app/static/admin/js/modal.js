import { createListSectionItem, resetForm, groupSwitcher } from "./form.js";
import {
  createLoader,
  transformAllMovingTab,
  initAllMovingTabs,
  updateInvoiceModalStats,
} from "./script.js";

function addInvoiceItem(form, table, item, itemsInput, formElement) {
  const data = item;

  if (!data) {
    return;
  }

  let items = [];

  try {
    items = JSON.parse(itemsInput?.value || "[]");
  } catch {
    items = [];
  }

  const stocks =
    Array.isArray(data.stocks) && data.stocks.length
      ? data.stocks
      : [
          {
            batch_number: data.batch_number,
            quantity: data.quantity,
          },
        ];

  let formValues = {};

  if (formElement) {
    const formData = new FormData(formElement);

    for (const [key, value] of formData.entries()) {
      formValues[key] = value;
    }
  }

  for (const stock of stocks) {
    const stockQuantity = Number(stock.quantity || 0);

    if (stockQuantity <= 0) {
      continue;
    }

    const stockItem = {
      medicine_id: data.medicine_id,
      batch_number: stock.batch_number ?? data.batch_number ?? null,
      quantity: stockQuantity,
      unit_price: Number(data.unit_price || 0),
      total_price: stockQuantity * Number(data.unit_price || 0),
    };

    for (const [key, value] of Object.entries(formValues)) {
      if (stockItem[key] === undefined && value !== "") {
        stockItem[key] = value;
      }
    }

    items.push(stockItem);

    if (table) {
      const thead = table.querySelector("thead");
      const tbody = table.querySelector("tbody");

      if (!thead || !tbody) {
        continue;
      }

      const trElement = document.createElement("tr");

      trElement.dataset.id = data.medicine_id;
      trElement.dataset.stockId = stock.stock_id ?? "";

      for (const thElement of Array.from(thead.querySelectorAll("th"))) {
        const dataName = thElement.dataset.name;

        const tdElement = document.createElement("td");
        tdElement.className = "text-xs text-center align-middle";

        let dataValue;

        if (dataName === "batch_number") {
          dataValue = stockItem.batch_number;
        } else if (dataName === "quantity") {
          dataValue = stockItem.quantity;
        } else if (dataName === "unit_price") {
          dataValue = Number(stockItem.unit_price).toFixed(2);
        } else if (dataName === "total_price") {
          dataValue = Number(stockItem.total_price).toFixed(2);
        } else {
          dataValue = data[dataName];
        }

        if (dataValue !== undefined && dataValue !== null) {
          tdElement.innerHTML = dataValue;
        }

        trElement.append(tdElement);
      }

      const checkboxTd = trElement.firstElementChild;

      if (checkboxTd) {
        checkboxTd.className = "checkbox-td text-center align-middle";

        const divElement = document.createElement("div");
        divElement.className = "form-check form-check-info p-0 m-0";

        const inputElement = document.createElement("input");

        inputElement.type = "checkbox";
        inputElement.name = "multiple-remove";
        inputElement.className = "form-check-input";

        if (data.is_deletable === false) {
          inputElement.disabled = true;
        }

        divElement.append(inputElement);
        checkboxTd.append(divElement);
      }

      const removeTd = trElement.lastElementChild;

      if (removeTd) {
        removeTd.className = "text-center align-middle";

        const removeElement = document.createElement("button");

        removeElement.type = "button";
        removeElement.dataset.bsRole = "remove";
        removeElement.dataset.role = "remove";

        removeElement.innerHTML = `
          <i class="material-symbols-rounded fs-5">
            delete
          </i>
        `;

        removeElement.className =
          "text-secondary font-weight-bold text-xs " +
          "m-1 btn btn-xs text-white btn-danger";

        if (data.is_deletable === false) {
          removeElement.classList.add("disabled");
          removeElement.disabled = true;
        }

        removeTd.append(removeElement);
      }

      tbody.append(trElement);
    }
  }

  if (itemsInput) {
    itemsInput.value = JSON.stringify(items);
  }

  updateInvoiceModalStats(form);
}

function cleanInvoiceItemsTable(table, form, itemsInput) {
  if (table)
    Array.from(table.querySelectorAll("tbody tr:not(.no-data)")).forEach(
      (tr) => {
        tr.remove();
      },
    );

  if (form && itemsInput) {
    itemsInput.value = "";
    updateInvoiceModalStats(form);
  }
}

(function () {
  document.addEventListener("show.bs.modal", (event) => {
    const form = event.target.querySelector("form");

    if (
      form &&
      !form.dataset.get &&
      event.target.dataset.onShowReset !== "false"
    ) {
      resetForm(form);
    }

    if (event.target.dataset.onShowReset == "false") {
      const selectElements = form.querySelectorAll("select");

      // Recreate Bootstrap Select
      selectElements.forEach((selectElement) => {
        const input = document.querySelector(
          `input[type="hidden"]#${selectElement.id}`,
        );

        if (input) {
          input.value = selectElement.value;
        }

        groupSwitcher(selectElement);
      });
    }
  });

  document.addEventListener("show.bs.modal", (event) => {
    if (!event.relatedTarget?.closest("[data-id]")?.dataset.id) {
      return;
    }

    const form = event.target.querySelector("form[data-get]");

    if (form) {
      resetForm(form);

      let table = form.querySelector("table[data-role=invoice-item]");
      let itemsInput = form.querySelector("input[type=hidden]#items");

      const totalDebtElement = form.querySelector("span[data-total-debt]");
      const totalCreditElement = form.querySelector("span[data-total-credit]");

      if (table && itemsInput) {
        cleanInvoiceItemsTable(table, form, itemsInput);
      }

      Array.from(form.querySelectorAll("input")).forEach((element) => {
        let groupElement = element.closest(".input-group");

        if (groupElement) {
          groupElement.classList.value = "input-group input-group-outline";
        }
      });

      const get = form.dataset.get;
      const id =
        event.relatedTarget.dataset.id ||
        event.relatedTarget?.closest("[data-id]")?.dataset.id;

      const url = get.replace("-1", id);

      fetch(url, {
        method: "get",
      })
        .then((response) => response.json())
        .then((data) => {
          let readonly = data?.readonly || new Array();

          let names = ["input", "textarea", "select", "button"];

          Array.from(
            form.querySelectorAll(names.join(String.fromCharCode(44))),
          ).forEach((input) => {
            let val = data[input.id];

            input.disabled = false;
            if (Array.from(readonly).includes(input.id)) {
              if (input.tagName !== "SELECT") {
                input.disabled = true;
              }
            }

            switch (input.tagName) {
              case "SELECT":
                const select = $(input);

                if (select.data("selectpicker")) {
                  select.selectpicker("destroy");
                }

                const depInput = document.querySelector(
                  `input[type="hidden"]#${input.id}`,
                );

                if (depInput) {
                  depInput.value = input.value;
                }

                $(input)
                  .prop("disabled", Array.from(readonly).includes(input.id))
                  .selectpicker();

                if (input.dataset.dependsOn) {
                  setTimeout(() => {
                    $(input).selectpicker("val", val);
                  }, 500);
                } else $(input).selectpicker("val", val);

                groupSwitcher(input);

                break;
            }

            switch (input.type) {
              case "select-one":
                input
                  ?.querySelector("option[value='%s']".replace("%s", val))
                  ?.setAttribute("selected", true);
                break;

              case "checkbox":
                input.checked = val ? true : false;

                break;

              case "file":
                let dropZone = input.closest("div.drop-zone");

                if (dropZone) {
                  let ulElement = dropZone.querySelector(".list-section ul");

                  if (ulElement) {
                    ulElement.innerHTML = "";

                    if (data[input.id])
                      for (const f of data[input.id]) {
                        if (f == null) continue;
                        let selector = "li[data-id='%s']";
                        if (
                          !ulElement.querySelector(
                            selector.replace("%s", f.link),
                          )
                        ) {
                          let item = createListSectionItem(
                            f.extension,
                            f.human_size,
                            true,
                            f.file_url,
                            f.id,
                          );
                          ulElement.append(item);
                        }

                        if (!input.multiple) break;
                      }
                  } else {
                    if (input.multiple) {
                    } else {
                      // Avatar
                      let fileOutput =
                        input.parentElement.querySelector(".output");

                      if (fileOutput) fileOutput.src = val || "";
                    }
                  }
                }
                break;

              case "select-one":
                const divElement = document.createElement("div");
                divElement.innerHTML = val;

                const v = divElement.querySelector(".value")?.innerText;

                if (v) input.value = v;

                break;

              default:
                if (val != undefined) {
                  let multiValueInput = input.closest("div.multi-value-input");

                  if (multiValueInput) {
                    multiValueInput.classList.remove("readonly");
                    if (Array.from(readonly).includes(input.id)) {
                      multiValueInput.classList.add("readonly");
                    }

                    const valuesElement =
                      multiValueInput.querySelector("div.values");

                    Array.from(val).forEach((v) => {
                      const spanElement = document.createElement("span");
                      spanElement.classList.value =
                        "badge badge-sm bg-gradient-secondary mx-2 my-1 cursor-pointer tt-none";
                      spanElement.innerHTML = v;
                      spanElement.dataset.role = "value";

                      valuesElement.append(spanElement);
                    });
                  } else {
                    input.value = data[input.id];

                    let inputGroup = input.closest("div.input-group");
                    if (inputGroup) inputGroup.classList.add("is-filled");
                  }
                }

                break;
            }
          });

          {
            // invoice item
            let items = data.items;

            if (table && items) {
              for (const item of Array.from(items)) {
                addInvoiceItem(form, table, item, itemsInput);
              }
            }
          }
        });
    }
  });

  document.addEventListener("show.bs.modal", (event) => {});

  document.addEventListener("hidden.bs.modal", (event) => {});

  document.addEventListener("click", (event) => {
    let target = event.target;

    let btn = target.closest("button[data-bs-target='#AddItemModal']");

    if (btn) {
      let currentForm = target.closest("form");

      let currentModal = target.closest(".modal");

      let nextModal = document.querySelector(btn.dataset.bsTarget);

      if (nextModal.dataset.onCloseOpen) {
        nextModal.dataset.onCloseOpen = `#${currentModal.id}`;
        let form = nextModal.querySelector("form[data-after-submit-open]");
        if (form) {
          form.dataset.afterSubmitOpen = `#${currentModal.id}`;
          if (currentForm) {
            const selectElements = currentForm.querySelectorAll("select");

            // Recreate Bootstrap Select
            selectElements.forEach((selectElement) => {
              groupSwitcher(selectElement, form);
            });
          }
        }
      }
    }
  });
}).call();

(function () {
  document.addEventListener("show.bs.modal", (event) => {
    let modalDialog = event.target.querySelector(".modal-dialog");

    if (event?.relatedTarget?.getAttribute("aria-label") !== "View Modal")
      return;

    let loaderElement = createLoader();

    modalDialog.append(loaderElement);

    let interval = setInterval(() => {
      let modalBody = modalDialog.querySelector(".modal-body");

      if (modalBody.innerHTML) {
        loaderElement.classList.add("fade");
        setTimeout(() => {
          loaderElement.remove();
          transformAllMovingTab();
          clearInterval(interval);
        }, 50);
      }
    }, 1000);
  });

  document.addEventListener("hidden.bs.modal", (event) => {
    let modalID;
    if ((modalID = event.target.dataset.onCloseOpen)) {
      let modalElement = document.querySelector(modalID);
      let nextModal = bootstrap.Modal.getOrCreateInstance(modalElement);
      nextModal.show();
    }

    let b = event.target.closest("#ViewModal")?.querySelector(".modal-body");

    if (b) b.innerHTML = "";
  });
}).call();

(function () {
  document.addEventListener("afterSubmit", (event) => {
    if (event?.detail?.errors || event.detail.category == "error") return;

    let formElement = event.target.closest("form[data-after-submit-open]");

    if (formElement) {
      let data = event?.detail?.data;

      let currentModal = formElement?.closest(".modal");
      let modalID = formElement.getAttribute("data-after-submit-open");
      let modalElement = document.querySelector(modalID);

      let form = modalElement.querySelector("form");
      let itemsInput = form.querySelector("input#items");

      if (data?.medicine_id) {
        let items = JSON.parse(itemsInput.value || "[]");
        const index = items.findIndex(
          (item) => item.medicine_id === +data?.medicine_id,
        );

        if (index !== -1) {
          Swal.fire({
            icon: "error",
            title: "Oops...",
            text: "This medicine has already been added to the invoice.",
          });

          return;
        }
      }

      // Close current modal
      if (currentModal) {
        let currentInstance = bootstrap.Modal.getInstance(currentModal);

        if (currentInstance) {
          currentInstance.hide();
        }
      }

      let table = modalElement.querySelector("table[data-role=invoice-item]");
      if (form && table && data && itemsInput) {
        addInvoiceItem(form, table, data, itemsInput, formElement);
      }

      // Open next modal after closing
      if (modalElement) {
        let nextModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        nextModal.show();
      }
    }
  });

  document.addEventListener("afterSubmit", (event) => {
    if (!event?.detail?.errors && event.detail.category !== "error") {
      let modal = event.target.closest("div.modal");
      let table = modal?.querySelector("table[data-role='invoice-item']");
      let tbody = table?.querySelector("tbody");
      let form = modal.querySelector("form");
      let itemsInput = form.querySelector("input[type=hidden]#items");

      if (tbody) {
        Array.from(tbody.querySelectorAll("a[data-bs-role='remove']")).forEach(
          (link) => {
            link.click();
          },
        );

        let nextModal = bootstrap.Modal.getOrCreateInstance(modal);
        nextModal.hide();

        if (form) {
          resetForm(form);
          cleanInvoiceItemsTable(table, form, itemsInput);
          updateInvoiceModalStats(form);
        }
      }
    }
  });

  document.addEventListener("hidden.bs.modal", (event) => {});
}).call(this);
