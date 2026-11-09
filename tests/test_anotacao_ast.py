import unittest

from minilang.ast import (
    AssignStmtNode,
    BinaryOpNode,
    IfStmtNode,
    LiteralNode,
    UnaryOpNode,
    VarAccessNode,
    formatar_ast,
)
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.semantic import AnalisadorSemantico


def analisar(corpo):
    lexer = Lexer("programa t {\n" + corpo + "\n} fim.")
    parser = Parser(lexer.tokenizar())
    arvore = parser.parse()
    assert not parser.tem_erros, parser.erros
    semantico = AnalisadorSemantico()
    semantico.analisar(arvore)
    return arvore, semantico


class TestAnotacaoDeTipos(unittest.TestCase):
    def test_literais_recebem_seus_tipos(self):
        arvore, _ = analisar("var x: inteiro; var b: booleano; x = 7; b = verdadeiro;")
        self.assertEqual(arvore.comandos[0].expressao.tipo_inferido, "inteiro")
        self.assertEqual(arvore.comandos[1].expressao.tipo_inferido, "booleano")

    def test_variavel_recebe_o_tipo_declarado(self):
        arvore, _ = analisar("var x: inteiro; var y: inteiro; y = x;")
        expressao = arvore.comandos[0].expressao
        self.assertIsInstance(expressao, VarAccessNode)
        self.assertEqual(expressao.tipo_inferido, "inteiro")

    def test_operadores_aritmeticos_e_relacionais(self):
        arvore, _ = analisar("var x: inteiro; var b: booleano; x = 1 + 2 * 3; b = x >= 2;")
        soma = arvore.comandos[0].expressao
        self.assertIsInstance(soma, BinaryOpNode)
        self.assertEqual(soma.tipo_inferido, "inteiro")
        self.assertEqual(soma.direita.tipo_inferido, "inteiro")
        self.assertEqual(arvore.comandos[1].expressao.tipo_inferido, "booleano")

    def test_operadores_logicos_e_unarios(self):
        arvore, _ = analisar("var b: booleano; var x: inteiro; b = não (x < 1) e verdadeiro; x = -x;")
        logico = arvore.comandos[0].expressao
        self.assertEqual(logico.tipo_inferido, "booleano")
        self.assertIsInstance(logico.esquerda, UnaryOpNode)
        self.assertEqual(logico.esquerda.tipo_inferido, "booleano")
        self.assertEqual(arvore.comandos[1].expressao.tipo_inferido, "inteiro")

    def test_condicao_do_se_e_anotada(self):
        arvore, _ = analisar("var x: inteiro; se (x > 0) { x = 1; }")
        comando = arvore.comandos[0]
        self.assertIsInstance(comando, IfStmtNode)
        self.assertEqual(comando.condicao.tipo_inferido, "booleano")

    def test_argumentos_de_chamada_sao_anotados(self):
        arvore, _ = analisar("procedimento p(a: inteiro, b: booleano) { } p(1 + 1, verdadeiro);")
        argumentos = arvore.comandos[0].argumentos
        self.assertEqual([a.tipo_inferido for a in argumentos], ["inteiro", "booleano"])

    def test_expressao_com_erro_fica_sem_tipo(self):
        arvore, semantico = analisar("var x: inteiro; x = y;")
        self.assertTrue(semantico.tem_erros)
        self.assertIsNone(arvore.comandos[0].expressao.tipo_inferido)

    def test_anotacao_nao_afeta_igualdade_nem_construtor(self):
        a = LiteralNode(1, 1, 5, "inteiro")
        b = LiteralNode(1, 1, 5, "inteiro")
        a.tipo_inferido = "inteiro"
        self.assertEqual(a, b)
        self.assertIsNone(b.tipo_inferido)
        self.assertIsInstance(AssignStmtNode(1, 1, "x", a), AssignStmtNode)

    def test_formatar_ast_mostra_tipos_inferidos(self):
        arvore, _ = analisar("var x: inteiro; x = 1 + 2;")
        texto = formatar_ast(arvore)
        self.assertIn("BinaryOp: (+) [linha 2, col 23] : inteiro", texto)
        self.assertIn("Literal: 1 (inteiro) [linha 2, col 21] : inteiro", texto)

    def test_formatar_ast_sem_analise_semantica_nao_mostra_tipos(self):
        lexer = Lexer("programa t { var x: inteiro; x = 1; } fim.")
        arvore = Parser(lexer.tokenizar()).parse()
        self.assertNotIn(" : inteiro", formatar_ast(arvore))


if __name__ == "__main__":
    unittest.main()
