const form = document.getElementById("form-analise");
const botao = document.getElementById("botao-analisar");
const estado = document.getElementById("estado-carga");

if (form && botao && estado) {
  form.addEventListener("submit", () => {
    if (!form.checkValidity()) {
      return;
    }
    estado.hidden = false;
    botao.disabled = true;
  });
}
