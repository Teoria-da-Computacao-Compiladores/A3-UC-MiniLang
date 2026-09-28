import unittest

from minilang.ast import (
    AssignStmtNode,
    BinaryOpNode,
    CallStmtNode,
    IfStmtNode,
    LiteralNode,
    ProcedureDeclNode,
    ProgramNode,
    UnaryOpNode,
    VarAccessNode,
    VarDeclNode,
    WhileStmtNode,
    formatar_ast,
)
from minilang.parser import Parser


class TestParser(unittest.TestCase):

    def test_programa_valido_minimo(self):
        codigo = "programa p { } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertIsInstance(ast, ProgramNode)
        self.assertEqual(ast.nome, "p")
        self.assertEqual(ast.declaracoes, [])
        self.assertEqual(ast.comandos, [])

    def test_declaracoes_variaveis(self):
        codigo = "programa p { var x: inteiro; var ok: booleano; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertEqual(len(ast.declaracoes), 2)
        self.assertIsInstance(ast.declaracoes[0], VarDeclNode)
        self.assertEqual(ast.declaracoes[0].nome, "x")
        self.assertEqual(ast.declaracoes[0].tipo, "inteiro")
        self.assertEqual(ast.declaracoes[1].nome, "ok")
        self.assertEqual(ast.declaracoes[1].tipo, "booleano")

    def test_procedimento_com_parametros_e_chamada(self):
        codigo = """
        programa p {
            procedimento exibir(val: inteiro, flag: booleano) {
                var dobro: inteiro;
                dobro = val * 2;
                escreva(dobro);
            }
            exibir(5, verdadeiro);
        } fim.
        """
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertEqual(len(ast.declaracoes), 1)
        proc = ast.declaracoes[0]
        self.assertIsInstance(proc, ProcedureDeclNode)
        self.assertEqual(proc.nome, "exibir")
        self.assertEqual(len(proc.parametros), 2)
        self.assertEqual(proc.parametros[0].nome, "val")
        self.assertEqual(proc.parametros[0].tipo, "inteiro")
        self.assertEqual(proc.parametros[1].nome, "flag")
        self.assertEqual(proc.parametros[1].tipo, "booleano")
        self.assertEqual(len(proc.declaracoes), 1)
        self.assertEqual(proc.declaracoes[0].nome, "dobro")
        self.assertEqual(len(proc.comandos), 2)

        self.assertEqual(len(ast.comandos), 1)
        chamada = ast.comandos[0]
        self.assertIsInstance(chamada, CallStmtNode)
        self.assertEqual(chamada.identificador, "exibir")
        self.assertEqual(len(chamada.argumentos), 2)

    def test_comandos_basicos(self):
        codigo = """
        programa p {
            var x: inteiro;
            leia(x);
            x = x + 10;
            escreva(x);
        } fim.
        """
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertEqual(len(ast.comandos), 3)

    def test_repeticao_enquanto(self):
        codigo = """
        programa p {
            var i: inteiro;
            enquanto (i < 10) {
                i = i + 1;
            }
        } fim.
        """
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertEqual(len(ast.comandos), 1)
        loop = ast.comandos[0]
        self.assertIsInstance(loop, WhileStmtNode)
        self.assertIsInstance(loop.condicao, BinaryOpNode)
        self.assertEqual(loop.condicao.operador, "<")
        self.assertEqual(len(loop.comandos), 1)

    def test_condicional_com_e_sem_senao(self):
        codigo = """
        programa p {
            var x: inteiro;
            se (x > 0) {
                escreva(1);
            }
            se (x == 0) {
                escreva(0);
            } senão {
                escreva(-1);
            }
        } fim.
        """
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        self.assertEqual(len(ast.comandos), 2)
        se1 = ast.comandos[0]
        self.assertIsInstance(se1, IfStmtNode)
        self.assertIsNone(se1.senao_comandos)

        se2 = ast.comandos[1]
        self.assertIsInstance(se2, IfStmtNode)
        self.assertIsNotNone(se2.senao_comandos)
        self.assertEqual(len(se2.senao_comandos), 1)

    def test_dangling_else(self):
        codigo = """
        programa p {
            se (cond1) {
                se (cond2) {
                    escreva(1);
                } senão {
                    escreva(2);
                }
            }
        } fim.
        """
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        se_externo = ast.comandos[0]
        self.assertIsNone(se_externo.senao_comandos)

        se_interno = se_externo.entao_comandos[0]
        self.assertIsNotNone(se_interno.senao_comandos)
        self.assertEqual(len(se_interno.senao_comandos), 1)

    def test_precedencia_multiplicacao_sobre_soma(self):
        codigo = "programa p { var x: inteiro; x = 2 + 3 * 4; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        atrib = ast.comandos[0]
        exp = atrib.expressao
        self.assertIsInstance(exp, BinaryOpNode)
        self.assertEqual(exp.operador, "+")
        self.assertIsInstance(exp.esquerda, LiteralNode)
        self.assertEqual(exp.esquerda.valor, 2)
        self.assertIsInstance(exp.direita, BinaryOpNode)
        self.assertEqual(exp.direita.operador, "*")

    def test_precedencia_e_sobre_ou(self):
        codigo = "programa p { var b: booleano; b = verdadeiro ou falso e verdadeiro; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        atrib = ast.comandos[0]
        exp = atrib.expressao
        self.assertIsInstance(exp, BinaryOpNode)
        self.assertEqual(exp.operador, "ou")
        self.assertIsInstance(exp.direita, BinaryOpNode)
        self.assertEqual(exp.direita.operador, "e")

    def test_associatividade_a_esquerda(self):
        codigo = "programa p { var x: inteiro; x = 10 - 5 - 2; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        atrib = ast.comandos[0]
        exp = atrib.expressao
        self.assertIsInstance(exp, BinaryOpNode)
        self.assertEqual(exp.operador, "-")
        self.assertIsInstance(exp.esquerda, BinaryOpNode)
        self.assertEqual(exp.esquerda.operador, "-")
        self.assertIsInstance(exp.direita, LiteralNode)
        self.assertEqual(exp.direita.valor, 2)

    def test_operador_unario(self):
        codigo = "programa p { var b: booleano; b = não verdadeiro; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        self.assertFalse(parser.tem_erros)
        atrib = ast.comandos[0]
        exp = atrib.expressao
        self.assertIsInstance(exp, UnaryOpNode)
        self.assertEqual(exp.operador, "não")
        self.assertIsInstance(exp.operando, LiteralNode)
        self.assertEqual(exp.operando.valor, True)

    def test_erro_sintatico_falta_ponto_e_virgula(self):
        codigo = "programa p { var x: inteiro x = 1; } fim."
        parser = Parser.from_code(codigo)
        parser.parse()

        self.assertTrue(parser.tem_erros)
        self.assertIn("Esperado ';'", parser.erros[0].mensagem)
        self.assertEqual(parser.erros[0].linha, 1)

    def test_erro_sintatico_falta_abre_chave(self):
        codigo = "programa p var x: inteiro; } fim."
        parser = Parser.from_code(codigo)
        parser.parse()

        self.assertTrue(parser.tem_erros)
        self.assertIn("Esperado '{'", parser.erros[0].mensagem)

    def test_recuperacao_modo_panico_multiplos_erros(self):
        codigo = """
        programa p {
            var a: inteiro
            var b: inteiro;
            a = ;
            b = 10;
            escreva();
            b = 20;
        } fim.
        """
        parser = Parser.from_code(codigo)
        parser.parse()

        self.assertTrue(parser.tem_erros)
        self.assertGreaterEqual(len(parser.erros), 2)

    def test_formatar_ast(self):
        codigo = "programa teste { var x: inteiro; x = 10; } fim."
        parser = Parser.from_code(codigo)
        ast = parser.parse()

        formatado = formatar_ast(ast)
        self.assertIn("Programa 'teste'", formatado)
        self.assertIn("VarDecl: x: inteiro", formatado)
        self.assertIn("Atribuicao: x =", formatado)
        self.assertIn("Literal: 10 (inteiro)", formatado)


if __name__ == "__main__":
    unittest.main()
