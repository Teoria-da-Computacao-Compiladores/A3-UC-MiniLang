# Ajustes do M1: o que mudou e como o código funciona

Este documento tem duas partes:

1. **O que mudou**: cada problema encontrado na revisão do M1, como era antes e como ficou.
2. **Como o código funciona**: um passeio por cada arquivo e cada função, com
   um exemplo executado passo a passo e perguntas que podem aparecer na arguição.

---

# Parte 1 — O que mudou

## Resumo

| # | Problema | Solução | Arquivos |
|---|---|---|---|
| 1 | Erro léxico só gerava um token `ERRO`, sem mensagem | Classe `ErroLexico` + lista `Lexer.erros` com mensagens de linha e coluna | `lexer.py` |
| 2 | ~1000 linhas de comentário seguidas quebravam o lexer (`RecursionError`) | Comentários e espaços descartados em um laço | `lexer.py` |
| 3 | `isalpha()`/`isdigit()` aceitavam qualquer Unicode (`x²` virava identificador) | Funções próprias `eh_letra()` e `eh_digito()` com o alfabeto da linguagem | `lexer.py` |
| 4 | `12abc` virava `NUMERO` + `IDENTIFICADOR` sem erro | Vira um único erro "número mal formado" | `lexer.py` |
| 5 | `_temp` gerava erro só no `_` e depois um identificador `temp` | Vira um único erro "identificador inválido" | `lexer.py` |
| 6 | `senao` e `nao` (sem acento) viravam identificadores | Aceitos como sinônimos de `senão` e `não` | `lexer.py` |
| 7 | `python -m minilang arquivo.min` (comando mostrado em aula) não funcionava | Criados `minilang/__init__.py` e `minilang/__main__.py` | `__init__.py`, `__main__.py` |
| 8 | Saída não era tabela e o programa terminava com código 0 mesmo com erros | Tabela Linha / Coluna / Tipo / Lexema, lista de erros e códigos de saída 0/1/2 | `__main__.py` |
| 9 | Exemplos com três estilos diferentes; `operadores.min` tinha `x + y;` como comando | Exemplos com a mesma sintaxe + novo `erros_multiplos.min` | `examples/` |
| 10 | Nenhum teste de mensagens de erro, casos-limite, exemplos ou linha de comando | 36 testes novos (de 20 para 56) | `tests/` |
| 11 | `test_lexer.py` alterava o `sys.path` | Removido: `python -m unittest discover -s tests` já encontra o pacote | `tests/test_lexer.py` |
| 12 | AFD só com tabela parcial ("etc."), sem diagrama nem expressões regulares | Alfabeto, regex, diagrama Mermaid, tabela completa, estados finais e decisões | `docs/entrega_m1.md` |
| 13 | Faltava a nota de marco de uma página | Criada (nomes, divisão do trabalho e uso de IA para a equipe completar) | `docs/nota_marco_m1.md` |
| 14 | README com link `SEU_USUARIO`, comandos sem formatação e sem declaração de IA | README reescrito | `README.md` |
| 15 | Arquivos `__pycache__/*.pyc` versionados | `.gitignore` e remoção dos `.pyc` do Git | `.gitignore` |

O que **não mudou**: os nomes de `TokenType`, a classe `Token`, os métodos
`avancar()`, `espiar()` e `proximo_token()`, e os 20 testes que já existiam
(todos continuam passando).

## Detalhes de cada mudança

### 1. Mensagens de erro léxico

**Antes:** ao ver `@`, o lexer devolvia `Token(ERRO, '@', 7, 12)` e nada mais.
Quem rodava o programa via o token na lista, mas não havia mensagem, e a
rubrica pede "reporta erro léxico com posição correta" e o checklist pede
"fase, linha, coluna e descrição".

**Depois:** o lexer continua devolvendo o token `ERRO` (o parser do M2 vai
precisar dele), **e também** guarda um `ErroLexico` na lista `lexer.erros`:

