# Yumis' Printer

**Compartilhamento inteligente de impressoras em rede local.**

Uma solução simples, elegante e prática para quem precisa imprimir em rede sem complicação.

---

## ✨ Sobre o Projeto

Yumis' Printer resolve um problema clássico: **configurar impressora na rede toda vez que alguém precisa imprimir**.

Em vez de instalar a impressora em cada computador, ajustar compartilhamentos manuais ou depender de suporte técnico, você instala o programa **apenas no computador host** (aquele que tem as impressoras físicas conectadas), seleciona quais impressoras deseja compartilhar e pronto.

Qualquer pessoa na mesma rede local pode acessar pelo navegador, enviar o arquivo e imprimir de forma rápida e visual.

---

## 🚀 Principais Recursos

- Detecção automática de impressoras locais e de rede
- Interface moderna e intuitiva (estilo Microsoft Fluent)
- Seleção fácil de quais impressoras serão compartilhadas
- Controle de ligar/desligar o servidor local
- Acesso via navegador para todos os usuários da rede
- Pré-visualização do documento antes de imprimir
- Suporte a PDF e imagens (PNG, JPG, JPEG, WEBP, BMP)
- Fila de impressão organizada
- Interface limpa tanto para o host quanto para os usuários finais

---

## 🎯 Para quem é ideal?

- Escritórios e pequenas empresas
- Recepções e atendimentos
- Escolas e laboratórios
- Lojas e operações comerciais
- Ambientes com múltiplos computadores compartilhando poucas impressoras
- Qualquer lugar onde configurar impressora em cada máquina é um problema

---

## Como funciona

### 1. No computador Host (onde estão as impressoras)
1. Baixe e execute o Yumis' Printer
2. O programa detecta automaticamente todas as impressoras
3. Marque com checkbox quais impressoras deseja liberar
4. Clique em **Iniciar Servidor**
5. Copie o endereço local exibido (ex: `http://192.168.1.100:5000`)

### 2. Nos outros computadores da rede
1. Abra o navegador e acesse o endereço fornecido
2. Faça upload do PDF ou imagem
3. Visualize o documento
4. Escolha a impressora e o número de cópias
5. Clique em **Imprimir agora**

Pronto. Simples assim.

---

## 🛠️ Tecnologias Utilizadas

- **Python + Flask** — Backend leve e eficiente
- **PyWin32** — Integração nativa com impressoras Windows
- **HTML + CSS + JavaScript** — Interface moderna com design Fluent
- **Tailwind / Custom CSS** — Estilo profissional e responsivo

---

## 📥 Como usar

1. Baixe a versão mais recente em **[Releases](https://github.com/Guilhermossauro/Yumis-Printer/releases)**
2. Extraia o arquivo
3. Execute `Yumis' Printer.exe` (Windows)
4. Permita o acesso na janela do Windows Firewall (se solicitado)
5. Selecione as impressoras e inicie o servidor

> **Dica:** Recomendamos fixar o programa na barra de tarefas do host para facilitar o uso diário.

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Se você quiser melhorar a interface, adicionar suporte a mais formatos, implementar autenticação simples ou qualquer outra funcionalidade, fique à vontade para abrir uma Issue ou Pull Request.

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** — veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## ⭐ Apoie o projeto

Se o Yumis' Printer está te ajudando a economizar tempo e simplificar a impressão na sua empresa ou casa, considere:

- Dar uma estrela ⭐ no repositório
- Compartilhar com quem possa precisar

---

**Feito com foco em simplicidade e praticidade.**

Torne o compartilhamento de impressoras algo **natural** novamente.

---

<div align="center">
  <strong>Yumis' Printer</strong> • Impressão em rede sem dor de cabeça
</div>
