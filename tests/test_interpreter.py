import unittest

from minilang.interpreter import (
    ErroExecucao,
    Interpretador,
    aplicar_binaria,
    dividir,
    formatar_valor,
    resto,
)
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.semantic import AnalisadorSemantico


def compilar(fonte):
    lexer = Lexer(fonte)
    tokens = lexer.tokenizar()
    assert not lexer.tem_erros, lexer.erros
    parser = Parser(tokens)
    arvore = parser.parse()
    assert not parser.tem_erros, parser.erros
    semantico = AnalisadorSemantico()
    semantico.analisar(arvore)
    assert not semantico.tem_erros, semantico.erros
    return arvore


def executar(corpo, entradas=(), **opcoes):
    fonte = "programa t {\n" + corpo + "\n} fim."
    saida = []
    fila = list(entradas)

    def entrada(nome):
        if not fila:
            raise EOFError
        return fila.pop(0)

    interpretador = Interpretador(entrada=entrada, saida=saida.append, **opcoes)
    interpretador.executar(compilar(fonte))
    return saida, interpretador


class TestAritmetica(unittest.TestCase):
    def test_divisao_trunca_em_direcao_a_zero(self):
        self.assertEqual(dividir(7, 2), 3)
        self.assertEqual(dividir(-7, 2), -3)
        self.assertEqual(dividir(7, -2), -3)
        self.assertEqual(dividir(-7, -2), 3)

    def test_resto_tem_o_sinal_do_dividendo(self):
        self.assertEqual(resto(7, 3), 1)
        self.assertEqual(resto(-7, 3), -1)
        self.assertEqual(resto(7, -3), 1)

    def test_divisao_por_zero_levanta_excecao(self):
        with self.assertRaises(ZeroDivisionError):
            dividir(1, 0)
        with self.assertRaises(ZeroDivisionError):
            aplicar_binaria("%", 1, 0)

    def test_formatar_valor(self):
        self.assertEqual(formatar_valor(True), "verdadeiro")
        self.assertEqual(formatar_valor(False), "falso")
        self.assertEqual(formatar_valor(-4), "-4")


class TestExecucaoBasica(unittest.TestCase):
    def test_escreva_expressao(self):
        saida, _ = executar("escreva(2 + 3 * 4);")
        self.assertEqual(saida, ["14"])

    def test_variaveis_comecam_com_valor_padrao(self):
        saida, _ = executar("var n: inteiro; var b: booleano; escreva(n); escreva(b);")
        self.assertEqual(saida, ["0", "falso"])

    def test_atribuicao_e_aritmetica(self):
        saida, _ = executar("var x: inteiro; x = 10; x = x * 2 - 3; escreva(x);")
        self.assertEqual(saida, ["17"])

    def test_divisao_e_resto_inteiros(self):
        saida, _ = executar("escreva(-7 / 2); escreva(-7 % 3); escreva(17 / 5);")
        self.assertEqual(saida, ["-3", "-1", "3"])

    def test_operadores_relacionais_e_logicos(self):
        saida, _ = executar(
            "escreva(1 < 2); escreva(2 <= 1); escreva(3 == 3); escreva(3 != 3);"
            "escreva(verdadeiro e falso); escreva(verdadeiro ou falso); escreva(não falso);"
        )
        self.assertEqual(
            saida, ["verdadeiro", "falso", "verdadeiro", "falso", "falso", "verdadeiro", "verdadeiro"]
        )

    def test_unario_menos(self):
        saida, _ = executar("var x: inteiro; x = 5; escreva(-x); escreva(-(-x));")
        self.assertEqual(saida, ["-5", "5"])

    def test_se_senao(self):
        corpo = (
            "var x: inteiro; leia(x);"
            "se (x > 0) { escreva(1); } senão { escreva(2); }"
        )
        self.assertEqual(executar(corpo, ["5"])[0], ["1"])
        self.assertEqual(executar(corpo, ["-5"])[0], ["2"])

    def test_se_sem_senao_com_condicao_falsa(self):
        saida, _ = executar("se (1 > 2) { escreva(1); } escreva(2);")
        self.assertEqual(saida, ["2"])

    def test_enquanto_soma_de_1_a_10(self):
        saida, _ = executar(
            "var i: inteiro; var s: inteiro; i = 1; s = 0;"
            "enquanto (i <= 10) { s = s + i; i = i + 1; } escreva(s);"
        )
        self.assertEqual(saida, ["55"])

    def test_enquanto_que_nunca_executa(self):
        saida, _ = executar("enquanto (1 > 2) { escreva(1); } escreva(0);")
        self.assertEqual(saida, ["0"])


class TestCurtoCircuito(unittest.TestCase):
    def test_e_nao_avalia_lado_direito_quando_falso(self):
        saida, _ = executar("var z: inteiro; escreva(falso e (10 / z == 1));")
        self.assertEqual(saida, ["falso"])

    def test_ou_nao_avalia_lado_direito_quando_verdadeiro(self):
        saida, _ = executar("var z: inteiro; escreva(verdadeiro ou (10 / z == 1));")
        self.assertEqual(saida, ["verdadeiro"])

    def test_sem_curto_circuito_o_erro_aparece(self):
        with self.assertRaises(ErroExecucao):
            executar("var z: inteiro; escreva(verdadeiro e (10 / z == 1));")


