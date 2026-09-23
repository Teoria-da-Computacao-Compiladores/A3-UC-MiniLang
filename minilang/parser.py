import os
import sys

_minilang_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_minilang_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
while _minilang_dir in sys.path:
    sys.path.remove(_minilang_dir)

from dataclasses import dataclass
from typing import List, Optional

from minilang.ast import (
    ASTNode,
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
from minilang.lexer import Lexer, Token, TokenType


class _ParseError(Exception):
    pass


@dataclass
class ErroSintatico:
    mensagem: str
    linha: int
    coluna: int

    def __str__(self):
        return f"Erro sintático [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"


class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.posicao = 0
        self.erros: List[ErroSintatico] = []

    @classmethod
    def from_code(cls, codigo: str):
        lexer = Lexer(codigo)
        tokens = lexer.tokenizar()
        return cls(tokens)

    @property
    def tem_erros(self) -> bool:
        return bool(self.erros)

    def _atual(self) -> Token:
        if self.posicao < len(self.tokens):
            return self.tokens[self.posicao]
        return self.tokens[-1]

    def _anterior(self) -> Token:
        if self.posicao > 0:
            return self.tokens[self.posicao - 1]
        return self.tokens[0]

    def _fim(self) -> bool:
        return self._atual().tipo == TokenType.EOF

    def _espiar(self) -> Token:
        if self.posicao + 1 < len(self.tokens):
            return self.tokens[self.posicao + 1]
        return self.tokens[-1]

    def _verificar(self, tipo: TokenType) -> bool:
        if self._fim():
            return tipo == TokenType.EOF
        return self._atual().tipo == tipo

    def _avancar(self) -> Token:
        if not self._fim():
            self.posicao += 1
        return self._anterior()

    def _consumir(self, tipo: TokenType, mensagem_esperado: str) -> Token:
        if self._verificar(tipo):
            return self._avancar()
        token = self._atual()
        self._registrar_erro(f"{mensagem_esperado}, mas foi encontrado '{token.lexema}'", token)
        raise _ParseError()

    def _registrar_erro(self, mensagem: str, token: Optional[Token] = None):
        tok = token or self._atual()
        self.erros.append(ErroSintatico(mensagem, tok.linha, tok.coluna))

    def _sincronizar(self):
        while not self._fim():
            if self._atual().tipo == TokenType.PONTO_VIRGULA:
                self._avancar()
                return
            if self._atual().tipo in (
                TokenType.FECHA_CHAVE,
                TokenType.VAR,
                TokenType.PROCEDIMENTO,
                TokenType.SE,
                TokenType.SENAO,
                TokenType.ENQUANTO,
                TokenType.ESCREVA,
                TokenType.LEIA,
                TokenType.FIM,
            ):
                return
            self._avancar()

    def parse(self) -> Optional[ProgramNode]:
        try:
            return self._programa()
        except _ParseError:
            return None

    def _programa(self) -> ProgramNode:
        token_programa = self._consumir(TokenType.PROGRAMA, "Esperado 'programa' no início do arquivo")
        token_nome = self._consumir(TokenType.IDENTIFICADOR, "Esperado nome do programa após 'programa'")
        self._consumir(TokenType.ABRE_CHAVE, "Esperado '{' após o nome do programa")

        declaracoes = self._declaracoes()
        comandos = self._comandos()

        self._consumir(TokenType.FECHA_CHAVE, "Esperado '}' para fechar o corpo do programa")
        self._consumir(TokenType.FIM, "Esperado 'fim' após o fechamento do bloco do programa")
        self._consumir(TokenType.PONTO, "Esperado '.' após 'fim'")

        if not self._verificar(TokenType.EOF):
            tok = self._atual()
            self._registrar_erro(f"Tokens adicionais inesperados após 'fim.': '{tok.lexema}'", tok)

        return ProgramNode(
            nome=token_nome.lexema,
            declaracoes=declaracoes,
            comandos=comandos,
            linha=token_programa.linha,
            coluna=token_programa.coluna,
        )

    def _declaracoes(self) -> List[ASTNode]:
        decls: List[ASTNode] = []
        while not self._fim():
            if self._verificar(TokenType.VAR):
                try:
                    decls.append(self._declaracao_var())
                except _ParseError:
                    self._sincronizar()
            elif self._verificar(TokenType.PROCEDIMENTO):
                try:
                    decls.append(self._declaracao_procedimento())
                except _ParseError:
                    self._sincronizar()
            else:
                break
        return decls

    def _declaracao_var(self) -> VarDeclNode:
        token_var = self._consumir(TokenType.VAR, "Esperado 'var'")
        token_id = self._consumir(TokenType.IDENTIFICADOR, "Esperado identificador após 'var'")
        self._consumir(TokenType.DOIS_PONTOS, "Esperado ':' após identificador na declaração")

        if not (self._verificar(TokenType.INTEIRO) or self._verificar(TokenType.BOOLEANO)):
            tok = self._atual()
            self._registrar_erro(f"Esperado tipo 'inteiro' ou 'booleano', mas foi encontrado '{tok.lexema}'", tok)
            raise _ParseError()

        token_tipo = self._avancar()
        self._consumir(TokenType.PONTO_VIRGULA, "Esperado ';' após o tipo da variável")

        return VarDeclNode(
            nome=token_id.lexema,
            tipo=token_tipo.lexema,
            linha=token_var.linha,
            coluna=token_var.coluna,
        )

    def _declaracao_procedimento(self) -> ProcedureDeclNode:
        token_proc = self._consumir(TokenType.PROCEDIMENTO, "Esperado 'procedimento'")
        token_nome = self._consumir(TokenType.IDENTIFICADOR, "Esperado identificador do procedimento")
        self._consumir(TokenType.ABRE_PAREN, "Esperado '(' após nome do procedimento")

        parametros = []
        if not self._verificar(TokenType.FECHA_PAREN):
            parametros = self._parametros()

        self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após lista de parâmetros")
        self._consumir(TokenType.ABRE_CHAVE, "Esperado '{' para iniciar o corpo do procedimento")

        decls_locais: List[VarDeclNode] = []
        while self._verificar(TokenType.VAR):
            try:
                decls_locais.append(self._declaracao_var())
            except _ParseError:
                self._sincronizar()

        comandos_proc = self._comandos()
        self._consumir(TokenType.FECHA_CHAVE, "Esperado '}' para fechar o corpo do procedimento")

        return ProcedureDeclNode(
            nome=token_nome.lexema,
            parametros=parametros,
            declaracoes=decls_locais,
            comandos=comandos_proc,
            linha=token_proc.linha,
            coluna=token_proc.coluna,
        )

    def _parametros(self) -> List[ParamNode]:
        params = [self._parametro()]
        while self._verificar(TokenType.VIRGULA):
            self._avancar()
            params.append(self._parametro())
        return params

    def _parametro(self) -> ParamNode:
        token_id = self._consumir(TokenType.IDENTIFICADOR, "Esperado nome do parâmetro")
        self._consumir(TokenType.DOIS_PONTOS, "Esperado ':' após nome do parâmetro")

        if not (self._verificar(TokenType.INTEIRO) or self._verificar(TokenType.BOOLEANO)):
            tok = self._atual()
            self._registrar_erro(f"Esperado tipo 'inteiro' ou 'booleano', mas foi encontrado '{tok.lexema}'", tok)
            raise _ParseError()

        token_tipo = self._avancar()
        return ParamNode(
            nome=token_id.lexema,
            tipo=token_tipo.lexema,
            linha=token_id.linha,
            coluna=token_id.coluna,
        )

    def _comandos(self) -> List[ASTNode]:
        comandos: List[ASTNode] = []
        while not self._fim() and not self._verificar(TokenType.FECHA_CHAVE) and not self._verificar(TokenType.FIM):
            try:
                cmd = self._comando()
                if cmd is not None:
                    comandos.append(cmd)
            except _ParseError:
                self._sincronizar()
        return comandos

    def _comando(self) -> Optional[ASTNode]:
        if self._verificar(TokenType.IDENTIFICADOR):
            return self._atribuicao_ou_chamada()
        if self._verificar(TokenType.SE):
            return self._condicional()
        if self._verificar(TokenType.ENQUANTO):
            return self._repeticao()
        if self._verificar(TokenType.LEIA):
            return self._leitura()
        if self._verificar(TokenType.ESCREVA):
            return self._escrita()

        tok = self._atual()
        self._registrar_erro(f"Comando inesperado iniciando com '{tok.lexema}'", tok)
        raise _ParseError()

    def _atribuicao_ou_chamada(self) -> ASTNode:
        token_id = self._consumir(TokenType.IDENTIFICADOR, "Esperado identificador")
        if self._verificar(TokenType.ATRIBUICAO):
            self._avancar()
            exp = self._expressao()
            self._consumir(TokenType.PONTO_VIRGULA, "Esperado ';' após atribuição")
            return AssignStmtNode(
                identificador=token_id.lexema,
                expressao=exp,
                linha=token_id.linha,
                coluna=token_id.coluna,
            )
        elif self._verificar(TokenType.ABRE_PAREN):
            self._avancar()
            args = []
            if not self._verificar(TokenType.FECHA_PAREN):
                args.append(self._expressao())
                while self._verificar(TokenType.VIRGULA):
                    self._avancar()
                    args.append(self._expressao())
            self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após argumentos da chamada")
            self._consumir(TokenType.PONTO_VIRGULA, "Esperado ';' após chamada de procedimento")
            return CallStmtNode(
                identificador=token_id.lexema,
                argumentos=args,
                linha=token_id.linha,
                coluna=token_id.coluna,
            )

        tok = self._atual()
        self._registrar_erro(f"Esperado '=' ou '(' após identificador, mas foi encontrado '{tok.lexema}'", tok)
        raise _ParseError()

    def _condicional(self) -> IfStmtNode:
        token_se = self._consumir(TokenType.SE, "Esperado 'se'")
        self._consumir(TokenType.ABRE_PAREN, "Esperado '(' após 'se'")
        condicao = self._expressao()
        self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após condição do 'se'")
        self._consumir(TokenType.ABRE_CHAVE, "Esperado '{' para bloco do 'se'")
        entao_comandos = self._comandos()
        self._consumir(TokenType.FECHA_CHAVE, "Esperado '}' para fechar bloco do 'se'")

        senao_comandos = None
        if self._verificar(TokenType.SENAO):
            self._avancar()
            self._consumir(TokenType.ABRE_CHAVE, "Esperado '{' para bloco do 'senão'")
            senao_comandos = self._comandos()
            self._consumir(TokenType.FECHA_CHAVE, "Esperado '}' para fechar bloco do 'senão'")

        return IfStmtNode(
            condicao=condicao,
            entao_comandos=entao_comandos,
            senao_comandos=senao_comandos,
            linha=token_se.linha,
            coluna=token_se.coluna,
        )

    def _repeticao(self) -> WhileStmtNode:
        token_enquanto = self._consumir(TokenType.ENQUANTO, "Esperado 'enquanto'")
        self._consumir(TokenType.ABRE_PAREN, "Esperado '(' após 'enquanto'")
        condicao = self._expressao()
        self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após condição do 'enquanto'")
        self._consumir(TokenType.ABRE_CHAVE, "Esperado '{' para bloco do 'enquanto'")
        comandos = self._comandos()
        self._consumir(TokenType.FECHA_CHAVE, "Esperado '}' para fechar bloco do 'enquanto'")

        return WhileStmtNode(
            condicao=condicao,
            comandos=comandos,
            linha=token_enquanto.linha,
            coluna=token_enquanto.coluna,
        )

    def _leitura(self) -> ReadStmtNode:
        token_leia = self._consumir(TokenType.LEIA, "Esperado 'leia'")
        self._consumir(TokenType.ABRE_PAREN, "Esperado '(' após 'leia'")
        token_id = self._consumir(TokenType.IDENTIFICADOR, "Esperado identificador no comando 'leia'")
        self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após identificador no comando 'leia'")
        self._consumir(TokenType.PONTO_VIRGULA, "Esperado ';' após comando 'leia'")

        return ReadStmtNode(
            identificador=token_id.lexema,
            linha=token_leia.linha,
            coluna=token_leia.coluna,
        )

    def _escrita(self) -> WriteStmtNode:
        token_escreva = self._consumir(TokenType.ESCREVA, "Esperado 'escreva'")
        self._consumir(TokenType.ABRE_PAREN, "Esperado '(' após 'escreva'")
        exp = self._expressao()
        self._consumir(TokenType.FECHA_PAREN, "Esperado ')' após expressão no comando 'escreva'")
        self._consumir(TokenType.PONTO_VIRGULA, "Esperado ';' após comando 'escreva'")

        return WriteStmtNode(
            expressao=exp,
            linha=token_escreva.linha,
            coluna=token_escreva.coluna,
        )

    def _expressao(self) -> ASTNode:
        return self._exp_ou()

    def _exp_ou(self) -> ASTNode:
        esq = self._exp_e()
        while self._verificar(TokenType.OU):
            op = self._avancar()
            dir_node = self._exp_e()
            esq = BinaryOpNode(
                esquerda=esq,
                operador=op.lexema,
                direita=dir_node,
                linha=op.linha,
                coluna=op.coluna,
            )
        return esq

    def _exp_e(self) -> ASTNode:
        esq = self._exp_relacional()
        while self._verificar(TokenType.E):
            op = self._avancar()
            dir_node = self._exp_relacional()
            esq = BinaryOpNode(
                esquerda=esq,
                operador=op.lexema,
                direita=dir_node,
                linha=op.linha,
                coluna=op.coluna,
            )
        return esq

    def _exp_relacional(self) -> ASTNode:
        esq = self._exp_aditiva()
        ops_rel = (
            TokenType.IGUAL,
            TokenType.DIFERENTE,
            TokenType.MENOR,
            TokenType.MENOR_IGUAL,
            TokenType.MAIOR,
            TokenType.MAIOR_IGUAL,
        )
        if self._atual().tipo in ops_rel:
            op = self._avancar()
            dir_node = self._exp_aditiva()
            esq = BinaryOpNode(
                esquerda=esq,
                operador=op.lexema,
                direita=dir_node,
                linha=op.linha,
                coluna=op.coluna,
            )
        return esq

    def _exp_aditiva(self) -> ASTNode:
        esq = self._exp_multiplicativa()
        while self._verificar(TokenType.SOMA) or self._verificar(TokenType.SUBTRACAO):
            op = self._avancar()
            dir_node = self._exp_multiplicativa()
            esq = BinaryOpNode(
                esquerda=esq,
                operador=op.lexema,
                direita=dir_node,
                linha=op.linha,
                coluna=op.coluna,
            )
        return esq

    def _exp_multiplicativa(self) -> ASTNode:
        esq = self._exp_unaria()
        while (
            self._verificar(TokenType.MULTIPLICACAO)
            or self._verificar(TokenType.DIVISAO)
            or self._verificar(TokenType.MODULO)
        ):
            op = self._avancar()
            dir_node = self._exp_unaria()
            esq = BinaryOpNode(
                esquerda=esq,
                operador=op.lexema,
                direita=dir_node,
                linha=op.linha,
                coluna=op.coluna,
            )
        return esq

    def _exp_unaria(self) -> ASTNode:
        if self._verificar(TokenType.NAO) or self._verificar(TokenType.SUBTRACAO):
            op = self._avancar()
            operando = self._exp_unaria()
            return UnaryOpNode(
                operador=op.lexema,
                operando=operando,
                linha=op.linha,
                coluna=op.coluna,
            )
        return self._exp_primaria()

    def _exp_primaria(self) -> ASTNode:
        tok = self._atual()

        if self._verificar(TokenType.NUMERO):
            self._avancar()
            return LiteralNode(valor=int(tok.lexema), tipo="inteiro", linha=tok.linha, coluna=tok.coluna)

        if self._verificar(TokenType.VERDADEIRO):
            self._avancar()
            return LiteralNode(valor=True, tipo="booleano", linha=tok.linha, coluna=tok.coluna)

        if self._verificar(TokenType.FALSO):
            self._avancar()
            return LiteralNode(valor=False, tipo="booleano", linha=tok.linha, coluna=tok.coluna)

        if self._verificar(TokenType.IDENTIFICADOR):
            self._avancar()
            return VarAccessNode(nome=tok.lexema, linha=tok.linha, coluna=tok.coluna)

        if self._verificar(TokenType.ABRE_PAREN):
            self._avancar()
            exp = self._expressao()
            self._consumir(TokenType.FECHA_PAREN, "Esperado ')' para fechar expressão")
            return exp

        self._registrar_erro(f"Expressão primária inválida iniciando com '{tok.lexema}'", tok)
        raise _ParseError()
