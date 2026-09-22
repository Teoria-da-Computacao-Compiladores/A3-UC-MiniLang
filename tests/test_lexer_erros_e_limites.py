import unittest

from minilang.lexer import ErroLexico, Lexer, TokenType


def tipos(codigo):
    return [token.tipo for token in Lexer(codigo).tokenizar()[:-1]]


class TestMensagensDeErro(unittest.TestCase):

    def test_caractere_invalido_gera_mensagem_com_posicao(self):
        lexer = Lexer("x = 10 @ 20;")
        lexer.tokenizar()

        self.assertEqual(len(lexer.erros), 1)
        erro = lexer.erros[0]
        self.assertEqual((erro.linha, erro.coluna), (1, 8))
        self.assertEqual(str(erro), "Erro léxico [linha 1, coluna 8]: caractere inválido '@'")

    def test_exclamacao_isolada_explica_como_corrigir(self):
        lexer = Lexer("a ! b")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[1].tipo, TokenType.ERRO)
        self.assertIn("'!' isolado", lexer.erros[0].mensagem)
        self.assertIn("'!='", lexer.erros[0].mensagem)

    def test_lexer_continua_depois_do_erro_e_acumula_todos(self):
        lexer = Lexer("x = 1 @ 2;\ny = $;\nz = ! 3;")
        tokens = lexer.tokenizar()

        posicoes = [(e.linha, e.coluna) for e in lexer.erros]
        self.assertEqual(posicoes, [(1, 7), (2, 5), (3, 5)])
        self.assertEqual(tokens[-1].tipo, TokenType.EOF)
        self.assertEqual(sum(t.tipo == TokenType.IDENTIFICADOR for t in tokens), 3)

    def test_codigo_valido_nao_tem_erros(self):
        lexer = Lexer("programa p { var x: inteiro; x = 1; } fim.")
        lexer.tokenizar()

        self.assertFalse(lexer.tem_erros)
        self.assertEqual(lexer.erros, [])

    def test_cada_erro_tambem_gera_token_erro(self):
        lexer = Lexer("@ $ &")
        tokens = lexer.tokenizar()

        erros_token = [t for t in tokens if t.tipo == TokenType.ERRO]
        self.assertEqual(len(erros_token), len(lexer.erros))
        for token, erro in zip(erros_token, lexer.erros):
            self.assertIsInstance(erro, ErroLexico)
            self.assertEqual((token.linha, token.coluna), (erro.linha, erro.coluna))


class TestNumerosEIdentificadoresMalFormados(unittest.TestCase):

    def test_numero_colado_em_letras_e_um_unico_erro(self):
        lexer = Lexer("x = 12abc;")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[2].tipo, TokenType.ERRO)
        self.assertEqual(tokens[2].lexema, "12abc")
        self.assertEqual(tokens[3].tipo, TokenType.PONTO_VIRGULA)
        self.assertIn("número mal formado '12abc'", lexer.erros[0].mensagem)

    def test_numero_seguido_de_sublinhado(self):
        lexer = Lexer("3_x")
        tokens = lexer.tokenizar()

        self.assertEqual([t.tipo for t in tokens[:-1]], [TokenType.ERRO])
        self.assertEqual(tokens[0].lexema, "3_x")

    def test_numero_seguido_de_simbolo_continua_valido(self):
        self.assertEqual(tipos("10;"), [TokenType.NUMERO, TokenType.PONTO_VIRGULA])
        self.assertEqual(tipos("10+2"), [TokenType.NUMERO, TokenType.SOMA, TokenType.NUMERO])

    def test_identificador_comecando_com_sublinhado(self):
        lexer = Lexer("_temp = 1")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[0].tipo, TokenType.ERRO)
        self.assertEqual(tokens[0].lexema, "_temp")
        self.assertIn("identificador inválido '_temp'", lexer.erros[0].mensagem)

    def test_digito_unicode_nao_faz_parte_do_identificador(self):
        lexer = Lexer("x² = 3")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[0].tipo, TokenType.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "x")
        self.assertEqual(tokens[1].tipo, TokenType.ERRO)
        self.assertEqual(tokens[1].lexema, "²")

    def test_digito_unicode_nao_e_numero(self):
        lexer = Lexer("٣")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[0].tipo, TokenType.ERRO)