```
Erro léxico [linha 7, coluna 12]: caractere inválido '@'
```

Mensagens específicas foram criadas para `!` isolado, `12abc` e `_temp`, que
explicam como corrigir.

### 2. Recursão nos comentários

**Antes:**

```python
if caractere == '#':
    while caractere is not None and caractere != '\n':
        self.avancar()
        caractere = self.espiar()
    return self.proximo_token()   # chama a si mesma
```

Cada comentário empilhava uma chamada de `proximo_token()`. O Python limita a
pilha a cerca de 1000 chamadas, então um arquivo com muitas linhas de
comentário seguidas quebrava com `RecursionError`.

**Depois:** `_pular_espacos_e_comentarios()` usa um `while True` que alterna
entre pular espaços e pular comentários até achar outro caractere. Não há
recursão; o teste `test_milhares_de_comentarios_seguidos_nao_estouram_recursao`
roda 5000 linhas de comentário.

### 3. Alfabeto restrito

**Antes:** `caractere.isalpha()`, `isalnum()`, `isdigit()` e `isspace()`.
Esses métodos do Python aceitam **qualquer** letra, dígito ou espaço Unicode:
`²`, `٣` (dígito árabe), letras gregas, espaço não separável copiado da web...

**Depois:** funções próprias no topo de `lexer.py`:

- `eh_letra(c)`: `a–z`, `A–Z` ou uma das letras em `LETRAS_ACENTUADAS`;
- `eh_digito(c)`: `0–9`;
- `ESPACOS = " \t\r\n"`.

Agora `x²` vira `IDENTIFICADOR(x)` + `ERRO(²)`.

### 4 e 5. `12abc` e `_temp`

**Antes:** `12abc` → `NUMERO(12)` + `IDENTIFICADOR(abc)`, sem erro nenhum; o
problema só apareceria no parser, com uma mensagem confusa.
`_temp` → `ERRO(_)` + `IDENTIFICADOR(temp)`.

**Depois:** os dois viram **um único** token `ERRO` com o lexema inteiro e uma
mensagem que explica a regra ("identificadores devem começar com letra").

### 6. `senao` e `nao`

Foram adicionados ao dicionário `PALAVRAS_RESERVADAS` apontando para
`TokenType.SENAO` e `TokenType.NAO`. Consequência: `senao` e `nao` não podem
mais ser usados como nomes de variáveis.

### 7 e 8. Linha de comando

**Antes:** só `python minilang/lexer.py arquivo.min`, com a saída
`Token(IDENTIFICADOR | Lexema: 'x' | ...)` e código de saída sempre 0.

**Depois:** `python -m minilang arquivo.min` imprime a tabela e os erros:

```
Tokens gerados:
Linha  Coluna  Tipo            Lexema
--------------------------------------------------
7      12      ERRO            @

1 erro(s) léxico(s) encontrado(s):
  Erro léxico [linha 7, coluna 12]: caractere inválido '@'
```

Códigos de saída: `0` sem erros, `1` com erros léxicos, `2` quando o arquivo
não existe, não está em UTF-8 ou nenhum arquivo foi informado. O comando antigo
continua funcionando.

### 9. Exemplos

Todos seguem a mesma forma: `programa nome { declarações e comandos } fim.`,
com `var nome: tipo;` e comandos terminados em `;`. Isso ainda não é a
gramática oficial (que será definida no M2), mas evita reescrever exemplos
contraditórios depois.

| Arquivo | Mudança |
|---|---|
| `valido.min` | Ganhou comentário explicativo e um `enquanto` |
| `operadores.min` | `x + y;` virou `r = x + y;` (expressão solta não é comando); ganhou operadores lógicos |
| `comentarios.min` | `var` sozinho virou `var x: inteiro;`; comentário no fim da linha e na última linha sem quebra |
| `erro_lexico.min` | Sem mudança (o erro continua na linha 7, coluna 12) |
| `erros_multiplos.min` | **Novo**: `_temp`, `12abc`, `$` e `!` isolado no mesmo arquivo |

