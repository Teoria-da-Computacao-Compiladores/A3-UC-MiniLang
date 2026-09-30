# Nota de marco — M3: Analisador Semântico

**Equipe:**
Davi Floriano Hermida | 1272413195
Paulo Victor Nonato de Jesus | 12724129348
Alexandre Ribeiro Silva e Silva | 12724133597
Eraldino Ramos Albergaria Lopes | 12724123513

**Repositório:** https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang
**Extensão escolhida:** Opção A — procedimentos sem retorno, com parâmetros por valor

## O que foi entregue

- Analisador semântico em [`minilang/semantic.py`](../minilang/semantic.py), que percorre a AST do M2.
- Tabela de símbolos com pilha de escopos (global e local de procedimento) e exibição via `--simbolos`.
- Verificação de declaração prévia, duplicidade por escopo e visibilidade de variáveis locais.
- Checagem de tipos em atribuições, expressões (aritméticas, relacionais, lógicas, unárias) e condições.
- Suporte semântico à **Opção A**: existência do procedimento, número e tipo dos argumentos.
- Erros acumulados com linha e coluna, sem erros em cascata.
- Integração ao compilador: `python -m minilang arquivo.min` executa léxico, sintático e semântico.
- Testes automatizados em [`tests/test_semantic.py`](../tests/test_semantic.py) e exemplos em [`examples/`](../examples/).
- Especificação em [`docs/entrega_m3.md`](entrega_m3.md).

## Principais decisões de projeto

- **Duas passadas nas declarações globais:** os procedimentos são registrados antes de analisar os corpos, permitindo recursão e chamadas a procedimentos declarados depois.
- **Erros acumulados:** a análise não para no primeiro erro; um tipo "desconhecido" evita mensagens em cascata.
- **Sombreamento permitido:** local ou parâmetro pode ocultar uma global de mesmo nome.
- **Parâmetros por valor:** atribuir a um parâmetro é válido e afeta só a cópia local.

## Limitações conhecidas

- Não há verificação de variável usada antes de receber valor (inicialização), nem de código inalcançável.
- Divisão por zero só é detectada quando o divisor é o literal `0`.
- O intervalo numérico de `inteiro` não é verificado (o léxico aceita números de qualquer tamanho).

## Uso de IA generativa

_[A equipe deve revisar e completar esta seção.]_ Foi utilizado o Claude (Anthropic) para implementar o analisador semântico, os testes e a documentação do M3 a partir do código do M2. Todos os integrantes devem revisar esse código e conseguir explicar qualquer trecho.
