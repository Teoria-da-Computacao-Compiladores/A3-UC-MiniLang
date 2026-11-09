import os
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def rodar_cli(*args, entrada=None):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "minilang", *args],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", env=env, input=entrada,
    )


def saida_do_programa(resultado):
    linhas = resultado.stdout.splitlines()
    inicio = linhas.index("Execução:") + 1
    fim = next(i for i in range(inicio, len(linhas)) if linhas[i] == "")
    return linhas[inicio:fim]


class TestExecutarNaLinhaDeComando(unittest.TestCase):
    def test_fatorial(self):
        resultado = rodar_cli("examples/fatorial.min", "--executar", "--sem-tokens")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertEqual(saida_do_programa(resultado), ["1", "2", "6", "24", "120", "720"])
        self.assertIn("6 chamada(s) de procedimento", resultado.stdout)

    def test_recursao_mostra_profundidade_da_pilha(self):
        resultado = rodar_cli("examples/recursao.min", "--executar", "--sem-tokens")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertEqual(
            saida_do_programa(resultado),
            ["5", "4", "3", "2", "1", "0", "1", "1", "2", "3", "5", "8", "13", "21", "34"],
        )
        self.assertIn("profundidade máxima da pilha de ativação: 11", resultado.stdout)

    def test_parametro_por_valor_e_escopo(self):
        resultado = rodar_cli("examples/escopo_e_valor.min", "--executar", "--sem-tokens")

        self.assertEqual(saida_do_programa(resultado), ["101", "7", "1", "50"])

    def test_entrada_pela_entrada_padrao(self):
        resultado = rodar_cli("examples/entrada.min", "--executar", "--sem-tokens", entrada="7\n12\n")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertEqual(saida_do_programa(resultado), ["19", "12"])

    def test_entrada_invalida_sai_com_tres(self):
        resultado = rodar_cli("examples/entrada.min", "--executar", "--sem-tokens", entrada="abc\n")

        self.assertEqual(resultado.returncode, 3)
        self.assertIn("Erro de execução [linha 8, coluna 5]", resultado.stdout)
        self.assertIn("esperado inteiro", resultado.stdout)

    def test_erro_de_execucao_sai_com_tres_e_preserva_saida_anterior(self):
        resultado = rodar_cli("examples/erro_execucao.min", "--executar", "--sem-tokens")

        self.assertEqual(resultado.returncode, 3)
        self.assertIn("Erro de execução [linha 11, coluna 23]: divisão por zero", resultado.stdout)
        linhas = resultado.stdout.splitlines()
        inicio = linhas.index("Execução:") + 1
        self.assertEqual(linhas[inicio:inicio + 5], ["2", "2", "3", "5", "10"])

    def test_sem_executar_o_programa_nao_roda(self):
        resultado = rodar_cli("examples/fatorial.min", "--sem-tokens")

        self.assertEqual(resultado.returncode, 0)
        self.assertNotIn("Execução:", resultado.stdout)

    def test_programa_com_erro_semantico_nao_executa(self):
        resultado = rodar_cli("examples/erro_semantico.min", "--executar")

        self.assertEqual(resultado.returncode, 1)
        self.assertIn("erro(s) semântico(s)", resultado.stdout)
        self.assertNotIn("Execução:", resultado.stdout)

    def test_programa_com_erro_sintatico_nao_executa(self):
        resultado = rodar_cli("examples/erro_sintatico.min", "--executar")

        self.assertEqual(resultado.returncode, 1)
        self.assertNotIn("Execução:", resultado.stdout)

    def test_sem_tokens_oculta_a_tabela(self):
        com = rodar_cli("examples/fatorial.min")
        sem = rodar_cli("examples/fatorial.min", "--sem-tokens")

        self.assertIn("Tokens gerados:", com.stdout)
        self.assertNotIn("Tokens gerados:", sem.stdout)


class TestOtimizarNaLinhaDeComando(unittest.TestCase):
    def test_relatorio_lista_as_tres_otimizacoes(self):
        resultado = rodar_cli("examples/otimizacao.min", "--otimizar", "--sem-tokens")

        self.assertEqual(resultado.returncode, 0, resultado.stdout + resultado.stderr)
        self.assertIn("Otimizações aplicadas:", resultado.stdout)
        self.assertIn("dobramento de constantes: '2 * 3' calculado em compilação: 6", resultado.stdout)
        self.assertIn("simplificação algébrica: 'x * 1' simplificado para 'x'", resultado.stdout)
        self.assertIn("eliminação de código morto", resultado.stdout)
        self.assertIn("Total: 15 otimização(ões)", resultado.stdout)

    def test_saida_do_programa_e_igual_com_e_sem_otimizacao(self):
        sem = rodar_cli("examples/otimizacao.min", "--executar", "--sem-tokens")
        com = rodar_cli("examples/otimizacao.min", "--otimizar", "--executar", "--sem-tokens")

        self.assertEqual(saida_do_programa(sem), ["10", "10", "10", "verdadeiro"])
        self.assertEqual(saida_do_programa(com), saida_do_programa(sem))

    def test_otimizacao_reduz_os_passos_executados(self):
        sem = rodar_cli("examples/otimizacao.min", "--executar", "--sem-tokens")
        com = rodar_cli("examples/otimizacao.min", "--otimizar", "--executar", "--sem-tokens")

        def passos(resultado):
            trecho = resultado.stdout.split("Execução concluída: ")[1]
            return int(trecho.split(" passo(s)")[0])

        self.assertLess(passos(com), passos(sem))

    def test_ast_otimizada_e_impressa_com_ast(self):
        resultado = rodar_cli("examples/otimizacao.min", "--otimizar", "--ast", "--sem-tokens")

        self.assertIn("Árvore Sintática Abstrata (AST):", resultado.stdout)
        self.assertIn("Árvore Sintática Abstrata otimizada:", resultado.stdout)

    def test_programa_sem_oportunidades(self):
        resultado = rodar_cli("examples/fatorial.min", "--otimizar", "--sem-tokens")

        self.assertIn("Nenhuma otimização aplicável neste programa.", resultado.stdout)


class TestAstAnotadaNaLinhaDeComando(unittest.TestCase):
    def test_ast_mostra_tipos_inferidos(self):
        resultado = rodar_cli("examples/procedimento.min", "--ast", "--sem-tokens")

        self.assertEqual(resultado.returncode, 0)
        self.assertIn("BinaryOp: (+) [linha 9, col 26] : inteiro", resultado.stdout)
        self.assertIn("Var: valor [linha 9, col 16] : inteiro", resultado.stdout)


if __name__ == "__main__":
    unittest.main()