---

# Parte 2 — Como o código funciona

## Visão geral

```
arquivo .min ──► __main__.py ──► Lexer (lexer.py) ──► lista de Token + lista de ErroLexico
                  (lê o arquivo,                          │
                   imprime a tabela)  ◄───────────────────┘
```

| Arquivo | Responsabilidade |
|---|---|
| `minilang/lexer.py` | O analisador léxico: tipos de token, alfabeto, tabelas e a classe `Lexer` |
| `minilang/__main__.py` | Linha de comando: lê o arquivo, chama o lexer, imprime tabela e erros |
| `minilang/__init__.py` | Marca `minilang` como pacote e exporta as classes principais |
| `tests/*.py` | Testes automatizados com `unittest` |
| `examples/*.min` | Programas de exemplo usados na demonstração e nos testes |

## `minilang/lexer.py`

O arquivo tem quatro blocos, nesta ordem.

### Bloco 1 — Tipos de dados

**`TokenType`** é um `Enum` com todas as categorias de token: uma para cada
palavra reservada (`PROGRAMA`, `SE`, ...), `IDENTIFICADOR`, `NUMERO`, um
membro por operador e delimitador, e dois especiais:

- `EOF`: fim da entrada. O parser do M2 usa esse token para saber que o
  programa acabou (e acusar erro se sobrar algo depois de `fim.`).
- `ERRO`: um trecho que não forma nenhum token válido.

`auto()` numera os membros automaticamente; só o nome importa.

**`Token`** é um `@dataclass` com quatro campos: `tipo`, `lexema` (o texto
exato lido), `linha` e `coluna` (posição do **primeiro** caractere). O
`@dataclass` gera sozinho o construtor e a comparação `==`, o que facilita os
testes. O `__str__` define como o token aparece no `print`.

**`ErroLexico`** também é um `@dataclass`, com `mensagem`, `linha` e `coluna`.
O `__str__` produz o texto `Erro léxico [linha L, coluna C]: mensagem`.

### Bloco 2 — Alfabeto

```python
LETRAS_ACENTUADAS = "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ"
ESPACOS = " \t\r\n"

def eh_letra(c): ...
def eh_digito(c): ...
def eh_caractere_de_identificador(c): ...
```

São as **classes de caracteres** do AFD (as "setas" do diagrama são rotuladas
com elas). Todas aceitam `c = None` (fim do arquivo) e devolvem `False` nesse
caso, para os laços pararem sem precisar testar `None` separadamente.

`eh_digito` compara `"0" <= c <= "9"`: a comparação de strings em Python segue
a ordem dos códigos Unicode, e os dígitos ASCII são consecutivos.

### Bloco 3 — Tabelas

Três dicionários guardam o que é "dado" da linguagem, separado da lógica:

| Tabela | Chave → valor | Usada em |
|---|---|---|
| `PALAVRAS_RESERVADAS` | lexema → `TokenType` (inclui `senao` e `nao`) | decidir se uma palavra é palavra reservada ou identificador |
| `SIMBOLOS_SIMPLES` | caractere → `TokenType` | `+ - * / % ( ) { } ; : , .` |
| `OPERADORES_COM_LOOKAHEAD` | caractere → (token sozinho, token com `=`) | `=`, `<`, `>`, `!` |

Em `OPERADORES_COM_LOOKAHEAD`, o `!` tem `None` como "token sozinho", porque
`!` isolado não existe na linguagem. Adicionar um operador novo de dois
caracteres (por exemplo, para uma extensão) é só acrescentar uma linha aqui.

### Bloco 4 — A classe `Lexer`

#### Estado interno

| Atributo | Significado |
|---|---|
| `codigo` | O texto completo do programa |
| `posicao` | Índice do próximo caractere a ler em `codigo` |
| `linha`, `coluna` | Posição (começando em 1) do próximo caractere a ler |
| `erros` | Lista de `ErroLexico` encontrados até agora |
| `tem_erros` | Propriedade: `True` se `erros` não estiver vazia |

