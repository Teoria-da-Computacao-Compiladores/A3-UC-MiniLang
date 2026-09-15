import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from minilang.lexer import Lexer, TokenType

class TestLexer(unittest.TestCase):
    
    def test_descarte_espacos_e_comentarios(self):
        codigo = "   \n\n  # Comentario ignorado\n 123"
        lexer = Lexer(codigo)
        token = lexer.proximo_token()
        
        self.assertEqual(token.tipo, TokenType.NUMERO)
        self.assertEqual(token.linha, 4)
        self.assertEqual(token.coluna, 2)
        
    def test_palavras_reservadas_e_identificadores(self):
        codigo = "programa meu_prog var inteiro"
        lexer = Lexer(codigo)
        
        t1 = lexer.proximo_token()
        self.assertEqual(t1.tipo, TokenType.PROGRAMA)
        
        t2 = lexer.proximo_token()
        self.assertEqual(t2.tipo, TokenType.IDENTIFICADOR)
        self.assertEqual(t2.lexema, "meu_prog")
        
        t3 = lexer.proximo_token()
        self.assertEqual(t3.tipo, TokenType.VAR)
        
    def test_numeros(self):
        codigo = "456 0 9999"
        lexer = Lexer(codigo)
        
        self.assertEqual(lexer.proximo_token().lexema, "456")
        self.assertEqual(lexer.proximo_token().lexema, "0")
        self.assertEqual(lexer.proximo_token().lexema, "9999")
        
    def test_operadores_lookahead(self):
        codigo = "= == < <= > >= ! !="
        lexer = Lexer(codigo)
        
        self.assertEqual(lexer.proximo_token().tipo, TokenType.ATRIBUICAO)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.IGUAL)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.MENOR)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.MENOR_IGUAL)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.MAIOR)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.MAIOR_IGUAL)
        self.assertEqual(lexer.proximo_token().tipo, TokenType.ERRO) 
        self.assertEqual(lexer.proximo_token().tipo, TokenType.DIFERENTE)

    def test_erro_lexico_e_posicionamento(self):
        codigo = "var x = 10;\n @ \n"
        lexer = Lexer(codigo)
        
        for _ in range(5):
            lexer.proximo_token()
            
        token_erro = lexer.proximo_token()
        self.assertEqual(token_erro.tipo, TokenType.ERRO)
        self.assertEqual(token_erro.lexema, "@")
        self.assertEqual(token_erro.linha, 2)
        self.assertEqual(token_erro.coluna, 2)

if __name__ == '__main__':
    unittest.main()