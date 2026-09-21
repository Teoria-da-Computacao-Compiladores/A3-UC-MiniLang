#  Analisador Léxico

> A especificação formal (expressões regulares, diagrama e tabela do AFD)
> está em [entrega_m1.md](entrega_m1.md).

## Objetivo

O analisador léxico é responsável por percorrer o código-fonte
da linguagem MiniLang e transformá-lo em uma sequência de tokens.

Cada token possui:

- tipo;
- lexema;
- linha;
- coluna.

## Palavras reservadas

A implementação reconhece as seguintes palavras reservadas:

- programa
- var
- inteiro
- booleano
- se
- senão (também aceita `senao`)
- enquanto
- escreva
- leia
- verdadeiro
- falso
- e
- ou
- não (também aceita `nao`)
- fim

A linguagem diferencia maiúsculas de minúsculas: `FIM` e `Programa` são
identificadores, não palavras reservadas.

## Identificadores

Os identificadores são reconhecidos quando o primeiro caractere
é uma letra e os caracteres seguintes são letras, dígitos ou `_`.

São letras: `a–z`, `A–Z` e as letras acentuadas do português
(`á à â ã é ê í ó ô õ ú ü ç`). Por isso `ação` é um identificador válido.

Quando o lexema corresponde a uma palavra reservada, ele é
classificado de acordo com sua palavra reservada.

Caso contrário, é classificado como IDENTIFICADOR.

Uma palavra que começa com `_` (ex.: `_temp`) gera erro léxico.

## Números

São reconhecidos números inteiros formados por uma sequência
de dígitos de `0` a `9`.

Dígitos colados em letras (ex.: `12abc`) formam um único erro léxico de
"número mal formado".

## Operadores

### Aritméticos

`+`
 `-`
 `*`
 `/`
 `%`

### Relacionais

 `==`
 `!=`
 `<`
 `<=`
 `>`
 `>=`

### Atribuição

 `=`

### Lógicos

 `e`
 `ou`
 `não`

## Delimitadores

`(`
 `)`
 `{`
 `}`
 `;`
 `:`
 `,`
 `.`

## Comentários

Os comentários começam com `#` e continuam até o final da linha.

O lexer ignora o conteúdo do comentário e continua a análise
normalmente na próxima linha. Um comentário na última linha do arquivo,
sem quebra de linha no final, também é aceito.

## Linha e coluna

O lexer mantém as informações de linha e coluna durante a leitura
do código-fonte.

Essas informações são armazenadas em cada token e também permitem
identificar a posição de caracteres que provocam erros léxicos.

- Linha e coluna começam em 1.
- A posição de um token é a do seu primeiro caractere.
- A tabulação conta como uma coluna.
- Quebras de linha do Windows (`\r\n`) contam como uma única linha.

## Lookahead

O analisador utiliza a leitura do próximo caractere para distinguir
operadores de um e dois caracteres.

São tratados dessa maneira:

 `=` / `==`
`<` / `<=`
`>` / `>=`
`!` / `!=`

O caractere `!` isolado não pertence ao conjunto de operadores
válidos e, portanto, gera um erro léxico.

## Erros léxicos

Quando o lexer encontra um erro, ele:

1. produz um token do tipo ERRO com o lexema, a linha e a coluna;
2. registra uma mensagem em `Lexer.erros`, no formato
   `Erro léxico [linha L, coluna C]: descrição`;
3. continua a análise, para reportar todos os erros de uma vez.

| Situação | Mensagem |
|---|---|
| Caractere fora do alfabeto (`@`, `$`, `²`) | `caractere inválido '@'` |
| `!` sem `=` | `'!' isolado não é um operador válido; use '!=' para diferente ou 'não' para negação` |
| `12abc` | `número mal formado '12abc': identificadores devem começar com letra` |
| `_temp` | `identificador inválido '_temp': identificadores devem começar com letra` |

## Fim do arquivo

Quando não existem mais caracteres para analisar, o lexer produz
um token EOF, indicando o fim da entrada.
