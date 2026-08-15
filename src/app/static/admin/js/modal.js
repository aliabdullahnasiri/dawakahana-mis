import { createListSectionItem, resetForm } from "./form.js";
import {
  createLoader,
  transformAllMovingTab,
  initAllMovingTabs,
  updateInvoiceModalStats,
} from "./script.js";

(function () {
  document.addEventListener("show.bs.modal", (event) => {

    const form = event.target.querySelector("form");

    if (event.target.dataset.onShowReset !== "false") 
    if (form) resetForm(form);
  });

  document.addEventListener("show.bs.modal", (event) => {
    const form = event.target.querySelector("form[data-get]");

    if (form) {
      resetForm(form);

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

          let names = ["input", "textarea", "select"];

          Array.from(
            form.querySelectorAll(names.join(String.fromCharCode(44))),
          ).forEach((input) => {
            let val = data[input.id];

            input.disabled = false;
            if (Array.from(readonly).includes(input.id)) {
              input.disabled = true;
            }

            switch (input.tagName) {
              case "SELECT":
                if (input.dataset.dependsOn) {
                  setTimeout(() => {
                    $(input).selectpicker("val", val);
                  }, 500);
                } else $(input).selectpicker("val", val);
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
        });
    }
  });

  document.addEventListener("hidden.bs.modal", (event) => {});
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
    let b = event.target.closest("#ViewModal")?.querySelector(".modal-body");
    if (b) b.innerHTML = "";
  });
}).call();

(function () {
  document.addEventListener("afterSubmit", (event) => {
    if (event?.detail?.errors) return;

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
      if (table && data) {
        let thead = table.querySelector("thead");
        let tbody = table.querySelector("tbody");

        let trElement = document.createElement("tr");
        let tdElement;
        let dataName;
        let dataVal;

        trElement.dataset.id = data.medicine_id;

        for (const thElement of Array.from(thead.querySelectorAll("th"))) {
          dataName = thElement.dataset.name;
          dataVal = data[dataName];

          tdElement = document.createElement("td");
          tdElement.classList.value = "text-xs text-center";

          if (dataVal !== undefined) {
            tdElement.innerHTML = dataVal;
          }

          trElement.append(tdElement);
        }

        const checkboxTd = trElement.firstElementChild;
        if (checkboxTd) {
          let divElement = document.createElement("div");
          let inputElement = document.createElement("input");

          tdElement.classList.value = "checkbox-td text-center";

          divElement.classList.value = "form-check form-check-info p-0";

          inputElement.type = "checkbox";
          inputElement.name = "multiple-remove";
          inputElement.classList.add("form-check-input");

          divElement.append(inputElement);
          checkboxTd.append(divElement);
        }

        const removeTd = trElement.lastElementChild;
        if (removeTd) {
          removeTd.classList.value = "text-center";

          let removeElement = document.createElement("a");
          removeElement.dataset.bsRole = "remove";

          removeElement.dataset.role = "remove";
          removeElement.innerHTML = `<i class="material-symbols-rounded fs-5">delete</i>`;
          removeElement.classList.value =
            "text-secondary font-weight-bold text-xs m-1 btn btn-xs text-white btn-danger";

          removeTd.append(removeElement);
        }

        tbody.append(trElement);
      }

      if (form && itemsInput) {
        let items = JSON.parse(itemsInput.value || "[]");

        items.push({
          medicine_id: data.medicine_id,
          quantity: data.quantity,
          unit_price: data.unitPrice,
          total_price: data.total_price,
        });

        itemsInput.value = JSON.stringify(items);
      }

      updateInvoiceModalStats(form);

      // Open next modal after closing
      if (modalElement) {
        let nextModal = bootstrap.Modal.getOrCreateInstance(modalElement);
        nextModal.show();
      }
    }
  });
}).call(this);
