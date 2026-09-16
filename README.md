# A3-UC-MiniLang
Este repositório contém a implementação de um compilador para a MiniLang, uma linguagem imperativa pequena e didática. O projeto está sendo desenvolvido progressivamente ao longo do semestre de 2026.2.

A extensão escolhida pela equipe para o projeto completo é a:
**Opção A (Procedimentos sem retorno, com parâmetros por valor)**.

## 🛠️ Tecnologias e Versão da Linguagem
- **Linguagem:** Python 3.10+ (Implementação manual do compilador).
- **Bibliotecas:** Apenas bibliotecas nativas (`enum`, `dataclasses`, `unittest`), sem dependências externas.

## ⚙️ Instalação
Como o projeto utiliza apenas bibliotecas nativas do Python, nenhuma configuração oculta ou instalação de pacotes externos (via `pip`) é necessária.

## Clone o repositório:
   git clone [https://github.com/SEU_USUARIO/minilang-compiler.git](https://github.com/SEU_USUARIO/minilang-compiler.git)
   cd minilang-compiler

## Execução do Analisador Léxico
   python minilang/lexer.py

## Execução dos Testes
   python -m unittest tests/test_lexer.py
   
   python3 -m unittest tests.test_lexer_complemento


## Execução no Terminal dos Exemplos
   python minilang/lexer.py examples/valido.min
   
   python3 minilang/lexer.py examples/operadores.min

   python3 minilang/lexer.py examples/comentarios.min

   python3 minilang/lexer.py examples/erro_lexico.min
