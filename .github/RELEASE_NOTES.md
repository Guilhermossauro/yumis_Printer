## O que mudou nesta versão

- 🐛 corrigido erro `ERR_CONNECTION_REFUSED` ao acessar o servidor pela rede local
- 🐛 corrigido carregamento da interface no executável compilado (`.exe`)
- ⚡ tamanho do `.exe` reduzido de 469 MB para ~42 MB — inicialização ~5× mais rápida
- 🔒 regra de firewall criada automaticamente ao iniciar o servidor (EXE standalone)
- 🛡️ instalador MSI cria regra de firewall na porta 8765 durante a instalação

---

## Como baixar e usar

**Opção 1 — Instalador (recomendado)**
1. Baixe `YumisPrinter-Setup-x64.msi` nos arquivos abaixo
2. Execute o instalador e siga os passos
3. Abra o atalho criado na Área de Trabalho ou no Menu Iniciar

**Opção 2 — Executável direto**
1. Baixe `YumisPrinter.exe` nos arquivos abaixo
2. Execute o arquivo diretamente — nenhuma instalação necessária
3. Na primeira vez que iniciar o servidor, autorize o acesso de rede quando solicitado pelo Windows

---

## Arquivos disponíveis

| Arquivo | Descrição |
|---|---|
| `YumisPrinter-Setup-x64.msi` | Instalador completo para Windows (recomendado) |
| `YumisPrinter.exe` | Executável portátil, sem instalação |
| `YumisPrinter-win64.zip` | Versão compactada do executável |
| `SHA256SUMS.txt` | Checksums para verificação de integridade |
