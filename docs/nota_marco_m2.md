# Nota de marco — M2: Analisador Sintático e AST

**Equipe:**
Davi Floriano Hermida | 1272413195
Paulo Victor Nonato de Jesus | 12724129348
Alexandre Ribeiro Silva e Silva | 12724133597
Eraldino Ramos Albergaria Lopes | 12724123513

**Repositório:** https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang  
**Extensão escolhida:** Opção A — procedimentos sem retorno, com parâmetros por valor  

## O que foi entregue

- Analisador sintático recursivo descendente manual em Python ([`minilang/parser.py`](../minilang/parser.py)).
- Árvore Sintática Abstrata (AST) navegável com nós em `@dataclass` e impressor hierárquico ([`minilang/ast.py`](../minilang/ast.py)).
- Suporte à sintaxe da **Opção A** (declaração de procedimentos `procedimento nome(...) { ... }` e chamada `nome(...);`).
- Precedência e associatividade de operadores rigorosamente implementadas nas expressões.
- Resolução e documentação do problema do *dangling else*.
- Recuperação de erros sintáticos em **modo pânico** com sincronização, reportando múltiplos erros em uma única execução com linha e coluna.
- Linha de comando com flag `--ast` para exibição e inspeção da árvore sintática.
- Suíte de testes automatizados para o parser em [`tests/test_parser.py`](../tests/test_parser.py).
- Programas de exemplo para procedimentos e erros sintáticos em [`examples/`](../examples/).
- Especificação formal da gramática em EBNF em [`docs/entrega_m2.md`](entrega_m2.md).

## Principais decisões de projeto

- **Implementação manual por descida recursiva**, dispensando geradores automáticos para manter clareza pedagógica e facilidade de depuração.
- **AST rica e tipada:** cada construção da linguagem possui seu nó específico com metadados de linha e coluna.
- **Chaves obrigatórias:** a sintaxe exige `{` e `}` para blocos de comandos, eliminando a ambiguidade clássica do *dangling else*.
- **Modo pânico seletivo:** o parser avança até delimitadores de instrução (`;`, `}`) ou palavras-chave para recuperar o fluxo de análise e listar todos os erros do arquivo.

## Limitações conhecidas

- A checagem de tipos (ex.: somar inteiro com booleano) e a validação de declaração prévia de variáveis e escopos serão tratadas no Marco 3 (Analisador Semântico).

## Uso de IA generativa

Foi utilizado auxílio de IA generativa para acelerar a estruturação dos casos de teste do analisador sintático e formalização da gramática EBNF. Todos os integrantes da equipe revisaram a implementação e dominam as decisões arquiteturais adotadas.
