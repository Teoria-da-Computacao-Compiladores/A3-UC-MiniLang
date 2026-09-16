## Documentação do AFD (Tabela de Transição)

O analisador léxico da MiniLang opera como uma máquina de estados finitos. A transição ocorre caractere a caractere. Quando a entrada é classificada como "Outro", o autômato utiliza o *lookahead* (não consome o caractere) e finaliza o token atual, retornando ao estado inicial para a próxima leitura.

| Estado Atual | Entrada (Caractere Lido) | Próximo Estado | Ação / Retorno (Token gerado) |
| :--- | :--- | :--- | :--- |
| **q0** (Inicial) | Letra | **q1** | - |
| **q0** | Dígito | **q2** | - |
| **q0** | `=` | **q3** | - |
| **q0** | `<` | **q4** | - |
| **q0** | `>` | **q5** | - |
| **q0** | `!` | **q6** | - |
| **q0** | `#` | **q7** | - |
| **q0** | Espaço ou `\n` | **q0** | Ignorar e avançar |
| **q0** | `+`, `-`, `*`, `/`, `(`, `)`, `{`, `}`, etc. | **q_final** | Retorna Token Simples (SOMA, PONTO, etc.) |
| **q0** | Outro caractere | **q_erro** | Retorna **ERRO** léxico |
| **q1** (Identificador) | Letra, Dígito ou `_` | **q1** | - |
| **q1** | Outro | **q_final** | Retorna **IDENTIFICADOR** ou **PALAVRA_RESERVADA** |
| **q2** (Número) | Dígito | **q2** | - |
| **q2** | Outro | **q_final** | Retorna **NUMERO** |
| **q3** (Atribuição) | `=` | **q_final** | Retorna **IGUAL** (`==`) |
| **q3** | Outro | **q_final** | Retorna **ATRIBUICAO** (`=`) |
| **q4** (Menor) | `=` | **q_final** | Retorna **MENOR_IGUAL** (`<=`) |
| **q4** | Outro | **q_final** | Retorna **MENOR** (`<`) |
| **q5** (Maior) | `=` | **q_final** | Retorna **MAIOR_IGUAL** (`>=`) |
| **q5** | Outro | **q_final** | Retorna **MAIOR** (`>`) |
| **q6** (Exclamação) | `=` | **q_final** | Retorna **DIFERENTE** (`!=`) |
| **q6** | Outro | **q_erro** | Retorna **ERRO** léxico (Não existe `!` isolado) |
| **q7** (Comentário) | Qualquer, exceto `\n` | **q7** | Ignorar caractere |
| **q7** | `\n` (Quebra de linha) | **q0** | Reinicia busca por token |