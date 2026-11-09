import unittest
from pathlib import Path

from minilang.ast import (
    BinaryOpNode,
    IfStmtNode,
    LiteralNode,
    VarAccessNode,
    WhileStmtNode,
    WriteStmtNode,
    formatar_ast,
)
from minilang.interpreter import ErroExecucao, Interpretador
from minilang.lexer import Lexer
from minilang.optimizer import ALGEBRICA, CODIGO_MORTO, DOBRAMENTO, Otimizador
from minilang.parser import Parser
from minilang.semantic import AnalisadorSemantico

EXEMPLOS = Path(__file__).resolve().parent.parent / "examples"


def compilar(fonte):
    lexer = Lexer(fonte)
    parser = Parser(lexer.tokenizar())
    arvore = parser.parse()
    assert not lexer.tem_erros and not parser.tem_erros
    semantico = AnalisadorSemantico()
    semantico.analisar(arvore)
    assert not semantico.tem_erros, semantico.erros
    return arvore


def otimizar(corpo):
    arvore = compilar("programa t {\n" + corpo + "\n} fim.")
    otimizador = Otimizador()
    return arvore, otimizador.otimizar(arvore), otimizador


def saida_de(arvore, entradas=()):
    saida = []
    fila = list(entradas)
    interpretador = Interpretador(entrada=lambda nome: fila.pop(0), saida=saida.append)
    interpretador.executar(arvore)
    return saida


def expressao_da_atribuicao(arvore):
    return arvore.comandos[0].expressao


class TestDobramentoDeConstantes(unittest.TestCase):
    def test_aritmetica_vira_literal(self):
        _, nova, otimizador = otimizar("var x: inteiro; x = 2 * 3 + 4;")
        expressao = expressao_da_atribuicao(nova)
        self.assertIsInstance(expressao, LiteralNode)
        self.assertEqual(expressao.valor, 10)
        self.assertEqual(expressao.tipo, "inteiro")
        self.assertEqual(otimizador.contagem()[DOBRAMENTO], 2)

    def test_relacional_vira_booleano(self):
        _, nova, _ = otimizar("var b: booleano; b = 3 < 5;")
        expressao = expressao_da_atribuicao(nova)
        self.assertIs(expressao.valor, True)
        self.assertEqual(expressao.tipo, "booleano")

    def test_logico_e_unario(self):
        _, nova, _ = otimizar("var b: booleano; b = verdadeiro e não falso;")
        self.assertIs(expressao_da_atribuicao(nova).valor, True)

    def test_unario_menos_sobre_literal(self):
        _, nova, _ = otimizar("var x: inteiro; x = -(2 + 3);")
        self.assertEqual(expressao_da_atribuicao(nova).valor, -5)

    def test_divisao_inteira_segue_a_semantica_do_interpretador(self):
        _, nova, _ = otimizar("var x: inteiro; x = -7 / 2;")
        self.assertEqual(expressao_da_atribuicao(nova).valor, -3)

    def test_divisao_por_zero_literal_nao_e_dobrada(self):
        arvore = compilar_sem_semantica("var x: inteiro; x = 4 / 0;")
        nova = Otimizador().otimizar(arvore)
        self.assertIsInstance(expressao_da_atribuicao(nova), BinaryOpNode)

    def test_tipo_inferido_do_literal_novo(self):
        _, nova, _ = otimizar("var x: inteiro; x = 1 + 2;")
        self.assertEqual(expressao_da_atribuicao(nova).tipo_inferido, "inteiro")

    def test_nao_altera_variaveis(self):
        _, nova, otimizador = otimizar("var x: inteiro; var y: inteiro; y = 1; x = y + 2;")
        self.assertIsInstance(expressao_da_atribuicao_n(nova, 1), BinaryOpNode)
        self.assertEqual(otimizador.total, 0)


def compilar_sem_semantica(corpo):
    lexer = Lexer("programa t {\n" + corpo + "\n} fim.")
    parser = Parser(lexer.tokenizar())
    return parser.parse()


def expressao_da_atribuicao_n(arvore, indice):
    return arvore.comandos[indice].expressao


