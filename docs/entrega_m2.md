# M2 — Especificação Sintática, Gramática EBNF e AST da MiniLang

Este documento descreve formalmente o **Analisador Sintático** e a **Árvore Sintática Abstrata (AST)** implementados no Marco 2 (M2) em [`minilang/parser.py`](../minilang/parser.py) e [`minilang/ast.py`](../minilang/ast.py), cobrindo a gramática livre de contexto (EBNF), precedência e associatividade de operadores, resolução do *dangling else*, estrutura da AST e recuperação de erros em modo pânico.

---

## 1. Gramática Livre de Contexto em EBNF (com Extensão Opção A)

A gramática abaixo define a sintaxe formal aceita pelo compilador, contemplando a especificação básica e a **Opção A** (Procedimentos sem retorno com parâmetros por valor):

```ebnf
Programa          ::= "programa" IDENTIFICADOR "{" Bloco "}" "fim" "."
Bloco             ::= { DeclaracaoVar | DeclaracaoProc } { Comando }

DeclaracaoVar     ::= "var" IDENTIFICADOR ":" Tipo ";"
Tipo              ::= "inteiro" | "booleano"

DeclaracaoProc    ::= "procedimento" IDENTIFICADOR "(" [ ListaParams ] ")" "{" BlocoProc "}"
ListaParams       ::= Parametro { "," Parametro }
Parametro         ::= IDENTIFICADOR ":" Tipo
BlocoProc         ::= { DeclaracaoVar } { Comando }

Comando           ::= Atribuicao
                    | ChamadaProc
                    | Condicional
                    | Repeticao
                    | Leitura
                    | Escrita

Atribuicao        ::= IDENTIFICADOR "=" Expressao ";"
ChamadaProc       ::= IDENTIFICADOR "(" [ ListaArgs ] ")" ";"
ListaArgs         ::= Expressao { "," Expressao }

Condicional       ::= "se" "(" Expressao ")" "{" { Comando } "}" [ "senão" "{" { Comando } "}" ]
Repeticao         ::= "enquanto" "(" Expressao ")" "{" { Comando } "}"
Leitura           ::= "leia" "(" IDENTIFICADOR ")" ";"
Escrita           ::= "escreva" "(" Expressao ")" ";"

Expressao         ::= ExpOu
ExpOu             ::= ExpE { "ou" ExpE }
ExpE              ::= ExpRel { "e" ExpRel }
ExpRel            ::= ExpAdit [ OpRelacional ExpAdit ]
OpRelacional      ::= "==" | "!=" | "<" | "<=" | ">" | ">="
ExpAdit           ::= ExpMult { ( "+" | "-" ) ExpMult }
ExpMult           ::= ExpUnaria { ( "*" | "/" | "%" ) ExpUnaria }
ExpUnaria         ::= [ "não" | "-" ] ExpPrimaria
ExpPrimaria       ::= NUMERO | "verdadeiro" | "falso" | IDENTIFICADOR | "(" Expressao ")"
```

---

## 2. Precedência e Associatividade de Operadores

A descida recursiva no analisador sintático reflete exatamente os níveis de precedência formal, garantindo que operações de maior prioridade sejam avaliadas antes:

| Nível (1 = mais baixo) | Categoria | Operadores | Associatividade | Método no Parser |
|:---:|:---:|:---:|:---:|:---:|
| **1** (mais baixo) | Lógico Disjuntivo | `ou` | À esquerda | `_exp_ou()` |
| **2** | Lógico Conjuntivo | `e` | À esquerda | `_exp_e()` |
| **3** | Relacional | `==`, `!=`, `<`, `<=`, `>`, `>=` | Não-associativo | `_exp_relacional()` |
| **4** | Aditivo | `+`, `-` | À esquerda | `_exp_aditiva()` |
| **5** | Multiplicativo | `*`, `/`, `%` | À esquerda | `_exp_multiplicativa()` |
| **6** | Unário | `não`, `-` (aritmético) | Prefixo / À direita | `_exp_unaria()` |
| **7** (mais alto) | Primário | Literais, variáveis, `(...)` | — | `_exp_primaria()` |

*Exemplo de ordenação garantida pela AST:*  
Na expressão `2 + 3 * 4`, a AST gera `BinaryOpNode("+", 2, BinaryOpNode("*", 3, 4))`, avaliando a multiplicação antes da soma.

---

## 3. Resolução do Problema do *Dangling Else*