class TestAlfabeto(unittest.TestCase):

    def test_identificador_com_acento_e_valido(self):
        tokens = Lexer("ação coração").tokenizar()

        self.assertEqual(tokens[0].tipo, TokenType.IDENTIFICADOR)
        self.assertEqual(tokens[0].lexema, "ação")
        self.assertEqual(tokens[1].lexema, "coração")

    def test_palavras_reservadas_sem_acento_sao_sinonimos(self):
        self.assertEqual(tipos("senao nao"), [TokenType.SENAO, TokenType.NAO])
        self.assertEqual(tipos("senão não"), [TokenType.SENAO, TokenType.NAO])

    def test_linguagem_diferencia_maiusculas(self):
        self.assertEqual(
            tipos("Programa FIM Se"),
            [TokenType.IDENTIFICADOR] * 3,
        )

    def test_espaco_nao_separavel_e_erro(self):
        lexer = Lexer("x = 1")
        tokens = lexer.tokenizar()

        self.assertEqual(tokens[1].tipo, TokenType.ERRO)
        self.assertEqual((lexer.erros[0].linha, lexer.erros[0].coluna), (1, 2))


class TestEspacosComentariosEPosicao(unittest.TestCase):

    def test_milhares_de_comentarios_seguidos_nao_estouram_recursao(self):
        codigo = "# comentário\n" * 5000 + "x"
        tokens = Lexer(codigo).tokenizar()

        self.assertEqual(tokens[0].tipo, TokenType.IDENTIFICADOR)
        self.assertEqual(tokens[0].linha, 5001)

    def test_comentario_na_ultima_linha_sem_quebra(self):
        tokens = Lexer("x = 1; # fim sem quebra de linha").tokenizar()

        self.assertEqual(tokens[-1].tipo, TokenType.EOF)
        self.assertEqual(len(tokens), 5)

    def test_comentario_no_meio_da_linha(self):
        self.assertEqual(
            tipos("x = 1; # comentário\ny = 2;"),
            [TokenType.IDENTIFICADOR, TokenType.ATRIBUICAO, TokenType.NUMERO,
             TokenType.PONTO_VIRGULA, TokenType.IDENTIFICADOR, TokenType.ATRIBUICAO,
             TokenType.NUMERO, TokenType.PONTO_VIRGULA],
        )

    def test_quebra_de_linha_windows(self):
        tokens = Lexer("var\r\n  x").tokenizar()

        self.assertEqual((tokens[1].linha, tokens[1].coluna), (2, 3))

    def test_tabulacao_conta_como_uma_coluna(self):
        tokens = Lexer("\tx").tokenizar()

        self.assertEqual((tokens[0].linha, tokens[0].coluna), (1, 2))

    def test_eof_fica_depois_do_ultimo_caractere(self):
        tokens = Lexer("x\ny").tokenizar()

        self.assertEqual((tokens[-1].linha, tokens[-1].coluna), (2, 2))

    def test_operadores_colados_sem_espaco(self):
        self.assertEqual(
            tipos("a<=b==c!=d>=f"),
            [TokenType.IDENTIFICADOR, TokenType.MENOR_IGUAL, TokenType.IDENTIFICADOR,
             TokenType.IGUAL, TokenType.IDENTIFICADOR, TokenType.DIFERENTE,
             TokenType.IDENTIFICADOR, TokenType.MAIOR_IGUAL, TokenType.IDENTIFICADOR],
        )

    def test_tres_iguais_viram_igual_e_atribuicao(self):
        self.assertEqual(tipos("==="), [TokenType.IGUAL, TokenType.ATRIBUICAO])

    def test_tokenizar_termina_com_um_unico_eof(self):
        tokens = Lexer("x").tokenizar()

        self.assertEqual([t.tipo for t in tokens].count(TokenType.EOF), 1)
        self.assertEqual(tokens[-1].tipo, TokenType.EOF)


if __name__ == "__main__":
    unittest.main()