class TestSimplificacaoAlgebrica(unittest.TestCase):
    DECLARACOES = "var x: inteiro; var b: booleano; var r: inteiro; var t: booleano;"

    def simplificar(self, expressao, destino="r"):
        _, nova, otimizador = otimizar(f"{self.DECLARACOES} {destino} = {expressao};")
        return nova.comandos[0].expressao, otimizador

    def conferir_variavel(self, expressao, nome, destino="r"):
        resultado, otimizador = self.simplificar(expressao, destino)
        self.assertIsInstance(resultado, VarAccessNode)
        self.assertEqual(resultado.nome, nome)
        self.assertEqual(otimizador.contagem()[ALGEBRICA], 1)

    def conferir_literal(self, expressao, valor, destino="r"):
        resultado, otimizador = self.simplificar(expressao, destino)
        self.assertIsInstance(resultado, LiteralNode)
        self.assertEqual(resultado.valor, valor)
        self.assertIs(type(resultado.valor), type(valor))
        self.assertEqual(otimizador.contagem()[ALGEBRICA], 1)

    def test_soma_com_zero(self):
        self.conferir_variavel("x + 0", "x")
        self.conferir_variavel("0 + x", "x")

    def test_subtracao_de_zero(self):
        self.conferir_variavel("x - 0", "x")

    def test_multiplicacao_por_um(self):
        self.conferir_variavel("x * 1", "x")
        self.conferir_variavel("1 * x", "x")

    def test_multiplicacao_por_zero(self):
        self.conferir_literal("x * 0", 0)
        self.conferir_literal("0 * x", 0)

    def test_divisao_por_um(self):
        self.conferir_variavel("x / 1", "x")

    def test_resto_por_um(self):
        self.conferir_literal("x % 1", 0)

    def test_e_com_verdadeiro(self):
        self.conferir_variavel("b e verdadeiro", "b", "t")
        self.conferir_variavel("verdadeiro e b", "b", "t")

    def test_ou_com_falso(self):
        self.conferir_variavel("b ou falso", "b", "t")
        self.conferir_variavel("falso ou b", "b", "t")

    def test_e_com_falso_a_esquerda_dispensa_o_lado_direito(self):
        self.conferir_literal("falso e (x / x == 1)", False, "t")

    def test_ou_com_verdadeiro_a_esquerda(self):
        self.conferir_literal("verdadeiro ou (x / x == 1)", True, "t")

    def test_e_com_falso_a_direita_com_esquerda_segura(self):
        self.conferir_literal("(x > 1) e falso", False, "t")

    def test_ou_com_verdadeiro_a_direita_com_esquerda_segura(self):
        self.conferir_literal("(x > 1) ou verdadeiro", True, "t")

    def test_dupla_negacao(self):
        self.conferir_variavel("não não b", "b", "t")

    def test_duplo_menos(self):
        self.conferir_variavel("-(-x)", "x")

    def test_expressao_sem_padrao_nao_muda(self):
        resultado, otimizador = self.simplificar("x * 2 + 3")
        self.assertIsInstance(resultado, BinaryOpNode)
        self.assertEqual(otimizador.total, 0)


class TestPreservacaoDeErros(unittest.TestCase):
    def test_multiplicar_por_zero_nao_apaga_divisao_que_pode_falhar(self):
        _, nova, otimizador = otimizar(
            "var z: inteiro; var r: inteiro; r = (1 / z) * 0;"
        )
        self.assertIsInstance(expressao_da_atribuicao_n(nova, 0), BinaryOpNode)
        self.assertEqual(otimizador.total, 0)
        with self.assertRaises(ErroExecucao):
            saida_de(nova)

    def test_e_com_falso_a_direita_so_simplifica_se_esquerda_for_segura(self):
        _, nova, otimizador = otimizar(
            "var z: inteiro; var b: booleano; b = (1 / z == 1) e falso;"
        )
        self.assertIsInstance(expressao_da_atribuicao_n(nova, 0), BinaryOpNode)
        self.assertEqual(otimizador.total, 0)

    def test_multiplicar_por_zero_com_expressao_segura(self):
        _, nova, _ = otimizar("var x: inteiro; var r: inteiro; r = (x + 3 * 2) * 0;")
        self.assertEqual(expressao_da_atribuicao_n(nova, 0).valor, 0)

    def test_divisao_por_literal_nao_nulo_e_segura(self):
        _, nova, _ = otimizar("var x: inteiro; var r: inteiro; r = (x / 2) * 0;")
        self.assertEqual(expressao_da_atribuicao_n(nova, 0).valor, 0)


