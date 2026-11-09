# Nota de marco — M4: Back-end, Relatório e Apresentação

**Equipe:**
Davi Floriano Hermida | 1272413195
Paulo Victor Nonato de Jesus | 12724129348
Alexandre Ribeiro Silva e Silva | 12724133597
Eraldino Ramos Albergaria Lopes | 12724123513

**Repositório:** https://github.com/Teoria-da-Computacao-Compiladores/A3-UC-MiniLang
**Extensão escolhida:** Opção A — procedimentos sem retorno, com parâmetros por valor

## O que foi entregue

- **Back-end por interpretação da AST** em [`minilang/interpreter.py`](../minilang/interpreter.py), com pilha de ativação, passagem por valor, variáveis locais, recursão, `leia`/`escreva` e erros de execução com linha e coluna.
- **Otimizador** em [`minilang/optimizer.py`](../minilang/optimizer.py) com três técnicas: dobramento de constantes, simplificação algébrica e eliminação de código morto, com relatório (`--otimizar`) e garantia de equivalência de saída.
- **Anotação da AST com tipos inferidos** (pendência do M3), visível em `--ast`.
- **Linha de comando completa:** `python -m minilang arquivo.min [--ast] [--simbolos] [--otimizar] [--executar]`, com código de saída `3` para erro de execução.
- **Extensão Opção A** demonstrada no código (parser, semântica, interpretador), nos testes e em exemplos (`procedimento.min`, `recursao.min`, `escopo_e_valor.min`, `fatorial.min`).
- **Testes automatizados:** 216 testes (`python -m unittest discover -s tests`), dos quais cerca de 145 são do M3/M4 (interpretador, otimizador, anotação e linha de comando).
- **Relatório técnico final** em [`docs/relatorio_final.pdf`](relatorio_final.pdf) (fonte em [`relatorio_final.html`](relatorio_final.html)) e **roteiro da apresentação** em [`docs/roteiro_apresentacao.md`](roteiro_apresentacao.md).
- Especificação do back-end em [`docs/entrega_m4.md`](entrega_m4.md).

## Principais decisões de projeto

- **Interpretar a AST em vez de gerar código de três endereços:** a AST já é anotada e verificada; interpretá-la dispensa uma representação intermediária e mantém a posição (linha/coluna) para erros de execução.
- **Semântica definida e documentada:** divisão inteira trunca em direção a zero, `%` tem o sinal do dividendo, `e`/`ou` fazem curto-circuito, variáveis começam em `0`/`falso`.
- **Uma única fonte de verdade para as operações:** o otimizador reutiliza as funções do interpretador, então dobrar uma constante em compilação nunca difere de calculá-la em execução.
- **Otimizações seguras:** uma regra que descartaria um operando só é aplicada se ele não puder falhar (por exemplo, `(1 / z) * 0` não é simplificado).
- **Otimizador sem efeito colateral na AST original:** a AST antes/depois pode ser comparada com `--ast --otimizar`.
- **Proteções de execução:** limite de profundidade da pilha de ativação e de passos, para que recursão infinita e laços infinitos virem erro em vez de travar.

## Limitações conhecidas

- `inteiro` usa inteiros de precisão arbitrária do Python; não há erro de estouro (*overflow*).
- A otimização é local (expressões e condições constantes); não há propagação de constantes entre comandos nem remoção de procedimentos não chamados.
- `leia` consome uma linha por chamada; não há tratamento de várias leituras na mesma linha.
- Não há verificação de variável usada antes de receber valor (bônus opcional do M3); variáveis não inicializadas valem `0`/`falso`.
- Procedimentos não retornam valor (limite da Opção A); só aparecem como comando.

## Uso de IA generativa

Foram usados o Claude (Anthropic) e o Google Gemini (por meio do assistente de programação Antigravity) ao longo do projeto. No M4 a IA ajudou a implementar o interpretador, o otimizador, a anotação da AST, os testes, os exemplos e a documentação.