O clássico problema da ambiguidade do `else` suspenso (*dangling else*) ocorre quando estruturas condicionais aninhadas possuem um ramo `else` que poderia sintaticamente pertencer tanto ao `se` externo quanto ao `se` interno:

```text
se (A)
    se (B)
        comando1;
    senão
        comando2;
```

### Solução Adotada na MiniLang:
1. **Delimitação Explícita por Chaves Obligatórias:** A gramática da MiniLang exige blocos delimitados por `{` e `}` tanto no ramo `se` quanto no ramo `senão`. Isso elimina a ambiguidade no nível léxico-estrutural.
2. **Resolução no Parser:** Na implementação recursiva descendente de `_condicional()`, a cláusula `senão` é verificada imediatamente após o fechamento do bloco `}` do `se` correspondente. Caso haja um `senão`, ele é vinculado obrigatoriamente ao `se` mais interno ativo no escopo daquele bloco.

---

## 4. Estrutura da Árvore Sintática Abstrata (AST)

A AST é implementada através de classes `@dataclass` em [`minilang/ast.py`](../minilang/ast.py):

* **Raiz do Programa:** `ProgramNode(nome, declaracoes, comandos, linha, coluna)`
* **Declarações:**
  * `VarDeclNode(nome, tipo, linha, coluna)`
  * `ProcedureDeclNode(nome, parametros, declaracoes, comandos, linha, coluna)`
  * `ParamNode(nome, tipo, linha, coluna)`
* **Comandos:**
  * `AssignStmtNode(identificador, expressao, linha, coluna)`
  * `CallStmtNode(identificador, argumentos, linha, coluna)`
  * `IfStmtNode(condicao, entao_comandos, senao_comandos, linha, coluna)`
  * `WhileStmtNode(condicao, comandos, linha, coluna)`
  * `ReadStmtNode(identificador, linha, coluna)`
  * `WriteStmtNode(expressao, linha, coluna)`
* **Expressões:**
  * `BinaryOpNode(esquerda, operador, direita, linha, coluna)`
  * `UnaryOpNode(operador, operando, linha, coluna)`
  * `LiteralNode(valor, tipo, linha, coluna)`
  * `VarAccessNode(nome, linha, coluna)`

A função `formatar_ast(no)` produz uma exibição textual hierárquica e indentada, permitindo a inspeção visual completa da estrutura construída.

---

## 5. Estratégia de Recuperação de Erros (Modo Pânico)

Para não interromper o compilador no primeiro erro sintático encontrado, o parser implementa o **Modo Pânico com Sincronização**:

1. Ao encontrar uma construção malformada ou a ausência de um token esperado (ex: falta de `;` ou `)`), o método `_consumir()` registra a ocorrência em `self.erros` contendo linha, coluna e descrição clara, e levanta uma exceção interna `_ParseError`.
2. O laço de controle do bloco captura a exceção e aciona o método `_sincronizar()`.
3. O cursor descarta tokens até encontrar um **token de sincronização seguro**:
   * Ponto e vírgula (`;`): consumido para reiniciar no comando seguinte.
   * Fechamento de bloco (`}`): encerra o escopo atual com segurança.
   * Palavras-chave de início de declaração ou comando (`var`, `procedimento`, `se`, `senão`, `enquanto`, `escreva`, `leia`, `fim`).
4. Essa recuperação permite que erros independentes sejam acumulados e exibidos juntos em uma única execução.

---

## 6. Correspondência entre Regras Gramaticais e Métodos do Código

| Regra Gramatical | Método em `minilang/parser.py` |
|---|---|
| Programa | `_programa()` |
| Declarações (Variáveis e Procedimentos) | `_declaracoes()`, `_declaracao_var()`, `_declaracao_procedimento()` |
| Parâmetros formais | `_parametros()`, `_parametro()` |
| Lista de Comandos | `_comandos()`, `_comando()` |
| Atribuição e Chamada de Procedimento | `_atribuicao_ou_chamada()` |
| Condicional (`se` / `senão`) | `_condicional()` |
| Repetição (`enquanto`) | `_repeticao()` |
| Entrada e Saída | `_leitura()`, `_escrita()` |
| Expressões e Precedência | `_expressao()`, `_exp_ou()`, `_exp_e()`, `_exp_relacional()`, `_exp_aditiva()`, `_exp_multiplicativa()`, `_exp_unaria()`, `_exp_primaria()` |
| Recuperação em Modo Pânico | `_sincronizar()` |
