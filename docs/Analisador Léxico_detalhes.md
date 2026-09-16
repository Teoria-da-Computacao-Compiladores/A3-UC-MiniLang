
#  Analisador Léxico

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
- senão
- enquanto
- escreva
- leia
- verdadeiro
- falso
- e
- ou
- não
- fim

## Identificadores

Os identificadores são reconhecidos quando o primeiro caractere
é alfabético e os caracteres seguintes podem ser alfabéticos,
numéricos ou `_`.

Quando o lexema corresponde a uma palavra reservada, ele é
classificado de acordo com sua palavra reservada.

Caso contrário, é classificado como IDENTIFICADOR.

## Números

São reconhecidos números inteiros formados por uma sequência
de dígitos.

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
normalmente na próxima linha.

## Linha e coluna

O lexer mantém as informações de linha e coluna durante a leitura
do código-fonte.

Essas informações são armazenadas em cada token e também permitem
identificar a posição de caracteres que provocam erros léxicos.

## Lookahead

O analisador utiliza a leitura do próximo caractere para distinguir
operadores de um e dois caracteres.

São tratados dessa maneira:

 `=` / `==`
`<` / `<=`
`>` / `>=`
`!` / `!=`

O caractere `!` isolado não pertence ao conjunto de operadores
válidos e, portanto, gera um token ERRO.

## Erros léxicos

Quando um caractere não reconhecido é encontrado, o lexer produz
um token do tipo ERRO contendo:

- lexema;
- linha;
- coluna.

Isso permite que o erro seja identificado posteriormente pelas
etapas seguintes do compilador.

## Fim do arquivo

Quando não existem mais caracteres para analisar, o lexer produz
um token EOF, indicando o fim da entrada.
