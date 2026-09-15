import sys
from enum import Enum, auto
from dataclasses import dataclass

class TokenType(Enum):
    PROGRAMA = auto(); VAR = auto(); INTEIRO = auto(); BOOLEANO = auto()
    SE = auto(); SENAO = auto(); ENQUANTO = auto(); ESCREVA = auto()
    LEIA = auto(); VERDADEIRO = auto(); FALSO = auto(); E = auto()
    OU = auto(); NAO = auto(); FIM = auto()
    IDENTIFICADOR = auto(); NUMERO = auto()
    SOMA = auto(); SUBTRACAO = auto(); MULTIPLICACAO = auto()
    DIVISAO = auto(); MODULO = auto()
    IGUAL = auto(); DIFERENTE = auto(); MENOR = auto()
    MENOR_IGUAL = auto(); MAIOR = auto(); MAIOR_IGUAL = auto()
    ATRIBUICAO = auto()
    ABRE_PAREN = auto(); FECHA_PAREN = auto(); ABRE_CHAVE = auto()
    FECHA_CHAVE = auto(); PONTO_VIRGULA = auto(); DOIS_PONTOS = auto()
    VIRGULA = auto(); PONTO = auto()
    EOF = auto(); ERRO = auto()

@dataclass
class Token:
    tipo: TokenType
    lexema: str
    linha: int
    coluna: int

    def __str__(self):
        return f"Token({self.tipo.name:<15} | Lexema: '{self.lexema:<10}' | Linha: {self.linha:02d}, Col: {self.coluna:02d})"

class Lexer:
    def __init__(self, codigo_fonte: str):
        self.codigo = codigo_fonte
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.palavras_reservadas = {
            'programa': TokenType.PROGRAMA, 'var': TokenType.VAR,
            'inteiro': TokenType.INTEIRO, 'booleano': TokenType.BOOLEANO,
            'se': TokenType.SE, 'senão': TokenType.SENAO,
            'enquanto': TokenType.ENQUANTO, 'escreva': TokenType.ESCREVA,
            'leia': TokenType.LEIA, 'verdadeiro': TokenType.VERDADEIRO,
            'falso': TokenType.FALSO, 'e': TokenType.E, 'ou': TokenType.OU,
            'não': TokenType.NAO, 'fim': TokenType.FIM
        }

    def avancar(self):
        if self.posicao < len(self.codigo):
            caractere = self.codigo[self.posicao]
            if caractere == '\n':
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.posicao += 1
            return caractere
        return None

    def espiar(self):
        if self.posicao < len(self.codigo):
            return self.codigo[self.posicao]
        return None

    def proximo_token(self) -> Token:
        caractere = self.espiar()

        while caractere is not None and caractere.isspace():
            self.avancar()
            caractere = self.espiar()

        if caractere == '#':
            while caractere is not None and caractere != '\n':
                self.avancar()
                caractere = self.espiar()
            return self.proximo_token()

        if caractere is None:
            return Token(TokenType.EOF, "", self.linha, self.coluna)

        linha_token = self.linha
        coluna_token = self.coluna

        if caractere.isalpha():
            lexema = ""
            while caractere is not None and (caractere.isalnum() or caractere == '_'):
                lexema += self.avancar()
                caractere = self.espiar()
            tipo = self.palavras_reservadas.get(lexema, TokenType.IDENTIFICADOR)
            return Token(tipo, lexema, linha_token, coluna_token)

        if caractere.isdigit():
            lexema = ""
            while caractere is not None and caractere.isdigit():
                lexema += self.avancar()
                caractere = self.espiar()
            return Token(TokenType.NUMERO, lexema, linha_token, coluna_token)

        if caractere == '=':
            lexema = self.avancar()
            if self.espiar() == '=':
                lexema += self.avancar()
                return Token(TokenType.IGUAL, lexema, linha_token, coluna_token)
            return Token(TokenType.ATRIBUICAO, lexema, linha_token, coluna_token)

        if caractere == '<':
            lexema = self.avancar()
            if self.espiar() == '=':
                lexema += self.avancar()
                return Token(TokenType.MENOR_IGUAL, lexema, linha_token, coluna_token)
            return Token(TokenType.MENOR, lexema, linha_token, coluna_token)

        if caractere == '>':
            lexema = self.avancar()
            if self.espiar() == '=':
                lexema += self.avancar()
                return Token(TokenType.MAIOR_IGUAL, lexema, linha_token, coluna_token)
            return Token(TokenType.MAIOR, lexema, linha_token, coluna_token)
            
        if caractere == '!':
            lexema = self.avancar()
            if self.espiar() == '=':
                lexema += self.avancar()
                return Token(TokenType.DIFERENTE, lexema, linha_token, coluna_token)
            return Token(TokenType.ERRO, lexema, linha_token, coluna_token)

        simples = {
            '+': TokenType.SOMA, '-': TokenType.SUBTRACAO, '*': TokenType.MULTIPLICACAO,
            '/': TokenType.DIVISAO, '%': TokenType.MODULO,
            '(': TokenType.ABRE_PAREN, ')': TokenType.FECHA_PAREN,
            '{': TokenType.ABRE_CHAVE, '}': TokenType.FECHA_CHAVE,
            ';': TokenType.PONTO_VIRGULA, ':': TokenType.DOIS_PONTOS,
            ',': TokenType.VIRGULA, '.': TokenType.PONTO
        }

        if caractere in simples:
            lexema = self.avancar()
            return Token(simples[caractere], lexema, linha_token, coluna_token)

        lexema_erro = self.avancar()
        return Token(TokenType.ERRO, lexema_erro, linha_token, coluna_token)

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8')
    codigo_teste = """
    programa exemplo {
      var x: inteiro;
      var ok: booleano;
      x = 10 + 2 * 3;
      ok = verdadeiro e não falso;
      se (x >= 10) {
        escreva(x);
      } senão {
        leia(x);
      }
    } fim.
    """
    analisador = Lexer(codigo_teste)
    while True:
        token = analisador.proximo_token()
        print(token)
        if token.tipo == TokenType.EOF:
            break