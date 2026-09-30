# A3-UC-MiniLang

Este repositório contém a implementação de um compilador para a MiniLang, uma
linguagem imperativa pequena e didática, desenvolvido para a A3 de Teoria da
Computação e Compiladores (UNIFACS 2026.2). O projeto é construído em marcos
ao longo do semestre.

## Equipe:

Davi Floriano Hermida | 1272413195
Paulo Victor Nonato de Jesus | 12724129348
Alexandre Ribeiro Silva e Silva | 12724133597
Eraldino Ramos Albergaria Lopes | 12724123513

| Marco | Entrega                            | Situação    |
| ----- | ---------------------------------- | ----------- |
| M1    | Analisador léxico                  | ✅ concluído |
| M2    | Analisador sintático + AST         | ✅ concluído |
| M3    | Analisador semântico               | ✅ concluído |
| M4    | Back-end, relatório e apresentação | próximo     |

A extensão escolhida pela equipe para o projeto completo é a **Opção A (procedimentos sem retorno, com parâmetros por valor)**.

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+ (implementação manual do compilador, sem geradores de analisadores).
- **Bibliotecas:** apenas a biblioteca padrão (`enum`, `dataclasses`, `argparse`, `unittest`). Não é preciso instalar nada com `pip`.

## ⚙️ Instalação

```
git clone https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang.git
cd A3-UC-MiniLang
```

## ▶️ Execução do compilador (Léxico + Sintático + AST + Semântico)

Todos os comandos devem ser executados na raiz do repositório.

```
# Executa análise léxica, sintática e semântica completa
python -m minilang examples/valido.min

# Executa e imprime a Árvore Sintática Abstrata (AST)
python -m minilang examples/valido.min --ast

# Executa o exemplo da Opção A (procedimentos)
python -m minilang examples/procedimento.min --ast

# Imprime a tabela de símbolos (M3)
python -m minilang examples/procedimento.min --simbolos
```

A saída exibe a tabela de tokens léxicos, seguida da análise sintática e da análise semântica e, se houver erros (léxicos, sintáticos ou semânticos), reporta cada um com linha, coluna e descrição. A análise de cada etapa só roda se a anterior não tiver erros.

Código de saída: `0` sem erros, `1` com erros léxicos, sintáticos ou semânticos, `2` se o arquivo não puder ser lido.

### Exemplos

| Arquivo                                   | O que mostra                                                     |
| ----------------------------------------- | ---------------------------------------------------------------- |
| `examples/valido.min`                     | Programa completo com comandos e expressões sem erros            |
| `examples/procedimento.min`               | Extensão Opção A: procedimento com parâmetros e variáveis locais |
| `examples/operadores.min`                 | Todos os operadores aritméticos, relacionais e lógicos           |
| `examples/comentarios.min`                | Comentários descartados corretamente em várias posições          |
| `examples/erro_lexico.min`                | Erro léxico pontual (`@`) com linha e coluna                     |
| `examples/erros_multiplos.min`            | Múltiplos erros léxicos reportados em lote                       |
| `examples/erro_sintatico.min`             | Erro sintático pontual com linha e coluna                        |
| `examples/erros_sintaticos_multiplos.min` | Recuperação em modo pânico reportando múltiplos erros sintáticos |
| `examples/erro_semantico.min`             | Erro semântico pontual: atribuição de `booleano` a `inteiro`     |
| `examples/erros_semanticos_multiplos.min` | Vários erros semânticos reportados em lote (escopo, tipos, procedimentos) |

```
python -m minilang examples/procedimento.min --ast
python -m minilang examples/erro_sintatico.min
python -m minilang examples/erros_sintaticos_multiplos.min
python -m minilang examples/erro_semantico.min
python -m minilang examples/erros_semanticos_multiplos.min
```
> No Linux/macOS, use `python3` se `python` não apontar para o Python 3.

## ✅ Testes

```
python -m unittest discover -s tests
```

| Arquivo                               | O que cobre                                                                             |
| ------------------------------------- | --------------------------------------------------------------------------------------- |
| `tests/test_lexer.py`                 | Casos básicos do léxico: espaços, comentários, palavras reservadas e lookahead          |
| `tests/test_lexer_complemento.py`     | Todas as categorias de token da especificação                                           |
| `tests/test_lexer_erros_e_limites.py` | Mensagens de erro léxico, identificadores mal formados, acentos e casos limite          |
| `tests/test_exemplos_e_cli.py`        | Integração dos exemplos e linha de comando do compilador                                |
| `tests/test_parser.py`                | Análise sintática: EBNF, AST, precedência, associatividade, dangling else e modo pânico |
| `tests/test_semantic.py`              | Análise semântica: escopos, tipos, condições e procedimentos (Opção A)                  |

## 📚 Documentação

- [docs/entrega_m1.md](docs/entrega_m1.md) — especificações léxicas, expressões regulares, diagrama Mermaid e tabela de transição do AFD.
- [docs/nota_marco_m1.md](docs/nota_marco_m1.md) — nota de marco do M1 (escopo, decisões técnicas e divisão da equipe).
- [docs/entrega_m2.md](docs/entrega_m2.md) — especificações sintáticas, gramática EBNF, precedência, resolução do dangling else e AST.
- [docs/nota_marco_m2.md](docs/nota_marco_m2.md) — nota de marco do M2 (escopo, decisões de projeto e divisão da equipe).
- [docs/entrega_m3.md](docs/entrega_m3.md) — tabela de símbolos, regras de tipos e verificações da Opção A.
- [docs/nota_marco_m3.md](docs/nota_marco_m3.md) — nota de marco do M3 (escopo, decisões de projeto e divisão da equipe).

## 📁 Estrutura

```
A3-UC-MiniLang/
├── minilang/
│   ├── __init__.py      # pacote do compilador
│   ├── __main__.py      # linha de comando (python -m minilang)
│   ├── ast.py           # nós da árvore sintática abstrata e formatador
│   ├── lexer.py         # analisador léxico
│   ├── parser.py        # analisador sintático recursivo descendente
│   └── semantic.py      # analisador semântico e tabela de símbolos
├── examples/            # programas MiniLang de exemplo (.min)
├── tests/               # testes automatizados (unittest)
└── docs/                # documentação formal, AFD, gramática EBNF e notas de marco
```
