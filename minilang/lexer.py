"""
Analisador léxico da MiniLang (M1).

Lê o código-fonte caractere a caractere e o transforma em uma lista de tokens
(tipo, lexema, linha, coluna). A implementação segue o AFD documentado em
docs/entrega_m1.md: cada método _ler_* corresponde a um caminho do autômato a
partir do estado inicial q0.

Erros léxicos não interrompem a análise: o lexer gera um token ERRO, registra
uma mensagem em self.erros e continua lendo o restante do arquivo.
"""

from dataclasses import dataclass
from enum import Enum, auto


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


@dataclass
class ErroLexico:
    mensagem: str
    linha: int
    coluna: int

    def __str__(self):
        return f"Erro léxico [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


# -----------------------------------------------------------------------------
# Alfabeto da linguagem
# -----------------------------------------------------------------------------

# Letras acentuadas do português. São necessárias para as palavras reservadas
# "senão" e "não" e, por decisão da equipe, também valem em identificadores.
LETRAS_ACENTUADAS = "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇ"

# Só estes caracteres contam como espaço. Outros (ex.: espaço não separável
# copiado da web) geram erro léxico em vez de passarem despercebidos.
ESPACOS = " \t\r\n"


def eh_letra(c):
    return c is not None and (("a" <= c <= "z") or ("A" <= c <= "Z") or c in LETRAS_ACENTUADAS)


def eh_digito(c):
    # Não usa str.isdigit(), que aceitaria dígitos Unicode como "²" ou "٣".
    return c is not None and "0" <= c <= "9"


def eh_caractere_de_identificador(c):
    return eh_letra(c) or eh_digito(c) or c == "_"


# -----------------------------------------------------------------------------
# Tabelas de tokens
# -----------------------------------------------------------------------------

PALAVRAS_RESERVADAS = {
    "programa": TokenType.PROGRAMA, "var": TokenType.VAR,
    "inteiro": TokenType.INTEIRO, "booleano": TokenType.BOOLEANO,
    "se": TokenType.SE, "senão": TokenType.SENAO,
    "enquanto": TokenType.ENQUANTO, "escreva": TokenType.ESCREVA,
    "leia": TokenType.LEIA, "verdadeiro": TokenType.VERDADEIRO,
    "falso": TokenType.FALSO, "e": TokenType.E, "ou": TokenType.OU,
    "não": TokenType.NAO, "fim": TokenType.FIM,
    # Sinônimos sem acento: quem digita sem acento não recebe um identificador
    # "senao" por engano (o que só daria erro mais tarde, no parser).
    "senao": TokenType.SENAO, "nao": TokenType.NAO,
}

# Operadores e delimitadores de um único caractere.
SIMBOLOS_SIMPLES = {
    "+": TokenType.SOMA, "-": TokenType.SUBTRACAO, "*": TokenType.MULTIPLICACAO,
    "/": TokenType.DIVISAO, "%": TokenType.MODULO,
    "(": TokenType.ABRE_PAREN, ")": TokenType.FECHA_PAREN,
    "{": TokenType.ABRE_CHAVE, "}": TokenType.FECHA_CHAVE,
    ";": TokenType.PONTO_VIRGULA, ":": TokenType.DOIS_PONTOS,
    ",": TokenType.VIRGULA, ".": TokenType.PONTO,
}

# Operadores que precisam de lookahead: primeiro caractere ->
# (token se vier sozinho, token se vier seguido de "=").
# None significa que o caractere sozinho não é um token válido.
OPERADORES_COM_LOOKAHEAD = {
    "=": (TokenType.ATRIBUICAO, TokenType.IGUAL),
    "<": (TokenType.MENOR, TokenType.MENOR_IGUAL),
    ">": (TokenType.MAIOR, TokenType.MAIOR_IGUAL),
    "!": (None, TokenType.DIFERENTE),
}


