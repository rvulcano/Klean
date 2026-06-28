<<<<<<< HEAD
# Klean 🧹

**Klean** é um utilitário de manutenção de sistema minimalista, seguro e transparente, projetado para otimizar o desempenho do Windows. A missão do Klean é devolver o controle e o espaço ao usuário, removendo arquivos inúteis e corrigindo erros comuns do sistema de forma rápida e segura.

---

## 🚀 Funcionalidades

- **Limpeza Profunda:** Remoção de arquivos temporários (`Temp`, `Prefetch`), logs do sistema e cache de downloads do Windows Update.
- **Otimização de Navegadores:** Limpeza inteligente de caches de navegadores populares (Chrome, Edge, Vivaldi, etc.).
- **Limpeza de Registro:** Remoção segura de entradas obsoletas (MuiCache, RunMRU, RecentDocs).
- **Reparo de Sistema:** Ferramentas nativas integradas para correção de erros de rede (DNS, Winsock) e reparo de integridade (SFC, DISM).
- **Transparência Total:** Código aberto. Você sabe exatamente o que o programa está fazendo no seu computador.

---

## 🛠️ Como Usar

Você pode rodar o Klean de duas formas:

### 1. Interface Interativa
Basta dar um clique duplo no `Agente_Otimizador.exe` e seguir o menu numerado no terminal.

### 2. Modo Comando (CLI)
Para automação, abra o terminal e use os argumentos:

| Comando | Descrição |
| :--- | :--- |
| `limpar --tudo` | Executa todas as limpezas e correções. |
| `limpar --temp` | Limpa apenas arquivos temporários e caches. |
| `limpar --registro` | Limpa apenas registros e históricos. |
| `limpar --reparar` | Roda as ferramentas de reparo (SFC, DISM, Rede). |
| `limpar --lixeira` | Esvazia a lixeira silenciosamente. |

> **Nota:** Para que as limpezas profundas funcionem, o programa solicitará privilégios de Administrador.

---

## 🏗️ Como Compilar

O Klean é compilado como um binário nativo usando o [Nuitka](https://nuitka.net/) para garantir performance e evitar falsos positivos de antivírus.

Para compilar na sua máquina:

1. Instale o Nuitka: `pip install nuitka`
2. Compile o código:
   ```bash
   python -m nuitka --onefile --assume-yes-for-downloads --windows-icon-from-ico="icone.ico" limpar.py
   ```

---

## 🛡️ Segurança e Transparência

O Klean não coleta dados, não possui telemetria e seu código está disponível para auditoria completa. A detecção de antivírus como "falso positivo" é comum em utilitários de sistema compilados. Se você confiar no projeto, adicione o executável à lista de exceções do seu antivírus.

---

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma *Issue* ou enviar um *Pull Request* para melhorar as funcionalidades do Klean.

---

*Desenvolvido com simplicidade e foco em performance.*
=======
# Klean
Utilitário de código aberto para otimização, limpeza e reparo do Windows de forma segura.
>>>>>>> 2932eb4415cef2470eae00237c8ccf2ede118d4e
