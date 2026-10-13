# M3 — Análise Semântica da MiniLang

Este documento descreve o **Analisador Semântico** implementado no Marco 3 (M3) em
[`minilang/semantic.py`](../minilang/semantic.py). Ele percorre a AST gerada no M2 e verifica
declaração de identificadores, escopos, compatibilidade de tipos e, pela **Opção A**, a declaração
e a chamada de procedimentos sem retorno com parâmetros por valor.

O pipeline completo é: **Léxico (M1) → Sintático + AST (M2) → Semântico (M3)**. A análise semântica
só roda se não houver erros léxicos nem sintáticos.

---

## 1. Tabela de símbolos e escopos

A tabela é uma **pilha de escopos** (`TabelaSimbolos`). Cada escopo mapeia nome → `Simbolo`.

| Escopo | Criado em | Contém |
|---|---|---|
| `global` | início do programa | variáveis globais e procedimentos |
| `procedimento <nome>` | cada `procedimento` | parâmetros e variáveis locais |

Cada símbolo guarda: nome, categoria (`variável`, `parâmetro` ou `procedimento`), tipo
(`inteiro` / `booleano`, ou nenhum para procedimentos), linha e coluna da declaração e, para
procedimentos, a assinatura (lista de `nome: tipo`).

**Regras de escopo**
- A busca de um nome vai do escopo mais interno para o mais externo.
- Um identificador só pode ser declarado **uma vez por escopo** (variáveis, parâmetros e
  procedimentos compartilham o mesmo espaço de nomes).
- Uma variável local ou parâmetro pode **sombrear** uma global (inclusive com outro tipo).
- Variáveis e parâmetros de um procedimento **não são visíveis** fora dele.
- As declarações globais são coletadas antes de analisar os corpos, então um procedimento pode
  chamar a si mesmo (recursão) ou outro procedimento declarado depois dele.

A opção `--simbolos` imprime a tabela de todos os escopos:

```bash
python -m minilang examples/procedimento.min --simbolos
```

---

## 2. Regras de tipos

Os tipos da MiniLang são `inteiro` e `booleano`.

| Construção | Regra |
|---|---|
| `x = expr;` | `x` declarada (variável ou parâmetro) e tipo de `expr` igual ao de `x` |
| `leia(x);` | `x` declarada como variável ou parâmetro |
| `escreva(expr);` | `expr` bem tipada |
| `se (c)` / `enquanto (c)` | `c` deve ser `booleano` |
| `+ - * / %` | operandos `inteiro` → resultado `inteiro` |
| `< <= > >=` | operandos `inteiro` → resultado `booleano` |
| `== !=` | operandos do **mesmo tipo** → resultado `booleano` |
| `e` `ou` | operandos `booleano` → resultado `booleano` |
| `não` | operando `booleano` → `booleano` |
| `-` (unário) | operando `inteiro` → `inteiro` |
| literais | número → `inteiro`; `verdadeiro`/`falso` → `booleano` |

Verificação extra: divisão ou resto por literal `0` (`x / 0`) é reportada como erro.

**Sem erros em cascata:** quando uma subexpressão já tem erro, o seu tipo passa a ser
"desconhecido" e ele não gera novos erros nos operadores acima dela. Um erro em `y + 1`
(com `y` não declarada) produz **um** erro, não vários.

---

## 3. Extensão Opção A — procedimentos

| Verificação | Mensagem (resumo) |
|---|---|
| Procedimento chamado sem declaração | `procedimento 'x' não declarado` |
| Nome de variável chamado como procedimento | `'x' é variável e não pode ser chamado como procedimento` |
| Nome de procedimento usado como variável | `'x' é um procedimento e não pode ser usado como variável` |
| Número de argumentos diferente do número de parâmetros | `procedimento 'x' espera N argumento(s), mas recebeu M` |
| Tipo de argumento diferente do tipo do parâmetro | `argumento K da chamada de 'x': o parâmetro 'p' é T, mas o argumento é U` |
| Procedimento, parâmetro ou local repetido | `identificador 'x' já declarado neste escopo` |

Como a passagem é **por valor**, atribuir a um parâmetro dentro do procedimento é permitido
(altera apenas a cópia local). Procedimentos não retornam valor, então só aparecem como comando
(`nome(args);`), nunca dentro de expressões. Isso já é garantido pela gramática do M2.

---

## 4. Formato dos erros e código de saída

Todos os erros são acumulados e listados juntos, com linha e coluna, no mesmo estilo dos M1 e M2:

```
Erro semântico [linha 12, coluna 5]: variável 'y' não declarada
```

Código de saída: `0` sem erros, `1` com erros léxicos, sintáticos ou semânticos, `2` se o arquivo
não puder ser lido.

---

## 5. Exemplos

| Arquivo | O que mostra |
|---|---|
| `examples/procedimento.min` | Programa válido com procedimento (deve passar na análise semântica) |
| `examples/erro_semantico.min` | Atribuição de `booleano` a `inteiro` |
| `examples/erros_semanticos_multiplos.min` | Vários erros semânticos de uma só vez |

```bash
python -m minilang examples/erro_semantico.min
python -m minilang examples/erros_semanticos_multiplos.min
```

---

## 6. Correspondência entre verificações e métodos

| Verificação | Método em `minilang/semantic.py` |
|---|---|
| Ponto de entrada e escopo global | `analisar()` |
| Declarações e duplicatas | `_declarar()`, `_declarar_procedimento()`, `_analisar_procedimento()` |
| Comandos | `_comando()`, `_comandos()` |
| Condições (`se`, `enquanto`) | `_condicao()` |
| Chamada de procedimento | `_chamada()` |
| Uso de variável | `_resolver_variavel()` |
| Expressões e operadores | `_expressao()`, `_unaria()`, `_binaria()`, `_exigir()` |
| Tabela de símbolos | `TabelaSimbolos`, `formatar_tabela_simbolos()` |