class Lexer:
    def __init__(self, codigo_fonte: str):
        self.codigo = codigo_fonte
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.palavras_reservadas = PALAVRAS_RESERVADAS
        self.erros: list[ErroLexico] = []

    @property
    def tem_erros(self) -> bool:
        return bool(self.erros)

    # -------------------------------------------------------------------------
    # Leitura de caracteres
    # -------------------------------------------------------------------------

    def avancar(self):
        """Consome o caractere atual, atualizando linha e coluna."""
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
        """Lookahead: devolve o caractere atual sem consumi-lo."""
        if self.posicao < len(self.codigo):
            return self.codigo[self.posicao]
        return None

    # -------------------------------------------------------------------------
    # API pública
    # -------------------------------------------------------------------------

    def proximo_token(self) -> Token:
        """Reconhece e devolve o próximo token (estado inicial q0 do AFD)."""
        self._pular_espacos_e_comentarios()

        caractere = self.espiar()
        if caractere is None:
            return Token(TokenType.EOF, "", self.linha, self.coluna)

        # Posição onde o token começa (usada no token e nas mensagens de erro)
        linha, coluna = self.linha, self.coluna

        if eh_letra(caractere):
            return self._ler_identificador_ou_palavra_reservada(linha, coluna)

        if eh_digito(caractere):
            return self._ler_numero(linha, coluna)

        if caractere == "_":
            return self._ler_identificador_invalido(linha, coluna)

        if caractere in OPERADORES_COM_LOOKAHEAD:
            return self._ler_operador_com_lookahead(linha, coluna)

        if caractere in SIMBOLOS_SIMPLES:
            self.avancar()
            return Token(SIMBOLOS_SIMPLES[caractere], caractere, linha, coluna)

        self.avancar()
        return self._erro(caractere, f"caractere inválido {caractere!r}", linha, coluna)

    def tokenizar(self) -> list[Token]:
        """Devolve todos os tokens do código, terminando sempre com EOF."""
        tokens = []
        while True:
            token = self.proximo_token()
            tokens.append(token)
            if token.tipo == TokenType.EOF:
                return tokens

    # -------------------------------------------------------------------------
    # Caminhos do AFD
    # -------------------------------------------------------------------------

    def _pular_espacos_e_comentarios(self):
        """
        Descarta espaços e comentários (# até o fim da linha).

        É um laço, não recursão: a versão recursiva estourava o limite de
        recursão do Python com ~1000 linhas de comentário seguidas.
        """
        while True:
            caractere = self.espiar()
            if caractere is not None and caractere in ESPACOS:
                self.avancar()
            elif caractere == "#":
                while self.espiar() not in (None, "\n"):
                    self.avancar()
            else:
                return

    def _ler_palavra(self) -> str:
        """Consome letras, dígitos e '_' a partir da posição atual."""
        lexema = ""
        while eh_caractere_de_identificador(self.espiar()):
            lexema += self.avancar()
        return lexema

    def _ler_identificador_ou_palavra_reservada(self, linha, coluna) -> Token:
        lexema = self._ler_palavra()
        tipo = PALAVRAS_RESERVADAS.get(lexema, TokenType.IDENTIFICADOR)
        return Token(tipo, lexema, linha, coluna)

    def _ler_numero(self, linha, coluna) -> Token:
        lexema = ""
        while eh_digito(self.espiar()):
            lexema += self.avancar()

        # "12abc" ou "3_x": dígitos colados em letras formam um único erro,
        # em vez de virarem NUMERO + IDENTIFICADOR silenciosamente.
        if eh_letra(self.espiar()) or self.espiar() == "_":
            lexema += self._ler_palavra()
            return self._erro(
                lexema,
                f"número mal formado '{lexema}': identificadores devem começar com letra",
                linha, coluna,
            )

        return Token(TokenType.NUMERO, lexema, linha, coluna)

    def _ler_identificador_invalido(self, linha, coluna) -> Token:
        lexema = self._ler_palavra()
        return self._erro(
            lexema,
            f"identificador inválido '{lexema}': identificadores devem começar com letra",
            linha, coluna,
        )

    def _ler_operador_com_lookahead(self, linha, coluna) -> Token:
        primeiro = self.avancar()
        tipo_simples, tipo_com_igual = OPERADORES_COM_LOOKAHEAD[primeiro]

        if self.espiar() == "=":
            self.avancar()
            return Token(tipo_com_igual, primeiro + "=", linha, coluna)

        if tipo_simples is None:  # "!" sozinho
            return self._erro(
                primeiro,
                "'!' isolado não é um operador válido; use '!=' para diferente ou 'não' para negação",
                linha, coluna,
            )

        return Token(tipo_simples, primeiro, linha, coluna)

    def _erro(self, lexema, mensagem, linha, coluna) -> Token:
        """Registra um erro léxico e devolve um token ERRO (a análise continua)."""
        self.erros.append(ErroLexico(mensagem, linha, coluna))
        return Token(TokenType.ERRO, lexema, linha, coluna)


if __name__ == "__main__":
    # Mantém compatível o comando antigo "python minilang/lexer.py arquivo.min".
    # O comando oficial é "python -m minilang arquivo.min".
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from minilang.__main__ import main

    sys.exit(main())