#### Leitura de caracteres: `avancar()` e `espiar()`

- **`espiar()`** devolve o caractere em `posicao` **sem consumir**. É o
  **lookahead**. Devolve `None` no fim do texto.
- **`avancar()`** devolve o caractere e anda uma posição. Se o caractere for
  `\n`, soma 1 na linha e volta a coluna para 1; senão, soma 1 na coluna.

Essas são as **únicas** funções que mexem em `posicao`, `linha` e `coluna`,
por isso a contagem de posição fica sempre correta.

Com `\r\n` (Windows), o `\r` soma uma coluna e o `\n` em seguida reinicia a
coluna, então o resultado é o mesmo de um arquivo com só `\n`.

#### `proximo_token()` — o estado inicial q0

É o coração do lexer. Cada chamada devolve **um** token:

1. `_pular_espacos_e_comentarios()` descarta tudo que não gera token.
2. Se `espiar()` devolve `None`, o arquivo acabou: devolve `EOF`.
3. Guarda `linha, coluna` **antes** de consumir, porque essa é a posição do token.
4. Olha o primeiro caractere e escolhe o caminho do AFD:

| Primeiro caractere | Caminho | Estado no AFD |
|---|---|---|
| letra | `_ler_identificador_ou_palavra_reservada()` | q1 |
| dígito | `_ler_numero()` | q2 / q3 |
| `_` | `_ler_identificador_invalido()` | q4 |
| `=` `<` `>` `!` | `_ler_operador_com_lookahead()` | q5–q12 |
| `+ - * / % ( ) { } ; : , .` | consome e consulta `SIMBOLOS_SIMPLES` | q14 |
| qualquer outro | consome e chama `_erro()` com "caractere inválido" | qerr |

A **ordem** dos `if` importa pouco porque as classes não se sobrepõem (um
caractere não é letra e dígito ao mesmo tempo).

#### `tokenizar()`

Chama `proximo_token()` até receber `EOF` e devolve a lista inteira (com o
`EOF` no final). É o que a linha de comando e os testes usam. O parser do M2
pode usar tanto a lista quanto chamar `proximo_token()` sob demanda.

#### `_pular_espacos_e_comentarios()` — q0 ↺ espaço e q13

```python
while True:
    caractere = self.espiar()
    if caractere is not None and caractere in ESPACOS:
        self.avancar()                      # espaço: consome e repete
    elif caractere == "#":
        while self.espiar() not in (None, "\n"):
            self.avancar()                  # consome até o fim da linha
    else:
        return                              # achou o início de um token
```

O `\n` que termina o comentário **não** é consumido no laço interno; ele é
consumido na volta seguinte como espaço, o que atualiza a linha normalmente.
Se o comentário for a última linha do arquivo, `espiar()` devolve `None` e o
laço também para.

#### `_ler_palavra()`

Consome letras, dígitos e `_` enquanto houver e devolve o texto lido. É usado
pelos três caminhos que leem "palavras": identificador, número mal formado e
identificador inválido.

#### `_ler_identificador_ou_palavra_reservada()` — q1

Lê a palavra inteira e só **depois** consulta `PALAVRAS_RESERVADAS`. Por isso
`programa1` é identificador (a palavra lida é `programa1`, que não está na
tabela), e `se` é palavra reservada. É o jeito padrão de separar palavras
reservadas de identificadores sem criar um estado no AFD para cada letra de
cada palavra reservada.

#### `_ler_numero()` — q2 e q3

1. Consome dígitos.
2. Se o próximo caractere (lookahead) for letra ou `_`, o número está "colado"
   em uma palavra: consome o resto com `_ler_palavra()` e devolve um erro
   "número mal formado" com o lexema inteiro (`12abc`).
3. Senão, devolve `NUMERO`.

