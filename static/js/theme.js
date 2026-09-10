(function () {
  "use strict";

  const CHAVE = "analisador-commits:tema";

  function temaPreferido() {
    const salvo = localStorage.getItem(CHAVE);
    if (salvo === "light" || salvo === "dark") {
      return salvo;
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  function aplicarTema(tema) {
    document.documentElement.setAttribute("data-bs-theme", tema);
  }

  aplicarTema(temaPreferido());

  window.addEventListener("DOMContentLoaded", () => {
    const botao = document.getElementById("botao-tema");
    if (!botao) {
      return;
    }
    botao.addEventListener("click", () => {
      const atual = document.documentElement.getAttribute("data-bs-theme");
      const proximo = atual === "dark" ? "light" : "dark";
      aplicarTema(proximo);
      localStorage.setItem(CHAVE, proximo);
    });
  });
})();
