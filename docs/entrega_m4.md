# M4 — Back-end: interpretação da AST, otimização e Opção A em execução

Este documento descreve o **back-end** implementado no Marco 4 (M4):

- [`minilang/interpreter.py`](../minilang/interpreter.py) — **interpreta a AST** diretamente (execução de programas MiniLang);
- [`minilang/optimizer.py`](../minilang/optimizer.py) — **otimizador** AST → AST (dobramento de constantes, simplificação algébrica e eliminação de código morto);
- [`minilang/__main__.py`](../minilang/__main__.py) — linha de comando com `--executar` e `--otimizar`.

Pipeline completo: **Léxico (M1) → Sintático + AST (M2) → Semântico + AST anotada (M3) → Otimização → Execução (M4)**. Cada fase só roda se a anterior não tiver erros.

```mermaid
flowchart LR
    A[".min"] --> B["Lexer<br/>tokens"] --> C["Parser<br/>AST"] --> D["Semântico<br/>AST anotada + tabela"] --> E["Otimizador<br/>AST menor"] --> F["Interpretador<br/>execução"]
```

---

## 1. Linha de comando e códigos de saída

```bash
python -m minilang arquivo.min [--ast] [--simbolos] [--otimizar] [--executar] [--sem-tokens]
```

| Opção | Efeito |
|---|---|
| `--executar` | Executa o programa (interpreta a AST) depois da análise semântica |
| `--otimizar` | Aplica as otimizações, imprime o relatório e passa a AST otimizada ao interpretador |
| `--ast` | Imprime a AST anotada com os tipos inferidos (e, com `--otimizar`, também a AST otimizada) |
| `--simbolos` | Imprime a tabela de símbolos |
| `--sem-tokens` | Oculta a tabela de tokens (saída mais limpa na demonstração) |

| Código | Significado |
|:---:|---|
| `0` | Sucesso |
| `1` | Erro léxico, sintático ou semântico |
| `2` | Arquivo não encontrado/ilegível ou uso incorreto da linha de comando |
| `3` | **Erro de execução** (divisão por zero, entrada inválida, estouro da pilha, laço infinito) |

Erros de execução seguem o mesmo padrão das demais fases:

```
Erro de execução [linha 11, coluna 23]: divisão por zero
```

---

## 2. Interpretador

### 2.1 Modelo de execução

O interpretador percorre a AST recursivamente (`_comando`, `_avaliar`). Os valores são `int` (tipo `inteiro`) e `bool` (tipo `booleano`).

**Memória.** Cada `Quadro` guarda, para um conjunto de nomes, o **valor** e o **tipo** declarado. Existe um quadro `global` e um quadro por chamada de procedimento; os quadros ficam em uma pilha (`Interpretador.pilha`) — a **pilha de ativação** exigida pela Opção A.

| Situação | Comportamento |
|---|---|
| Variável declarada sem valor | Começa com o valor padrão: `0` (`inteiro`) ou `falso` (`booleano`) |
| Busca de um nome | Quadro do topo da pilha; se não achar, quadro global (escopo estático: procedimentos não aninham) |
| Variável local com o nome de uma global | **Oculta** a global dentro do procedimento (mesma regra da tabela de símbolos do M3) |

### 2.2 Semântica das operações

| Construção | Semântica de execução |
|---|---|
| `/` | Divisão inteira que **trunca em direção a zero** (`-7 / 2 = -3`) |
| `%` | Resto com o **sinal do dividendo**, coerente com `/` (`-7 % 3 = -1`), isto é, `a = (a / b) * b + (a % b)` |
| `/` ou `%` por zero | Erro de execução com linha e coluna do operador |
| `e`, `ou` | **Curto-circuito**: `falso e X` e `verdadeiro ou X` não avaliam `X` |
| `==`, `!=`, `<`, `<=`, `>`, `>=` | Resultado `booleano` |
| `escreva(expr)` | Imprime uma linha; booleanos aparecem como `verdadeiro` / `falso` |
| `leia(x)` | Lê **uma linha** da entrada padrão; converte conforme o tipo declarado de `x` |
| `se` / `enquanto` | A condição já é garantidamente `booleano` (verificado no M3) |