`10;` e `10+2` continuam válidos, porque `;` e `+` não são letras.

#### `_ler_identificador_invalido()` — q4

Chamado quando a palavra começa com `_`. Consome a palavra toda e devolve um
único erro.

#### `_ler_operador_com_lookahead()` — q5 a q12

```python
primeiro = self.avancar()                                  # ex.: "<"
tipo_simples, tipo_com_igual = OPERADORES_COM_LOOKAHEAD[primeiro]

if self.espiar() == "=":                                   # lookahead
    self.avancar()
    return Token(tipo_com_igual, primeiro + "=", ...)      # "<="

if tipo_simples is None:                                   # "!" sozinho
    return self._erro(...)

return Token(tipo_simples, primeiro, ...)                  # "<"
```

Um único método trata os quatro operadores porque todos seguem o mesmo padrão
"caractere, opcionalmente seguido de `=`". Isso implementa a **regra do maior
prefixo**: se dá para formar `<=`, forma; só se não der, fica com `<`.

#### `_erro()`

Registra `ErroLexico(mensagem, linha, coluna)` em `self.erros` e devolve um
`Token(ERRO, ...)`. Como ela **devolve** um token em vez de lançar uma exceção,
a análise continua normalmente no caractere seguinte.

#### Bloco `if __name__ == "__main__"`

Só roda quando alguém executa `python minilang/lexer.py arquivo.min` (o
comando antigo). Ele ajusta o `sys.path` para o Python encontrar o pacote
`minilang` e chama a mesma função `main()` da linha de comando nova. Assim os
dois comandos têm exatamente o mesmo comportamento.

## Exemplo executado passo a passo

Entrada (duas linhas):

```
x <= 10; # limite
se
```

| Passo | `posicao` → caractere | O que acontece | Token emitido |
|---|---|---|---|
| 1 | 0 → `x` | Não é espaço nem `#`. Guarda (1,1). É letra → q1. Lê `x`; próximo é espaço, para. `x` não está em `PALAVRAS_RESERVADAS`. | `IDENTIFICADOR 'x' (1,1)` |
| 2 | 1 → ` ` | Pula o espaço. Guarda (1,3). `<` → lookahead. `espiar()` vê `=`, consome. | `MENOR_IGUAL '<=' (1,3)` |
| 3 | 4 → ` ` | Pula o espaço. Guarda (1,6). Dígito → q2. Lê `10`; próximo é `;`, não é letra. | `NUMERO '10' (1,6)` |
| 4 | 7 → `;` | Símbolo simples. | `PONTO_VIRGULA ';' (1,8)` |
| 5 | 8 → ` ` | Pula o espaço. Vê `#`: consome `# limite` até antes do `\n`. Volta ao laço: `\n` é espaço, consome (linha 2, coluna 1). Guarda (2,1). Letra → q1. Lê `se`, que está na tabela. | `SE 'se' (2,1)` |
| 6 | 20 → fim | `espiar()` devolve `None`. | `EOF '' (2,3)` |

## `minilang/__main__.py`

É executado por `python -m minilang arquivo.min` (o Python procura o arquivo
`__main__.py` dentro do pacote).

| Função | O que faz |
|---|---|
| `main(argv=None)` | Configura a saída em UTF-8 (para acentos aparecerem certo no terminal do Windows), lê o argumento com `argparse`, chama `ler_arquivo()`, roda `Lexer(...).tokenizar()`, imprime a tabela e os erros e devolve o código de saída. Recebe `argv` como parâmetro para poder ser testada sem abrir um terminal. |
| `ler_arquivo(caminho)` | Abre o arquivo em UTF-8 e devolve `(codigo, None)` ou `(None, mensagem)` para arquivo inexistente, arquivo que não está em UTF-8 ou outro erro de leitura. |
| `formatar_tabela(tokens)` | Monta o texto da tabela com colunas de largura fixa (`f"{valor:<7}"` alinha à esquerda em 7 caracteres). O `EOF` aparece como `(fim da entrada)` porque o lexema dele é vazio. |

