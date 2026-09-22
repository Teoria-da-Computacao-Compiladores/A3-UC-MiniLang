import os
import subprocess
import sys
import unittest
from pathlib import Path

from minilang.__main__ import formatar_tabela
from minilang.lexer import Lexer, TokenType

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLOS = RAIZ / "examples"


def analisar_exemplo(nome):
    lexer = Lexer((EXEMPLOS / nome).read_text(encoding="utf-8"))
    return lexer.tokenizar(), lexer.erros


def rodar_cli(*args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, *args],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", env=env,
    )


class TestExemplos(unittest.TestCase):

    def test_exemplos_validos_nao_tem_erros(self):
        for nome in ["valido.min", "comentarios.min", "operadores.min"]:
            with self.subTest(exemplo=nome):
                tokens, erros = analisar_exemplo(nome)
                self.assertEqual(erros, [])
                self.assertEqual(tokens[-1].tipo, TokenType.EOF)

    def test_valido_comeca_com_a_estrutura_do_programa(self):
        tokens, _ = analisar_exemplo("valido.min")

        self.assertEqual(
            [t.tipo for t in tokens[:4]],
            [TokenType.PROGRAMA, TokenType.IDENTIFICADOR, TokenType.ABRE_CHAVE, TokenType.VAR],
        )
        self.assertEqual((tokens[0].linha, tokens[0].coluna), (3, 1))
        self.assertEqual([t.tipo for t in tokens[-3:]], [TokenType.FIM, TokenType.PONTO, TokenType.EOF])

    def test_comentarios_nao_geram_tokens(self):
        tokens, _ = analisar_exemplo("comentarios.min")

        self.assertFalse(any("#" in t.lexema for t in tokens))
        self.assertFalse(any(t.lexema == "declaração" for t in tokens))

    def test_operadores_reconhece_todos_os_operadores(self):
        tokens, _ = analisar_exemplo("operadores.min")
        tipos = {t.tipo for t in tokens}

        esperados = {
            TokenType.SOMA, TokenType.SUBTRACAO, TokenType.MULTIPLICACAO,
            TokenType.DIVISAO, TokenType.MODULO, TokenType.IGUAL, TokenType.DIFERENTE,
            TokenType.MENOR, TokenType.MENOR_IGUAL, TokenType.MAIOR, TokenType.MAIOR_IGUAL,
            TokenType.ATRIBUICAO, TokenType.E, TokenType.OU, TokenType.NAO,
        }
        self.assertTrue(esperados <= tipos, esperados - tipos)

    def test_erro_lexico_aponta_linha_e_coluna_do_arroba(self):
        _, erros = analisar_exemplo("erro_lexico.min")

        self.assertEqual(len(erros), 1)
        self.assertEqual((erros[0].linha, erros[0].coluna), (7, 12))

    def test_erros_multiplos_reporta_todos_em_uma_execucao(self):
        _, erros = analisar_exemplo("erros_multiplos.min")

        self.assertEqual(
            [(e.linha, e.coluna) for e in erros],
            [(4, 9), (5, 13), (6, 19), (7, 9)],
        )


class TestLinhaDeComando(unittest.TestCase):

    def test_arquivo_valido_imprime_tabela_e_sai_com_zero(self):
        resultado = rodar_cli("-m", "minilang", "examples/valido.min")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("Linha  Coluna  Tipo", resultado.stdout)
        self.assertIn("PROGRAMA", resultado.stdout)
        self.assertIn("Nenhum erro léxico encontrado.", resultado.stdout)

    def test_arquivo_com_erro_lista_erros_e_sai_com_um(self):
        resultado = rodar_cli("-m", "minilang", "examples/erro_lexico.min")

        self.assertEqual(resultado.returncode, 1)
        self.assertIn("Erro léxico [linha 7, coluna 12]: caractere inválido '@'", resultado.stdout)

    def test_arquivo_inexistente_sai_com_dois(self):
        resultado = rodar_cli("-m", "minilang", "examples/nao_existe.min")

        self.assertEqual(resultado.returncode, 2)
        self.assertIn("não foi encontrado", resultado.stdout)

    def test_sem_argumento_mostra_uso(self):
        resultado = rodar_cli("-m", "minilang")

        self.assertEqual(resultado.returncode, 2)
        self.assertIn("usage", resultado.stderr.lower())

    def test_comando_antigo_continua_funcionando(self):
        resultado = rodar_cli("minilang/lexer.py", "examples/valido.min")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("Nenhum erro léxico encontrado.", resultado.stdout)

    def test_tabela_mostra_fim_da_entrada_no_eof(self):
        tabela = formatar_tabela(Lexer("x").tokenizar())

        self.assertIn("EOF", tabela)
        self.assertIn("(fim da entrada)", tabela)


if __name__ == "__main__":
    unittest.main()
