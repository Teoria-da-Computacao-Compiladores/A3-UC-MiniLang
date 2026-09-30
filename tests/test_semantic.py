import unittest

from minilang.ast import (
    AssignStmtNode,
    BinaryOpNode,
    CallStmtNode,
    IfStmtNode,
    LiteralNode,
    ParamNode,
    ProcedureDeclNode,
    ProgramNode,
    ReadStmtNode,
    UnaryOpNode,
    VarAccessNode,
    VarDeclNode,
    WhileStmtNode,
    WriteStmtNode,
)
from minilang.semantic import AnalisadorSemantico, formatar_tabela_simbolos


# --- construtores de AST (posição fixa: só o conteúdo importa) --------------

def num(v):
    return LiteralNode(1, 1, v, "inteiro")


def boo(v):
    return LiteralNode(1, 1, v, "booleano")


def var(n):
    return VarAccessNode(1, 1, n)


def op(esq, o, dir_):
    return BinaryOpNode(1, 1, esq, o, dir_)


def decl(n, t):
    return VarDeclNode(1, 1, n, t)


def atrib(n, e):
    return AssignStmtNode(1, 1, n, e)


def prog(decls=(), cmds=()):
    return ProgramNode(1, 1, "p", list(decls), list(cmds))


def proc(nome, params=(), locais=(), cmds=()):
    ps = [ParamNode(1, 1, n, t) for n, t in params]
    return ProcedureDeclNode(1, 1, nome, ps, list(locais), list(cmds))


def analisar(programa):
    a = AnalisadorSemantico()
    a.analisar(programa)
    return a


def mensagens(a):
    return [e.mensagem for e in a.erros]