class TestCodigoMorto(unittest.TestCase):
    def test_se_verdadeiro_mantem_apenas_o_ramo_entao(self):
        _, nova, otimizador = otimizar("se (verdadeiro) { escreva(1); } senão { escreva(2); }")
        self.assertEqual(len(nova.comandos), 1)
        self.assertIsInstance(nova.comandos[0], WriteStmtNode)
        self.assertEqual(nova.comandos[0].expressao.valor, 1)
        self.assertEqual(otimizador.contagem()[CODIGO_MORTO], 1)

    def test_se_falso_mantem_apenas_o_ramo_senao(self):
        _, nova, _ = otimizar("se (falso) { escreva(1); } senão { escreva(2); }")
        self.assertEqual(len(nova.comandos), 1)
        self.assertEqual(nova.comandos[0].expressao.valor, 2)

    def test_se_falso_sem_senao_desaparece(self):
        _, nova, _ = otimizar("se (1 > 2) { escreva(1); }")
        self.assertEqual(nova.comandos, [])

    def test_enquanto_falso_desaparece(self):
        _, nova, otimizador = otimizar("enquanto (1 == 2) { escreva(1); } escreva(0);")
        self.assertEqual(len(nova.comandos), 1)
        self.assertEqual(otimizador.contagem()[CODIGO_MORTO], 1)

    def test_enquanto_verdadeiro_e_mantido(self):
        _, nova, _ = otimizar("var i: inteiro; enquanto (i < 3) { i = i + 1; }")
        self.assertIsInstance(nova.comandos[0], WhileStmtNode)

    def test_condicional_nao_constante_e_mantido(self):
        _, nova, otimizador = otimizar("var x: inteiro; se (x > 0) { escreva(1); } senão { escreva(2); }")
        self.assertIsInstance(nova.comandos[0], IfStmtNode)
        self.assertEqual(otimizador.total, 0)

    def test_blocos_internos_tambem_sao_otimizados(self):
        _, nova, _ = otimizar(
            "var x: inteiro; se (x > 0) { escreva(1 + 1); se (falso) { escreva(9); } }"
        )
        interno = nova.comandos[0].entao_comandos
        self.assertEqual(len(interno), 1)
        self.assertEqual(interno[0].expressao.valor, 2)

    def test_corpo_de_procedimento_e_otimizado(self):
        _, nova, _ = otimizar("procedimento p() { escreva(2 * 5); } p();")
        procedimento = nova.declaracoes[0]
        self.assertEqual(procedimento.comandos[0].expressao.valor, 10)

    def test_argumentos_de_chamada_sao_otimizados(self):
        _, nova, _ = otimizar("procedimento p(a: inteiro) { escreva(a); } p(1 + 2);")
        self.assertEqual(nova.comandos[0].argumentos[0].valor, 3)

    def test_ramo_inlinado_preserva_a_ordem_dos_comandos(self):
        _, nova, _ = otimizar(
            "escreva(1); se (verdadeiro) { escreva(2); escreva(3); } escreva(4);"
        )
        self.assertEqual([c.expressao.valor for c in nova.comandos], [1, 2, 3, 4])


class TestNaoMutaOriginal(unittest.TestCase):
    def test_arvore_original_permanece_intacta(self):
        original, nova, _ = otimizar("var x: inteiro; x = 2 * 3;")
        self.assertIsInstance(expressao_da_atribuicao(original), BinaryOpNode)
        self.assertIsInstance(expressao_da_atribuicao(nova), LiteralNode)
        self.assertIsNot(original, nova)

    def test_otimizar_duas_vezes_e_estavel(self):
        _, nova, _ = otimizar("var x: inteiro; x = 2 * 3 + 0;")
        segundo = Otimizador()
        segundo.otimizar(nova)
        self.assertEqual(segundo.total, 0)

    def test_registros_trazem_posicao_e_descricao(self):
        _, _, otimizador = otimizar("var x: inteiro; x = 2 * 3;")
        registro = otimizador.registros[0]
        self.assertEqual(registro.tipo, DOBRAMENTO)
        self.assertGreater(registro.linha, 0)
        self.assertIn("2 * 3", registro.descricao)
        self.assertTrue(str(registro).startswith("[linha "))


class TestEquivalenciaSemantica(unittest.TestCase):
    def conferir(self, fonte, entradas=()):
        arvore = compilar(fonte)
        otimizada = Otimizador().otimizar(arvore)
        self.assertEqual(saida_de(arvore, entradas), saida_de(otimizada, entradas))

    def test_exemplos_com_saida_deterministica(self):
        for nome in ["fatorial", "recursao", "escopo_e_valor", "otimizacao", "procedimento", "valido"]:
            arquivo = EXEMPLOS / f"{nome}.min"
            with self.subTest(exemplo=nome):
                self.conferir(arquivo.read_text(encoding="utf-8"))

    def test_programa_misto(self):
        self.conferir(
            """
            programa misto {
                var i: inteiro;
                var acc: inteiro;
                var ok: booleano;
                procedimento mostrar(v: inteiro, flag: booleano) {
                    se (flag e v > 3 * 2) { escreva(v * 1 + 0); } senão { escreva(0 - v); }
                }
                i = 0;
                acc = 10 / 3 + 7 % 4;
                ok = acc > 5 ou falso;
                enquanto (i < 4 + 2) {
                    mostrar(i + acc, ok e verdadeiro);
                    i = i + 1;
                }
                se (1 == 1) { escreva(acc * 0 + i); }
            } fim.
            """
        )

    def test_entrada_dependente(self):
        fonte = """
        programa p {
            var a: inteiro;
            leia(a);
            se (a > 0 + 0) { escreva(a * 1); } senão { escreva(-a - 0); }
        } fim.
        """
        self.conferir(fonte, ["5"])
        self.conferir(fonte, ["-5"])


class TestFormatarASTOtimizada(unittest.TestCase):
    def test_ast_otimizada_e_menor(self):
        original, nova, _ = otimizar("var x: inteiro; x = 2 * 3 + 4;")
        self.assertLess(len(formatar_ast(nova)), len(formatar_ast(original)))
        self.assertIn("Literal: 10 (inteiro)", formatar_ast(nova))


if __name__ == "__main__":
    unittest.main()
