# Nota de marco — M1: Analisador léxico

**Equipe:** 
Davi Floriano Hermida |	1272413195
Paulo Victor Nonato de Jesus |	12724129348
Alexandre Ribeiro Silva e Silva |	12724133597
Eraldino Ramos Albergaria Lopes |	12724123513

**Repositório:** https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang
**Extensão escolhida (para o M4):** Opção A — procedimentos sem retorno, com parâmetros por valor

## O que foi entregue

- Analisador léxico manual em Python, baseado em AFD ([`minilang/lexer.py`](../minilang/lexer.py)).
- Reconhece todas as categorias da especificação: 15 palavras reservadas,
  identificadores, números inteiros, operadores aritméticos, relacionais,
  lógicos e de atribuição, e os 8 delimitadores.
- Lookahead de 1 caractere para `=`/`==`, `<`/`<=`, `>`/`>=` e `!=`.
- Descarta espaços e comentários (`#` até o fim da linha) e rastreia linha e coluna.
- Erros léxicos com mensagem, linha e coluna; a análise continua após o erro.
- Linha de comando: `python -m minilang arquivo.min` (tabela de tokens + erros).
- Especificação formal: expressões regulares, diagrama e tabela de transição
  do AFD em [`docs/entrega_m1.md`](entrega_m1.md).
- 56 testes automatizados (`python -m unittest discover -s tests`), com casos
  válidos, inválidos e os arquivos de `examples/`.

## Principais decisões

- **Implementação manual**, sem gerador: cada método do lexer é um caminho do AFD.
- **Maior prefixo (maximal munch):** `<=` é um token; `===` vira `==` + `=`.
- **`12abc` e `_temp` são erros léxicos**, em vez de passarem adiante como tokens separados.
- **`senao` e `nao`** são aceitos como sinônimos de `senão` e `não`.
- **Alfabeto restrito** a letras (com acentos do português), dígitos `0–9` e
  espaço, tabulação e quebra de linha; qualquer outro caractere é erro.
- **Erro vira token `ERRO` + mensagem**, para o parser do M2 poder continuar
  a análise e reportar vários erros.

## Limitações conhecidas

- Números não têm limite de tamanho no lexer; o intervalo de `inteiro` será
  verificado nas fases seguintes.
- A coluna conta caracteres: uma tabulação vale uma coluna, não a largura
  exibida pelo editor.

## Uso de IA generativa

_[A equipe deve revisar e completar esta seção.]_ Foi usado o Claude
(Anthropic) para revisar o M1 e implementar os ajustes técnicos:
mensagens de erro léxico, correção da recursão nos comentários, restrição do
alfabeto, linha de comando, testes e documentação do AFD. Todos os integrantes
devem revisar esse código e conseguir explicar qualquer trecho.
