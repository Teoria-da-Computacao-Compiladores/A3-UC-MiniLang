# A3-UC-MiniLang

Este repositório contém a implementação de um compilador para a MiniLang, uma
linguagem imperativa pequena e didática, desenvolvido para a A3 de Teoria da
Computação e Compiladores (UNIFACS 2026.2). O projeto é construído em marcos
ao longo do semestre.

| Marco | Entrega | Situação |
|---|---|---|
| M1 | Analisador léxico | ✅ concluído |
| M2 | Analisador sintático + AST | próximo |
| M3 | Analisador semântico | — |
| M4 | Back-end, relatório e apresentação | — |

A extensão escolhida pela equipe para o projeto completo é a
**Opção A (procedimentos sem retorno, com parâmetros por valor)**.

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+ (implementação manual do compilador, sem geradores de analisadores).
- **Bibliotecas:** apenas a biblioteca padrão (`enum`, `dataclasses`, `argparse`, `unittest`). Não é preciso instalar nada com `pip`.

## ⚙️ Instalação

```bash
git clone https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang.git
cd A3-UC-MiniLang
```

## ▶️ Execução do analisador léxico

Todos os comandos devem ser executados na raiz do repositório.

```bash
python -m minilang examples/valido.min
```

A saída é a tabela de tokens (linha, coluna, tipo e lexema), seguida da lista
de erros léxicos, se houver:

```
Analisando: examples/erro_lexico.min

Tokens gerados:
Linha  Coluna  Tipo            Lexema
--------------------------------------------------
1      1       PROGRAMA        programa
...
7      12      ERRO            @
...

1 erro(s) léxico(s) encontrado(s):
  Erro léxico [linha 7, coluna 12]: caractere inválido '@'
```

Código de saída: `0` sem erros, `1` com erros léxicos, `2` se o arquivo não
puder ser lido.

### Exemplos

| Arquivo | O que mostra |
|---|---|
| `examples/valido.min` | Programa completo sem erros |
| `examples/operadores.min` | Todos os operadores, incluindo o lookahead |
| `examples/comentarios.min` | Comentários em linha própria, no fim da linha e na última linha |
| `examples/erro_lexico.min` | Um erro léxico (`@`) com linha e coluna |
| `examples/erros_multiplos.min` | Vários erros léxicos reportados em uma única execução |

```bash
python -m minilang examples/operadores.min
python -m minilang examples/comentarios.min
python -m minilang examples/erro_lexico.min
python -m minilang examples/erros_multiplos.min
```

> No Linux/macOS, use `python3` se `python` não apontar para o Python 3.

## ✅ Testes

```bash
python -m unittest discover -s tests
```

| Arquivo | O que cobre |
|---|---|
| `tests/test_lexer.py` | Casos básicos: espaços, comentários, palavras reservadas, números, lookahead e erro |
| `tests/test_lexer_complemento.py` | Todas as categorias de token da especificação |
| `tests/test_lexer_erros_e_limites.py` | Mensagens de erro, números e identificadores mal formados, alfabeto, recursão, `\r\n` e tabulação |
| `tests/test_exemplos_e_cli.py` | Arquivos de `examples/` e a linha de comando |

## 📚 Documentação

- [docs/entrega_m1.md](docs/entrega_m1.md) — expressões regulares, diagrama e tabela de transição do AFD.
- [docs/Analisador Léxico_detalhes.md](<docs/Analisador Léxico_detalhes.md>) — descrição do lexer em linguagem natural.
- [docs/nota_marco_m1.md](docs/nota_marco_m1.md) — nota de marco do M1.
- [docs/mudancas_m1.md](docs/mudancas_m1.md) — o que mudou nos ajustes do M1 e como cada parte do código funciona.

## 📁 Estrutura

```
A3-UC-MiniLang/
├── minilang/
│   ├── __init__.py      # pacote do compilador
│   ├── __main__.py      # linha de comando (python -m minilang)
│   └── lexer.py         # analisador léxico
├── examples/            # programas MiniLang de exemplo
├── tests/               # testes automatizados (unittest)
└── docs/                # especificação do AFD, notas de marco e explicações
```
