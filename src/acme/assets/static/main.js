document.addEventListener(
  "DOMContentLoaded",
  function () {
    const wildcard = "*";

    const expandDiv = document.getElementById("expand");
    const sidebarDiv = document.getElementById("sidebar");
    const contentDiv = document.getElementById("content");
    const realmSelect = document.getElementById("realmSelect");

    // expand/collapse sidebar
    expandDiv.addEventListener("click", function () {
      const expanded = !(expandDiv.getAttribute("data-expanded") === "true");
      const width = expanded ? "35rem" : "20rem";
      const margin = expanded ? "36rem" : "21rem";

      sidebarDiv.style.width = width;
      contentDiv.style.marginLeft = margin;
      expandDiv.setAttribute("data-expanded", expanded);
      expandDiv.textContent = expanded ? "[collapse]" : "[expand]";
    });

    // realm specifics filter
    realmSelect.addEventListener("change", function handleSelectChange(event) {
      const selectedRealm = event.target.value;

      document.querySelectorAll(".config code").forEach((span) => {
        if (selectedRealm === wildcard) {
          span.classList.remove("hidden");
        } else {
          const realms = span.getAttribute("data-realms").split(" ");
          if (realms.includes(selectedRealm)) {
            span.classList.remove("hidden");
          } else {
            span.classList.add("hidden");
          }
        }
      });

      document.querySelectorAll("span.level2").forEach((span) => {
        if (selectedRealm === wildcard) {
          span.parentElement.classList.remove("hidden");
          span.parentElement.classList.remove("display-block");
        } else {
          const realms = span.getAttribute("data-realms").split(" ");
          if (realms.includes(selectedRealm)) {
            span.parentElement.classList.remove("hidden");
            span.parentElement.classList.add("display-block");
          } else {
            span.parentElement.classList.add("hidden");
            span.parentElement.classList.remove("display-block");
          }
        }
      });

      document.querySelectorAll("span.level1").forEach((elem) => {
        if (selectedRealm === wildcard) {
          elem.parentElement.classList.remove("hidden");
          elem.parentElement.classList.remove("display-block");
        } else {
          const realms = elem.getAttribute("data-realms").split(" ");
          if (realms.includes(selectedRealm)) {
            elem.parentElement.classList.remove("hidden");
            elem.parentElement.classList.add("display-block");
          } else {
            elem.parentElement.classList.add("hidden");
            elem.parentElement.classList.remove("display-block");
          }
        }
      });

      document.querySelectorAll("li.level1").forEach((li) => {
        if (selectedRealm === wildcard) {
          li.classList.remove("hidden");
          li.classList.remove("display-block");

          li.querySelectorAll("span.count").forEach((span) =>
            span.classList.remove("hidden")
          );

          li.querySelectorAll(":scope > details").forEach((details) =>
            details.removeAttribute("open")
          );
        } else {
          const hasVisibleLeafs =
            li.querySelectorAll(".display-block").length > 0;

          if (hasVisibleLeafs) {
            li.classList.remove("hidden");
            li.classList.add("display-block");
          } else {
            li.classList.add("hidden");
            li.classList.remove("display-block");
          }

          li.querySelectorAll("span.count").forEach((span) =>
            span.classList.add("hidden")
          );

          li.querySelectorAll(":scope > details").forEach((details) =>
            details.setAttribute("open", "")
          );
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    });
  },
  false
);
