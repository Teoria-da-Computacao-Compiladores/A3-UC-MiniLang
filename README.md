# A3-UC-MiniLang

Este repositório contém a implementação completa de um compilador para a **MiniLang**, uma
linguagem imperativa pequena e didática, desenvolvido para a A3 de Teoria da
Computação e Compiladores (UNIFACS 2026.2). O projeto foi construído progressivamente em marcos
ao longo do semestre, cobrindo todo o pipeline de compilação: léxico, sintático, semântico, otimização e execução.

## Equipe:

- Davi Floriano Hermida | 1272413195
- Paulo Victor Nonato de Jesus | 12724129348
- Alexandre Ribeiro Silva e Silva | 12724133597
- Eraldino Ramos Albergaria Lopes | 12724123513

| Marco | Entrega | Situação |
| :---: | :--- | :---: |
| **M1** | Analisador léxico (AFD manual e tokens com linha/coluna) | ✅ concluído |
| **M2** | Analisador sintático (EBNF, precedência, dangling else e AST) | ✅ concluído |
| **M3** | Analisador semântico (tabela de símbolos, escopos, tipos e AST anotada) | ✅ concluído |
| **M4** | Back-end (interpretador com pilha de ativação), otimizador e relatório final | ✅ concluído |

A extensão escolhida e implementada integralmente pela equipe é a **Opção A (procedimentos sem retorno, com parâmetros por valor e escopo local aninhado)**.

---

## 🛠️ Tecnologias

- **Linguagem:** Python 3.10+ (implementação 100% manual, sem uso de geradores automáticos como Lex/Yacc, ANTLR ou PLY).
- **Bibliotecas:** apenas a biblioteca padrão (`enum`, `dataclasses`, `argparse`, `unittest`). Nenhuma dependência externa via `pip` é necessária para rodar o compilador ou os testes.

---

## ⚙️ Instalação

```bash
git clone https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang.git
cd A3-UC-MiniLang
```

---

## ▶️ Execução do Compilador (M1 a M4)

Todos os comandos devem ser executados na raiz do repositório:

```bash
# Análise completa (Léxico + Sintático + Semântico)
python -m minilang examples/valido.min

# Executa o programa interpretando a AST (M4)
python -m minilang examples/fatorial.min --executar

# Executa com otimizações aplicadas e exibe o relatório de transformações (M4)
python -m minilang examples/otimizacao.min --otimizar --executar

# Exibe a Árvore Sintática Abstrata (AST) anotada com os tipos inferidos (M3/M4)
python -m minilang examples/procedimento.min --ast

# Exibe a tabela de símbolos e seus escopos aninhados (M3)
python -m minilang examples/procedimento.min --simbolos

# Oculta a tabela de tokens léxicos para saída limpa em apresentações
python -m minilang examples/fatorial.min --sem-tokens --executar
```

### Códigos de Saída (Exit Codes)

| Código | Significado |
| :---: | :--- |
| `0` | Sucesso absoluto em todas as etapas executadas |
| `1` | Erro de compilação (léxico, sintático ou semântico) |
| `2` | Erro de leitura de arquivo (não encontrado / ilegível) ou uso incorreto da CLI |
| `3` | Erro em tempo de execução (divisão por zero, entrada inválida, estouro de pilha) |

---

## 📁 Exemplos Demonstrativos

| Arquivo | O que demonstra | Comando sugerido |
| :--- | :--- | :--- |
| `examples/fatorial.min` | Laço `enquanto` + procedimento com variáveis locais (M4) | `python -m minilang examples/fatorial.min --executar` |
| `examples/recursao.min` | Recursão com pilha de ativação dinâmica — profundidade 11 (M4/Opção A) | `python -m minilang examples/recursao.min --executar` |
| `examples/escopo_e_valor.min` | Passagem por valor e sombreamento de variável global (M4/Opção A) | `python -m minilang examples/escopo_e_valor.min --executar` |
| `examples/otimizacao.min` | Dobramento de constantes, simplificação algébrica e poda de código morto (M4) | `python -m minilang examples/otimizacao.min --otimizar --executar --ast` |
| `examples/entrada.min` | Comando `leia()` recebendo dados via entrada padrão (M4) | `"7","12" \| python -m minilang examples/entrada.min --executar` |
| `examples/procedimento.min` | Extensão Opção A: procedimento com múltiplos parâmetros (M2/M3) | `python -m minilang examples/procedimento.min --ast --simbolos` |
| `examples/valido.min` | Programa completo clássico sem erros | `python -m minilang examples/valido.min --executar` |
| `examples/erro_execucao.min` | Erro em tempo de execução (divisão por zero) com exit code 3 | `python -m minilang examples/erro_execucao.min --executar` |
| `examples/erro_semantico.min` | Atribuição incompatível (`booleano` para `inteiro`) | `python -m minilang examples/erro_semantico.min` |
| `examples/erros_semanticos_multiplos.min` | Múltiplos erros semânticos reportados sem efeito avalanche | `python -m minilang examples/erros_semanticos_multiplos.min` |
| `examples/erro_sintatico.min` | Erro sintático pontual com linha e coluna | `python -m minilang examples/erro_sintatico.min` |
| `examples/erros_sintaticos_multiplos.min` | Recuperação sintática em modo pânico | `python -m minilang examples/erros_sintaticos_multiplos.min` |
| `examples/erro_lexico.min` | Caractere inválido (`@`) | `python -m minilang examples/erro_lexico.min` |
| `examples/erros_multiplos.min` | Múltiplos erros léxicos acumulados | `python -m minilang examples/erros_multiplos.min` |