class TestEntrada(unittest.TestCase):
    def test_leia_inteiro_com_espacos_e_sinal(self):
        saida, _ = executar("var a: inteiro; leia(a); escreva(a + 1);", ["  -41  \n"])
        self.assertEqual(saida, ["-40"])

    def test_leia_booleano(self):
        saida, _ = executar("var b: booleano; leia(b); escreva(não b);", ["verdadeiro"])
        self.assertEqual(saida, ["falso"])

    def test_leia_inteiro_invalido(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("var a: inteiro; leia(a);", ["abc"])
        self.assertIn("esperado inteiro", contexto.exception.mensagem)

    def test_leia_booleano_invalido(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("var b: booleano; leia(b);", ["1"])
        self.assertIn("'verdadeiro' ou 'falso'", contexto.exception.mensagem)

    def test_leia_sem_dados_disponiveis(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("var a: inteiro; leia(a);")
        self.assertIn("fim da entrada", contexto.exception.mensagem)

    def test_leia_em_parametro(self):
        saida, _ = executar(
            "procedimento p(a: inteiro) { leia(a); escreva(a); } p(0);", ["9"]
        )
        self.assertEqual(saida, ["9"])


class TestProcedimentos(unittest.TestCase):
    def test_chamada_com_parametros_e_local(self):
        saida, interpretador = executar(
            "procedimento soma(a: inteiro, b: inteiro) { var t: inteiro; t = a + b; escreva(t); }"
            "soma(2, 3);"
        )
        self.assertEqual(saida, ["5"])
        self.assertEqual(interpretador.chamadas, 1)

    def test_passagem_por_valor(self):
        saida, _ = executar(
            "var x: inteiro;"
            "procedimento mexer(v: inteiro) { v = v + 100; escreva(v); }"
            "x = 1; mexer(x); escreva(x);"
        )
        self.assertEqual(saida, ["101", "1"])

    def test_local_oculta_global(self):
        saida, _ = executar(
            "var g: inteiro;"
            "procedimento p() { var g: inteiro; g = 7; escreva(g); }"
            "g = 50; p(); escreva(g);"
        )
        self.assertEqual(saida, ["7", "50"])

    def test_procedimento_altera_global(self):
        saida, _ = executar(
            "var c: inteiro; procedimento inc() { c = c + 1; } inc(); inc(); inc(); escreva(c);"
        )
        self.assertEqual(saida, ["3"])

    def test_locais_sao_reiniciadas_a_cada_chamada(self):
        saida, _ = executar(
            "procedimento p() { var n: inteiro; n = n + 1; escreva(n); } p(); p();"
        )
        self.assertEqual(saida, ["1", "1"])

    def test_recursao(self):
        saida, interpretador = executar(
            "procedimento c(n: inteiro) { se (n > 0) { escreva(n); c(n - 1); } } c(3);"
        )
        self.assertEqual(saida, ["3", "2", "1"])
        self.assertEqual(interpretador.chamadas, 4)
        self.assertEqual(interpretador.profundidade_maxima, 4)

    def test_recursao_mutua_com_declaracao_posterior(self):
        saida, _ = executar(
            "procedimento par(n: inteiro) { se (n == 0) { escreva(verdadeiro); } senão { impar(n - 1); } }"
            "procedimento impar(n: inteiro) { se (n == 0) { escreva(falso); } senão { par(n - 1); } }"
            "par(7);"
        )
        self.assertEqual(saida, ["falso"])

    def test_argumento_e_avaliado_no_quadro_do_chamador(self):
        saida, _ = executar(
            "var a: inteiro; procedimento p(a: inteiro) { escreva(a); } a = 4; p(a * 2); escreva(a);"
        )
        self.assertEqual(saida, ["8", "4"])

    def test_estouro_da_pilha_de_ativacao(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("procedimento p(n: inteiro) { p(n + 1); } p(0);", limite_pilha=20)
        self.assertIn("estouro da pilha de ativação", contexto.exception.mensagem)

    def test_pilha_e_restaurada_apos_erro(self):
        fonte = "programa t { var z: inteiro; procedimento p() { escreva(1 / z); } p(); } fim."
        interpretador = Interpretador(saida=lambda texto: None)
        with self.assertRaises(ErroExecucao):
            interpretador.executar(compilar(fonte))
        self.assertEqual(len(interpretador.pilha), 1)


class TestErrosDeExecucao(unittest.TestCase):
    def test_divisao_por_zero_em_tempo_de_execucao(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("var z: inteiro; escreva(5 / z);")
        erro = contexto.exception
        self.assertEqual(erro.mensagem, "divisão por zero")
        self.assertTrue(str(erro).startswith("Erro de execução [linha "))

    def test_resto_por_zero_em_tempo_de_execucao(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("var z: inteiro; escreva(5 % z);")
        self.assertIn("resto", contexto.exception.mensagem)

    def test_laco_infinito_e_interrompido(self):
        with self.assertRaises(ErroExecucao) as contexto:
            executar("enquanto (verdadeiro) { }", limite_passos=1000)
        self.assertIn("limite de 1000 passos", contexto.exception.mensagem)

    def test_saida_anterior_ao_erro_e_preservada(self):
        saida = []
        interpretador = Interpretador(saida=saida.append)
        arvore = compilar("programa t { var z: inteiro; escreva(1); escreva(1 / z); } fim.")
        with self.assertRaises(ErroExecucao):
            interpretador.executar(arvore)
        self.assertEqual(saida, ["1"])


class TestContadores(unittest.TestCase):
    def test_passos_sao_contados(self):
        _, interpretador = executar("var x: inteiro; x = 1; x = 2; escreva(x);")
        self.assertEqual(interpretador.passos, 3)

    def test_interpretador_pode_ser_reutilizado(self):
        arvore = compilar("programa t { escreva(1); } fim.")
        saida = []
        interpretador = Interpretador(saida=saida.append)
        interpretador.executar(arvore)
        interpretador.executar(arvore)
        self.assertEqual(saida, ["1", "1"])
        self.assertEqual(interpretador.passos, 1)


if __name__ == "__main__":
    unittest.main()