`leia` de `inteiro` aceita `-?[0-9]+` (apenas dígitos ASCII, igual ao léxico); `leia` de `booleano` aceita exatamente `verdadeiro` ou `falso`. Qualquer outra entrada, ou fim de arquivo, é erro de execução com a posição do comando `leia`. Em terminal interativo é exibido o prompt `nome? `; com entrada redirecionada (`echo 7 | python ...`) nenhum prompt é impresso.

### 2.3 Opção A: procedimentos em execução

Uma chamada `p(a1, ..., an);` executa, em ordem:

1. Avalia os argumentos **no quadro do chamador**.
2. Confere a quantidade de argumentos (defesa extra; o M3 já garante).
3. Cria um novo `Quadro`: os parâmetros recebem **cópias** dos valores (**passagem por valor**) e as variáveis locais recebem o valor padrão (**são reiniciadas a cada chamada**).
4. Empilha o quadro, executa o corpo e **sempre** desempilha (`try/finally`), mesmo se houver erro.

Consequências verificadas nos testes: alterar um parâmetro não altera a variável do chamador; procedimentos enxergam e podem alterar globais; a **recursão** (inclusive mútua, com declaração posterior) funciona porque o M3 registra todos os procedimentos antes de analisar os corpos.

```
programa escopo_e_valor { ... }   -> saída: 101, 7, 1, 50
```

### 2.4 Proteções

| Proteção | Padrão | Erro reportado |
|---|---|---|
| Profundidade da pilha de ativação | 100 chamadas | `estouro da pilha de ativação: profundidade máxima de 100 chamadas excedida em 'p'` |
| Passos executados (comandos + iterações) | 1.000.000 | `limite de 1000000 passos excedido (possível laço infinito)` |
| `RecursionError` do Python | — | convertido em erro de execução (nunca vaza *traceback*) |

Ao final, a CLI imprime estatísticas: passos, chamadas de procedimento e profundidade máxima da pilha.

---

## 3. Otimizador

O otimizador recebe a AST **já verificada e anotada** e devolve uma **nova AST** (a original não é modificada). Cada transformação gera um registro `Otimizacao(tipo, linha, coluna, descricao)`, exibido pelo relatório de `--otimizar`.

### 3.1 Técnicas implementadas

**1. Dobramento de constantes** (*constant folding*): operadores aplicados a literais são calculados em tempo de compilação.

| Antes | Depois |
|---|---|
| `2 * 3 + 4` | `10` |
| `verdadeiro e não falso` | `verdadeiro` |
| `2 > 3` | `falso` |
| `-(2 + 3)` | `-5` |

**2. Simplificação algébrica**: identidades que eliminam operações.

| Padrão | Resultado | Padrão | Resultado |
|---|---|---|---|
| `x + 0`, `0 + x`, `x - 0` | `x` | `b e verdadeiro` | `b` |
| `x * 1`, `1 * x`, `x / 1` | `x` | `b ou falso` | `b` |
| `x * 0`, `0 * x`, `x % 1` | `0` (*) | `falso e X` | `falso` |
| `não não b`, `-(-x)` | `b`, `x` | `verdadeiro ou X` | `verdadeiro` |
| `B e falso`, `B ou verdadeiro` | `falso`, `verdadeiro` (*) | | |

**3. Eliminação de código morto**: após o dobramento, condições constantes decidem o fluxo.

| Antes | Depois |
|---|---|
| `se (verdadeiro) { A } senão { B }` | `A` (comandos inseridos no lugar do `se`) |
| `se (falso) { A } senão { B }` | `B` |
| `se (falso) { A }` | *(nada)* |
| `enquanto (falso) { ... }` | *(nada)* |

### 3.2 Correção (preservação da semântica)

(*) As regras marcadas só se aplicam quando o operando descartado **não pode falhar** (`_sem_falha`): não contém `/` ou `%` com divisor que não seja literal diferente de zero. Assim, `(1 / z) * 0` **não** vira `0`, pois isso esconderia a divisão por zero que o programa original provocaria. As regras com `falso e X` / `verdadeiro ou X` são sempre seguras porque o interpretador faz curto-circuito.

O dobramento usa **as mesmas funções** do interpretador (`aplicar_binaria`, `aplicar_unaria`, `dividir`, `resto`), então não existe divergência entre calcular em compilação ou em execução. Divisão por zero literal **não** é dobrada: o erro continua sendo reportado em tempo de execução.

Os testes de equivalência (`TestEquivalenciaSemantica`) executam cada programa antes e depois da otimização e exigem **saída idêntica**.

