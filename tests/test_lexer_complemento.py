import unittest

from minilang.lexer import Lexer, TokenType


def obter_tokens(codigo):
    lexer = Lexer(codigo)
    tokens = []

    while True:
        token = lexer.proximo_token()
        tokens.append(token)

        if token.tipo == TokenType.EOF:
            break

    return tokens


class TestLexerCompleto(unittest.TestCase):

    def test_todas_palavras_reservadas(self):
        codigo = (
            "programa var inteiro booleano se senão "
            "enquanto escreva leia verdadeiro falso "
            "e ou não fim"
        )

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.PROGRAMA,
            TokenType.VAR,
            TokenType.INTEIRO,
            TokenType.BOOLEANO,
            TokenType.SE,
            TokenType.SENAO,
            TokenType.ENQUANTO,
            TokenType.ESCREVA,
            TokenType.LEIA,
            TokenType.VERDADEIRO,
            TokenType.FALSO,
            TokenType.E,
            TokenType.OU,
            TokenType.NAO,
            TokenType.FIM,
        ]

        self.assertEqual(tipos, esperados)

    def test_identificadores_validos(self):
        codigo = "x contador contador_1 numero2"

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.IDENTIFICADOR,
            TokenType.IDENTIFICADOR,
            TokenType.IDENTIFICADOR,
            TokenType.IDENTIFICADOR,
        ]

        self.assertEqual(tipos, esperados)

    def test_identificadores_parecidos_com_palavras_reservadas(self):
        codigo = "programa1 inteiro2 enquanto_1 escreva2"

        tokens = obter_tokens(codigo)

        for token in tokens[:-1]:
            self.assertEqual(token.tipo, TokenType.IDENTIFICADOR)

    def test_numeros(self):
        codigo = "0 1 10 123 99999"

        tokens = obter_tokens(codigo)

        for token in tokens[:-1]:
            self.assertEqual(token.tipo, TokenType.NUMERO)

    def test_operadores_aritmeticos(self):
        codigo = "+ - * / %"

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.SOMA,
            TokenType.SUBTRACAO,
            TokenType.MULTIPLICACAO,
            TokenType.DIVISAO,
            TokenType.MODULO,
        ]

        self.assertEqual(tipos, esperados)

    def test_operadores_relacionais(self):
        codigo = "== != < <= > >="

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.IGUAL,
            TokenType.DIFERENTE,
            TokenType.MENOR,
            TokenType.MENOR_IGUAL,
            TokenType.MAIOR,
            TokenType.MAIOR_IGUAL,
        ]

        self.assertEqual(tipos, esperados)

    def test_atribuicao(self):
        tokens = obter_tokens("=")

        self.assertEqual(tokens[0].tipo, TokenType.ATRIBUICAO)

    def test_delimitadores(self):
        codigo = "( ) { } ; : , ."

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.ABRE_PAREN,
            TokenType.FECHA_PAREN,
            TokenType.ABRE_CHAVE,
            TokenType.FECHA_CHAVE,
            TokenType.PONTO_VIRGULA,
            TokenType.DOIS_PONTOS,
            TokenType.VIRGULA,
            TokenType.PONTO,
        ]

        self.assertEqual(tipos, esperados)

    def test_operadores_logicos(self):
        codigo = "e ou não"

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.E,
            TokenType.OU,
            TokenType.NAO,
        ]

        self.assertEqual(tipos, esperados)

    def test_comentario(self):
        codigo = "var # comentário\ninteiro"

        tokens = obter_tokens(codigo)

        tipos = [token.tipo for token in tokens[:-1]]

        esperados = [
            TokenType.VAR,
            TokenType.INTEIRO,
        ]

        self.assertEqual(tipos, esperados)

    def test_erro_exclamacao_isolada(self):
        tokens = obter_tokens("!")

        self.assertEqual(tokens[0].tipo, TokenType.ERRO)
        self.assertEqual(tokens[0].lexema, "!")

    def test_caractere_invalido(self):
        tokens = obter_tokens("@")

        self.assertEqual(tokens[0].tipo, TokenType.ERRO)
        self.assertEqual(tokens[0].lexema, "@")

    def test_multiplos_caracteres_invalidos(self):
        tokens = obter_tokens("@ $ &")

        erros = [token for token in tokens if token.tipo == TokenType.ERRO]

        self.assertEqual(len(erros), 3)

    def test_linha_e_coluna(self):
        codigo = "var\n    x"

        tokens = obter_tokens(codigo)

        self.assertEqual(tokens[0].linha, 1)
        self.assertEqual(tokens[0].coluna, 1)

        self.assertEqual(tokens[1].linha, 2)
        self.assertEqual(tokens[1].coluna, 5)

    def test_eof(self):
        tokens = obter_tokens("")

        self.assertEqual(tokens[-1].tipo, TokenType.EOF)
        self.assertEqual(tokens[-1].linha, 1)
        self.assertEqual(tokens[-1].coluna, 1)


if __name__ == "__main__":
    unittest.main()