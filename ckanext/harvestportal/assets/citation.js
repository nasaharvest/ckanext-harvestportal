/* Copy buttons in the dataset Cite dialog. Copies the citation's plain
   text, and its formatting (italic titles) where the browser supports it,
   so pasting into a word processor keeps the italics. */
(function () {
  "use strict";

  function flash(button, ok) {
    var label = button.querySelector("span");
    if (!label) return;
    var original = label.getAttribute("data-label") || label.textContent;
    label.setAttribute("data-label", original);
    label.textContent = ok ? "Copied" : "Copy failed";
    button.classList.toggle("is-copied", ok);
    window.setTimeout(function () {
      label.textContent = original;
      button.classList.remove("is-copied");
    }, 1800);
  }

  function copy(el) {
    var text = el.innerText.trim();
    var html = el.innerHTML.trim();
    if (navigator.clipboard && window.ClipboardItem && window.isSecureContext) {
      var item = new window.ClipboardItem({
        "text/plain": new Blob([text], { type: "text/plain" }),
        "text/html": new Blob([html], { type: "text/html" }),
      });
      return navigator.clipboard.write([item]).catch(function () {
        return navigator.clipboard.writeText(text);
      });
    }
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // Old browsers / plain http: select the text and use execCommand.
    return new Promise(function (resolve, reject) {
      var range = document.createRange();
      range.selectNodeContents(el);
      var selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      var ok = document.execCommand("copy");
      selection.removeAllRanges();
      ok ? resolve() : reject();
    });
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest("[data-cite-copy]");
    if (!button) return;
    var target = document.getElementById(button.getAttribute("data-cite-copy"));
    if (!target) return;
    copy(target).then(
      function () { flash(button, true); },
      function () { flash(button, false); }
    );
  });
})();