### 3.3 Demonstração

```bash
python -m minilang examples/otimizacao.min --otimizar --executar --sem-tokens
```

Resultado: 15 otimizações (7 de dobramento de constantes, 5 de simplificação algébrica, 3 de eliminação de código morto); a saída do programa é a mesma (`10, 10, 10, verdadeiro`), mas são executados **7 passos em vez de 10** (o `se` constante, o `se` falso e o `enquanto` falso deixam de existir). Com `--ast` as duas árvores (original e otimizada) são impressas para comparação.

---

## 4. Anotação da AST com tipos inferidos (fecha o M3)

Todo `ASTNode` possui o campo `tipo_inferido` (`None` até a análise semântica). O `AnalisadorSemantico` grava `"inteiro"` ou `"booleano"` em **cada expressão** que consegue tipar (literais, variáveis, operadores unários e binários, condições e argumentos de chamada). Expressões com erro permanecem `None`. O campo não participa de `==` nem do construtor (`field(init=False, compare=False)`), então os nós continuam sendo criados exatamente como antes. `formatar_ast` exibe o tipo ao final da linha:

```
BinaryOp: (+) [linha 9, col 26] : inteiro
  BinaryOp: (*) [linha 9, col 22] : inteiro
    Var: valor [linha 9, col 16] : inteiro
```

---

## 5. Correspondência entre funcionalidades e código

| Funcionalidade | Onde |
|---|---|
| Execução de comandos | `Interpretador._comando()` |
| Avaliação de expressões e curto-circuito | `Interpretador._avaliar()` |
| Pilha de ativação e chamadas | `Quadro`, `Interpretador._chamar()` |
| Entrada (`leia`) | `Interpretador._ler()`, `entrada_padrao()` |
| Operações aritméticas compartilhadas | `dividir()`, `resto()`, `aplicar_binaria()`, `aplicar_unaria()` |
| Erros de execução | `ErroExecucao` |
| Dobramento de constantes | `Otimizador._unaria()`, `Otimizador._binaria()` |
| Simplificação algébrica | `Otimizador._simplificar()` |
| Código morto | `Otimizador._condicional()`, ramo `WhileStmtNode` de `Otimizador._comando()` |
| Segurança das regras | `_sem_falha()` |
| Relatório | `Otimizacao`, `Otimizador.registros`, `formatar_relatorio_otimizacao()` |
| Anotação de tipos | `AnalisadorSemantico._expressao()`, `ASTNode.tipo_inferido` |

## 6. Exemplos de execução

| Arquivo | O que mostra | Comando |
|---|---|---|
| `examples/fatorial.min` | Laço + procedimento com locais; fatoriais de 1 a 6 | `python -m minilang examples/fatorial.min --executar --sem-tokens` |
| `examples/recursao.min` | Recursão (pilha de ativação, profundidade 11) | `python -m minilang examples/recursao.min --executar --sem-tokens` |
| `examples/escopo_e_valor.min` | Passagem por valor e ocultação de global | `python -m minilang examples/escopo_e_valor.min --executar --sem-tokens` |
| `examples/otimizacao.min` | Três otimizações e AST antes/depois | `python -m minilang examples/otimizacao.min --otimizar --executar --ast --sem-tokens` |
| `examples/entrada.min` | `leia` de dois inteiros (entrada padrão) | `"7","12" \| python -m minilang examples/entrada.min --executar --sem-tokens` (PowerShell) ou execução interativa |
| `examples/erro_execucao.min` | Erro **de execução** (divisão por zero) com código de saída 3 | `python -m minilang examples/erro_execucao.min --executar --sem-tokens` |

## 7. Testes do M4

| Arquivo | Cobertura |
|---|---|
| `tests/test_interpreter.py` | Aritmética (truncamento, resto), operadores, curto-circuito, `leia`, procedimentos, escopo, recursão, estouro de pilha, laço infinito, erros de execução |
| `tests/test_optimizer.py` | Cada regra de dobramento/simplificação/código morto, casos em que **não** se deve otimizar, imutabilidade da AST original, equivalência de saída antes/depois |
| `tests/test_anotacao_ast.py` | Tipos inferidos em literais, variáveis, operadores, condições e argumentos; `formatar_ast` |
| `tests/test_backend_cli.py` | `--executar`, `--otimizar`, `--sem-tokens`, entrada padrão, códigos de saída 0/1/3 |
