"""
Linha de comando do compilador MiniLang.

Uso:
    python -m minilang arquivo.min

Imprime a tabela de tokens e, se houver, a lista de erros léxicos.
Código de saída: 0 sem erros, 1 com erros léxicos, 2 se o arquivo não puder
ser lido.
"""

import argparse
import sys

from minilang.lexer import Lexer, TokenType


def formatar_tabela(tokens) -> str:
    linhas = [
        f"{'Linha':<7}{'Coluna':<8}{'Tipo':<16}Lexema",
        "-" * 50,
    ]
    for token in tokens:
        lexema = "(fim da entrada)" if token.tipo == TokenType.EOF else token.lexema
        linhas.append(f"{token.linha:<7}{token.coluna:<8}{token.tipo.name:<16}{lexema}")
    return "\n".join(linhas)


def ler_arquivo(caminho):
    """Lê o código-fonte; devolve (codigo, mensagem_de_erro)."""
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return arquivo.read(), None
    except FileNotFoundError:
        return None, f"Erro: o arquivo '{caminho}' não foi encontrado."
    except UnicodeDecodeError:
        return None, f"Erro: o arquivo '{caminho}' não está em UTF-8."
    except OSError as erro:
        return None, f"Erro: não foi possível ler '{caminho}': {erro.strerror}."


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        prog="python -m minilang",
        description="Analisador léxico da MiniLang: lista os tokens de um arquivo .min.",
    )
    parser.add_argument("arquivo", help="caminho do programa MiniLang (ex.: examples/valido.min)")
    args = parser.parse_args(argv)

    codigo, erro_leitura = ler_arquivo(args.arquivo)
    if erro_leitura:
        print(erro_leitura)
        return 2

    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()

    print(f"Analisando: {args.arquivo}\n")
    print("Tokens gerados:")
    print(formatar_tabela(tokens))
    print()

    if lexer.tem_erros:
        print(f"{len(lexer.erros)} erro(s) léxico(s) encontrado(s):")
        for erro in lexer.erros:
            print(f"  {erro}")
        return 1

    print("Nenhum erro léxico encontrado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