class TestDeclaracoes(unittest.TestCase):
    def test_programa_valido_sem_erros(self):
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", num(1))]))
        self.assertFalse(a.tem_erros)

    def test_variavel_nao_declarada_na_atribuicao(self):
        a = analisar(prog([], [atrib("x", num(1))]))
        self.assertEqual(mensagens(a), ["variável 'x' não declarada"])

    def test_variavel_nao_declarada_em_expressao(self):
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", var("y"))]))
        self.assertEqual(mensagens(a), ["variável 'y' não declarada"])

    def test_declaracao_duplicada(self):
        a = analisar(prog([decl("x", "inteiro"), decl("x", "booleano")]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("já declarado", a.erros[0].mensagem)

    def test_leitura_de_variavel_nao_declarada(self):
        a = analisar(prog([], [ReadStmtNode(1, 1, "z")]))
        self.assertEqual(mensagens(a), ["variável 'z' não declarada"])


class TestTipos(unittest.TestCase):
    def test_atribuicao_incompativel(self):
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", boo(True))]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("tipos incompatíveis na atribuição", a.erros[0].mensagem)

    def test_atribuicao_relacional_a_booleano(self):
        a = analisar(prog([decl("b", "booleano")], [atrib("b", op(num(1), "<", num(2)))]))
        self.assertFalse(a.tem_erros)

    def test_aritmetica_com_booleano(self):
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", op(num(1), "+", boo(True)))]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("operando direito é booleano", a.erros[0].mensagem)

    def test_logico_com_inteiro(self):
        a = analisar(prog([decl("b", "booleano")], [atrib("b", op(boo(True), "e", num(1)))]))
        self.assertEqual(len(a.erros), 1)

    def test_igualdade_tipos_diferentes(self):
        a = analisar(prog([decl("b", "booleano")], [atrib("b", op(num(1), "==", boo(True)))]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("mesmo tipo", a.erros[0].mensagem)

    def test_igualdade_booleanos_ok(self):
        a = analisar(prog([decl("b", "booleano")], [atrib("b", op(boo(True), "!=", boo(False)))]))
        self.assertFalse(a.tem_erros)

    def test_unario_nao_com_inteiro(self):
        e = UnaryOpNode(1, 1, "não", num(1))
        a = analisar(prog([decl("b", "booleano")], [atrib("b", e)]))
        self.assertEqual(len(a.erros), 1)

    def test_unario_menos_com_booleano(self):
        e = UnaryOpNode(1, 1, "-", boo(True))
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", e)]))
        self.assertEqual(len(a.erros), 1)

    def test_divisao_por_zero_literal(self):
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", op(num(4), "/", num(0)))]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("divisão por zero", a.erros[0].mensagem)

    def test_sem_erros_em_cascata(self):
        # 'y' não existe: só 1 erro, mesmo usada dentro de expressão maior.
        e = op(op(var("y"), "+", num(1)), "*", num(2))
        a = analisar(prog([decl("x", "inteiro")], [atrib("x", e)]))
        self.assertEqual(len(a.erros), 1)


class TestCondicoes(unittest.TestCase):
    def test_se_com_condicao_inteira(self):
        cmd = IfStmtNode(1, 1, num(1), [], None)
        a = analisar(prog([], [cmd]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("'se'", a.erros[0].mensagem)

    def test_enquanto_com_condicao_inteira(self):
        cmd = WhileStmtNode(1, 1, var("x"), [])
        a = analisar(prog([decl("x", "inteiro")], [cmd]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("'enquanto'", a.erros[0].mensagem)

    def test_se_senao_validos(self):
        cmd = IfStmtNode(1, 1, op(num(1), "<", num(2)),
                         [WriteStmtNode(1, 1, num(1))], [WriteStmtNode(1, 1, num(2))])
        self.assertFalse(analisar(prog([], [cmd])).tem_erros)

    def test_erros_dentro_dos_blocos_sao_reportados(self):
        cmd = IfStmtNode(1, 1, boo(True), [atrib("nada", num(1))], [atrib("tambem", num(1))])
        self.assertEqual(len(analisar(prog([], [cmd])).erros), 2)


class TestProcedimentos(unittest.TestCase):
    def setUp(self):
        self.soma = proc("soma", [("a", "inteiro"), ("b", "inteiro")],
                         [decl("t", "inteiro")],
                         [atrib("t", op(var("a"), "+", var("b"))), WriteStmtNode(1, 1, var("t"))])

    def test_chamada_valida(self):
        c = CallStmtNode(1, 1, "soma", [num(1), num(2)])
        self.assertFalse(analisar(prog([self.soma], [c])).tem_erros)

    def test_procedimento_nao_declarado(self):
        c = CallStmtNode(1, 1, "xyz", [])
        a = analisar(prog([], [c]))
        self.assertEqual(mensagens(a), ["procedimento 'xyz' não declarado"])

    def test_numero_de_argumentos_errado(self):
        c = CallStmtNode(1, 1, "soma", [num(1)])
        a = analisar(prog([self.soma], [c]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("espera 2 argumento(s), mas recebeu 1", a.erros[0].mensagem)

    def test_tipo_de_argumento_errado(self):
        c = CallStmtNode(1, 1, "soma", [num(1), boo(True)])
        a = analisar(prog([self.soma], [c]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("argumento 2", a.erros[0].mensagem)

    def test_variavel_chamada_como_procedimento(self):
        c = CallStmtNode(1, 1, "x", [])
        a = analisar(prog([decl("x", "inteiro")], [c]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("não pode ser chamado", a.erros[0].mensagem)

    def test_procedimento_usado_como_variavel(self):
        a = analisar(prog([self.soma, decl("x", "inteiro")], [atrib("x", var("soma"))]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("é um procedimento", a.erros[0].mensagem)

    def test_procedimento_duplicado(self):
        a = analisar(prog([self.soma, proc("soma")]))
        self.assertEqual(len(a.erros), 1)

    def test_parametro_duplicado_e_local_com_mesmo_nome(self):
        p = proc("f", [("a", "inteiro")], [decl("a", "inteiro")])
        a = analisar(prog([p]))
        self.assertEqual(len(a.erros), 1)
        self.assertIn("já declarado", a.erros[0].mensagem)

    def test_variavel_local_nao_vaza_para_o_escopo_global(self):
        a = analisar(prog([self.soma], [atrib("t", num(1))]))
        self.assertEqual(mensagens(a), ["variável 't' não declarada"])

    def test_procedimento_enxerga_global(self):
        p = proc("f", [], [], [atrib("g", num(1))])
        self.assertFalse(analisar(prog([decl("g", "inteiro"), p])).tem_erros)

    def test_local_sombreia_global_com_outro_tipo(self):
        p = proc("f", [], [decl("g", "booleano")], [atrib("g", boo(True))])
        self.assertFalse(analisar(prog([decl("g", "inteiro"), p])).tem_erros)

    def test_recursao_e_chamada_a_procedimento_declarado_depois(self):
        f = proc("f", [("n", "inteiro")], [], [CallStmtNode(1, 1, "g", [var("n")])])
        g = proc("g", [("m", "inteiro")], [], [CallStmtNode(1, 1, "f", [var("m")])])
        self.assertFalse(analisar(prog([f, g])).tem_erros)

    def test_parametro_tem_tipo_declarado(self):
        p = proc("f", [("flag", "booleano")], [], [atrib("flag", num(1))])
        a = analisar(prog([p]))
        self.assertEqual(len(a.erros), 1)


class TestTabelaDeSimbolos(unittest.TestCase):
    def test_tabela_lista_escopos_e_simbolos(self):
        p = proc("f", [("a", "inteiro")], [decl("t", "booleano")])
        a = analisar(prog([decl("x", "inteiro"), p]))
        texto = formatar_tabela_simbolos(a.tabela)
        self.assertIn("Escopo: global", texto)
        self.assertIn("Escopo: procedimento f", texto)
        self.assertIn("parâmetro", texto)
        self.assertIn("(a: inteiro)", texto)

    def test_formato_da_mensagem_de_erro(self):
        a = analisar(ProgramNode(1, 1, "p", [], [atrib("x", num(1))]))
        self.assertTrue(str(a.erros[0]).startswith("Erro semântico [linha "))


# --- Integração com léxico + parser reais (requer o repositório completo) ---

def _compilar(fonte):
    from minilang.lexer import Lexer
    from minilang.parser import Parser

    lexer = Lexer(fonte)
    tokens = lexer.tokenizar()
    assert not lexer.tem_erros, lexer.erros
    parser = Parser(tokens)
    arvore = parser.parse()
    assert not parser.tem_erros, parser.erros
    return analisar(arvore)


class TestIntegracao(unittest.TestCase):
    def test_exemplo_procedimento_da_opcao_a(self):
        fonte = """
        programa ok {
            var base: inteiro;
            procedimento dobrar(valor: inteiro, inc: inteiro) {
                var temp: inteiro;
                temp = valor * 2 + inc;
                escreva(temp);
            }
            base = 10;
            dobrar(base, 5);
        } fim.
        """
        self.assertFalse(_compilar(fonte).tem_erros)

    def test_varios_erros_em_um_unico_programa(self):
        fonte = """
        programa ruim {
            var x: inteiro;
            var b: booleano;
            procedimento soma(a: inteiro, c: inteiro) {
                escreva(a + c);
            }
            y = 10;
            b = x + 1;
            se (x) { escreva(x); }
            soma(1);
            soma(1, verdadeiro);
            nada(3);
        } fim.
        """
        self.assertEqual(len(_compilar(fonte).erros), 6)


if __name__ == "__main__":
    unittest.main()