`sys.exit(main())` transforma o valor devolvido por `main()` no código de
saída do processo, que scripts e a CI podem usar para saber se houve erro.

Se nenhum arquivo for informado, o próprio `argparse` mostra a mensagem de uso
e sai com código 2.

## `minilang/__init__.py`

Transforma a pasta `minilang` em pacote (necessário para `python -m minilang`
e para `from minilang.lexer import ...`) e reexporta `Lexer`, `Token`,
`TokenType` e `ErroLexico`, permitindo escrever `from minilang import Lexer`.

## Testes

Todos usam `unittest` (biblioteca padrão). O comando
`python -m unittest discover -s tests` procura arquivos `test_*.py` na pasta
`tests/`; como ele é executado na raiz do projeto, o pacote `minilang` é
encontrado sem mexer no `sys.path`.

| Arquivo | Testes | O que verifica |
|---|---|---|
| `test_lexer.py` | 5 | Casos básicos (já existia) |
| `test_lexer_complemento.py` | 15 | Todas as categorias de token (já existia) |
| `test_lexer_erros_e_limites.py` | 24 | Texto e posição das mensagens de erro; vários erros no mesmo código; `12abc`, `3_x`, `_temp`, `x²`, `٣`; acentos em identificadores; `senao`/`nao`; maiúsculas; espaço não separável; 5000 comentários; comentário na última linha; `\r\n`; tabulação; posição do EOF; operadores colados (`a<=b==c`); `===` |
| `test_exemplos_e_cli.py` | 12 | Cada arquivo de `examples/` (sem erros ou com os erros esperados nas posições certas) e a linha de comando rodando de verdade em um subprocesso: tabela, mensagens e códigos de saída 0, 1 e 2, além do comando antigo |

A função auxiliar `tipos(codigo)` devolve só a lista de tipos (sem o `EOF`),
o que deixa as asserções curtas. Os testes da linha de comando usam
`subprocess.run([sys.executable, "-m", "minilang", ...])`, ou seja, executam o
mesmo comando que o professor vai digitar.

## Perguntas prováveis na arguição

**Por que o lexer é um AFD?** Tokens são linguagens regulares (Tipo 3 na
hierarquia de Chomsky): cada categoria é descrita por uma expressão regular, e
toda expressão regular tem um AFD equivalente. O lexer é esse AFD escrito em
código: `proximo_token()` é o estado inicial e cada `_ler_*` é um caminho.

**Onde está o lookahead?** Em `espiar()`. Ele é usado em
`_ler_operador_com_lookahead()` (decidir entre `<` e `<=`), nos laços que
leem palavras e números (saber quando parar) e em `_ler_numero()` (detectar
`12abc`).

**Por que `===` vira `==` e `=`?** Pela regra do maior prefixo: o lexer forma
o maior token possível começando na posição atual (`==`) e recomeça a partir
do que sobrou (`=`).

**Como uma palavra reservada é diferenciada de um identificador?** O lexer lê
a palavra inteira como se fosse identificador e depois consulta
`PALAVRAS_RESERVADAS`. Por isso `programa1` é identificador.

**Por que o erro gera um token e não uma exceção?** Para a análise continuar e
reportar todos os erros de uma vez. A partir do M2 o compilador precisa se
recuperar de erros, e o parser vai receber os tokens `ERRO` para tratá-los.

**Como a coluna é calculada?** `avancar()` soma 1 a cada caractere e volta a 1
depois de `\n`. A posição de um token é guardada antes de consumir o primeiro
caractere dele.

**Por que não usar `isalpha()`?** Porque aceita letras e dígitos de qualquer
alfabeto (`²`, `٣`, letras gregas), que não pertencem à MiniLang.

**O que aconteceria sem o `EOF`?** O parser não teria como distinguir "o
programa acabou" de "faltam tokens", nem detectar tokens sobrando depois de
`fim.`.
