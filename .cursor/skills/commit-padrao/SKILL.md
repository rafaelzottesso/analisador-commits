---
name: commit-padrao
description: Use sempre que for escrever a mensagem de um commit neste projeto — gera mensagens no padrão Conventional Commits, com resumo no imperativo e um corpo curto que descreve o que foi implementado, nunca apenas um rótulo genérico como "fix" ou "ajustes".
allowed-tools: Bash(git diff *), Bash(git status *), Bash(git log *)
---

## Mudanças pendentes

!`git diff --cached`

## Instruções

Escreva a mensagem de commit para o diff acima seguindo estas regras, sem exceção:

1. **Primeira linha**: `tipo(escopo): resumo no imperativo`, até 72 caracteres, sem ponto
   final. Tipos válidos: feat, fix, docs, style, refactor, perf, test, build, ci, chore.
2. **Linha em branco** depois do resumo.
3. **Corpo obrigatório se o diff tocar mais de um arquivo ou passar de ~15 linhas**:
   2 a 5 linhas (ou bullets) descrevendo em termos concretos o que foi implementado —
   nomeie a função, o modelo, a rota ou o comportamento que mudou. Nunca escreva
   "ajustes diversos", "melhorias" ou repita o resumo com outras palavras.
4. Se o diff misturar mudanças sem relação entre si, não invente uma mensagem que
   cubra as duas — avise o usuário e sugira separar em dois commits.
5. Nunca descreva algo que não está no diff mostrado acima.
6. Se o diff estiver vazio, informe que não há mudanças staged (sugira `git add`)
   em vez de gerar uma mensagem genérica.
