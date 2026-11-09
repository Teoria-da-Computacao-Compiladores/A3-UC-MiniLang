import argparse
import sys

from minilang.ast import formatar_ast
from minilang.interpreter import ErroExecucao, Interpretador
from minilang.lexer import Lexer, TokenType
from minilang.optimizer import Otimizador
from minilang.parser import Parser
from minilang.semantic import AnalisadorSemantico, formatar_tabela_simbolos


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
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return arquivo.read(), None
    except FileNotFoundError:
        return None, f"Erro: o arquivo '{caminho}' não foi encontrado."
    except UnicodeDecodeError:
        return None, f"Erro: o arquivo '{caminho}' não está em UTF-8."
    except OSError as erro:
        return None, f"Erro: não foi possível ler '{caminho}': {erro.strerror}."


def formatar_relatorio_otimizacao(otimizador: Otimizador) -> str:
    if otimizador.total == 0:
        return "Nenhuma otimização aplicável neste programa."
    linhas = [f"  {registro}" for registro in otimizador.registros]
    resumo = ", ".join(f"{quantidade} de {tipo}" for tipo, quantidade in otimizador.contagem().items() if quantidade)
    linhas.append(f"Total: {otimizador.total} otimização(ões) ({resumo}).")
    return "\n".join(linhas)


def executar_programa(arvore) -> int:
    interpretador = Interpretador()
    try:
        interpretador.executar(arvore)
    except ErroExecucao as erro:
        print(f"\n{erro}")
        return 3
    print(
        f"\nExecução concluída: {interpretador.passos} passo(s), "
        f"{interpretador.chamadas} chamada(s) de procedimento, "
        f"profundidade máxima da pilha de ativação: {interpretador.profundidade_maxima}."
    )
    return 0


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    arg_parser = argparse.ArgumentParser(
        prog="python -m minilang",
        description="Compilador da MiniLang: análise léxica, sintática e semântica, otimização e execução.",
    )
    arg_parser.add_argument("arquivo", help="caminho do programa MiniLang (ex.: examples/valido.min)")
    arg_parser.add_argument("--ast", action="store_true", help="imprime a Árvore Sintática Abstrata (AST) anotada com os tipos inferidos")
    arg_parser.add_argument("--simbolos", action="store_true", help="imprime a tabela de símbolos (M3)")
    arg_parser.add_argument("--otimizar", action="store_true", help="aplica as otimizações à AST e imprime o relatório (M4)")
    arg_parser.add_argument("--executar", action="store_true", help="executa o programa interpretando a AST (M4)")
    arg_parser.add_argument("--sem-tokens", action="store_true", help="não imprime a tabela de tokens")
    args = arg_parser.parse_args(argv)

    codigo, erro_leitura = ler_arquivo(args.arquivo)
    if erro_leitura:
        print(erro_leitura)
        return 2

    lexer = Lexer(codigo)
    tokens = lexer.tokenizar()

    print(f"Analisando: {args.arquivo}\n")
    if not args.sem_tokens:
        print("Tokens gerados:")
        print(formatar_tabela(tokens))
        print()

    if lexer.tem_erros:
        print(f"{len(lexer.erros)} erro(s) léxico(s) encontrado(s):")
        for erro in lexer.erros:
            print(f"  {erro}")
        return 1

    print("Nenhum erro léxico encontrado.")

    sintatico = Parser(tokens)
    arvore = sintatico.parse()

    if sintatico.tem_erros:
        print(f"\n{len(sintatico.erros)} erro(s) sintático(s) encontrado(s):")
        for erro in sintatico.erros:
            print(f"  {erro}")
        return 1

    print("\nAnálise sintática concluída com sucesso: programa sintaticamente correto.")

    if arvore is None:
        return 1

    semantico = AnalisadorSemantico()
    semantico.analisar(arvore)

    if args.ast:
        print("\nÁrvore Sintática Abstrata (AST):")
        print(formatar_ast(arvore))

    if args.simbolos:
        print("\nTabela de símbolos:")
        print(formatar_tabela_simbolos(semantico.tabela))

    if semantico.tem_erros:
        print(f"\n{len(semantico.erros)} erro(s) semântico(s) encontrado(s):")
        for erro in semantico.erros:
            print(f"  {erro}")
        return 1

    print("\nAnálise semântica concluída com sucesso: programa semanticamente correto.")

    if args.otimizar:
        otimizador = Otimizador()
        arvore = otimizador.otimizar(arvore)
        print("\nOtimizações aplicadas:")
        print(formatar_relatorio_otimizacao(otimizador))
        if args.ast:
            print("\nÁrvore Sintática Abstrata otimizada:")
            print(formatar_ast(arvore))

    if args.executar:
        print("\nExecução:")
        return executar_programa(arvore)

    return 0


if __name__ == "__main__":
    sys.exit(main())
