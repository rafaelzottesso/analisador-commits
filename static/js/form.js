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

const campoUrl = document.getElementById("url");
const campoUsuario = document.getElementById("gh-usuario");
const campoRepo = document.getElementById("gh-repo");
const botaoPreencher = document.getElementById("botao-preencher");
const preview = document.getElementById("preview-url");

function montarUrl(usuario, repo) {
  const u = usuario.trim().replace(/^\/+|\/+$/g, "");
  const r = repo.trim().replace(/^\/+|\/+$/g, "");
  if (!u || !r) {
    return null;
  }
  return `https://github.com/${u}/${r}`;
}

function atualizarPreview() {
  if (!preview) {
    return;
  }
  const montada = montarUrl(campoUsuario.value || "", campoRepo.value || "");
  preview.textContent = montada || "https://github.com/usuario/repositorio";
}

if (campoUsuario && campoRepo && botaoPreencher && campoUrl) {
  campoUsuario.addEventListener("input", atualizarPreview);
  campoRepo.addEventListener("input", atualizarPreview);

  botaoPreencher.addEventListener("click", () => {
    const montada = montarUrl(campoUsuario.value || "", campoRepo.value || "");
    if (!montada) {
      campoUsuario.reportValidity?.();
      return;
    }
    campoUrl.value = montada;
    campoUrl.focus();
  });
}