---

## ✅ Testes Automatizados (216 Testes)

Para rodar toda a suíte de testes do compilador:

```bash
python -m unittest discover -s tests
```

| Arquivo de Teste | Fase | Qtd | Cobertura |
| :--- | :---: | :---: | :--- |
| `tests/test_lexer.py` | M1 | 5 | Casos básicos do léxico: espaços, comentários e lookahead |
| `tests/test_lexer_complemento.py` | M1 | 15 | Todas as categorias de tokens da especificação |
| `tests/test_lexer_erros_e_limites.py` | M1 | 23 | Mensagens de erro léxico, `12abc`, acentos e limites de recursão |
| `tests/test_exemplos_e_cli.py` | M1/M2 | 12 | Integração dos exemplos de M1/M2 e comandos CLI |
| `tests/test_parser.py` | M2 | 15 | Gramática EBNF, precedência, associatividade, dangling else e modo pânico |
| `tests/test_semantic.py` | M3 | 36 | Escopos, tipos, condições e procedimentos (Opção A) |
| `tests/test_anotacao_ast.py` | M3 | 10 | Anotação de tipos inferidos na AST e formatação visual |
| `tests/test_interpreter.py` | M4 | 39 | Execução sobre a AST, truncamento, curto-circuito, pilha de ativação e erros de runtime |
| `tests/test_optimizer.py` | M4 | 43 | Dobramento de constantes, simplificação algébrica, código morto e equivalência semântica |
| `tests/test_backend_cli.py` | M4 | 18 | Flags `--executar`, `--otimizar`, entrada padrão e exit codes 0, 1, 2 e 3 |

---

## 📚 Documentação e Entregáveis

- [docs/relatorio_final.pdf](docs/relatorio_final.pdf) — **Relatório Técnico Final oficial (8 páginas)** com arquitetura, decisões, gramática EBNF, AFD, otimizações e declaração de IA.
- [docs/roteiro_apresentacao.md](docs/roteiro_apresentacao.md) — Roteiro completo de 15 minutos com comandos prontos para a apresentação e possíveis perguntas da arguição.
- [docs/entrega_m1.md](docs/entrega_m1.md) e [docs/nota_marco_m1.md](docs/nota_marco_m1.md) — Especificações e nota do Marco 1 (Léxico / AFD).
- [docs/entrega_m2.md](docs/entrega_m2.md) e [docs/nota_marco_m2.md](docs/nota_marco_m2.md) — Especificações e nota do Marco 2 (Sintático / EBNF / AST).
- [docs/entrega_m3.md](docs/entrega_m3.md) e [docs/nota_marco_m3.md](docs/nota_marco_m3.md) — Especificações e nota do Marco 3 (Semântico / Tipos / Tabela de Símbolos).
- [docs/entrega_m4.md](docs/entrega_m4.md) e [docs/nota_marco_m4.md](docs/nota_marco_m4.md) — Especificações e nota do Marco 4 (Back-end / Otimizador / Execução).

---

## 📁 Estrutura do Código

```
A3-UC-MiniLang/
├── minilang/
│   ├── __init__.py        # Pacote e exportações da API pública
│   ├── __main__.py        # Ponto de entrada CLI (python -m minilang)
│   ├── ast.py             # Definição dos nós da AST com tipo_inferido
│   ├── lexer.py           # Analisador léxico manual baseado em AFD
│   ├── parser.py          # Analisador sintático preditivo recursivo descendente
│   ├── semantic.py        # Analisador semântico e tabela de símbolos
│   ├── optimizer.py       # Otimizador AST->AST (dobramento, algébrica, código morto)
│   └── interpreter.py     # Back-end: interpretador com pilha de ativação
├── examples/              # Programas MiniLang de teste e demonstração (.min)
├── tests/                 # Suíte completa de 216 testes automatizados (unittest)
└── docs/                  # Relatório técnico final, notas de marco e especificações
```
