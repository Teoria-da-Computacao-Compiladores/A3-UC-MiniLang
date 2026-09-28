import os
import sys

_minilang_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_minilang_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
while _minilang_dir in sys.path:
    sys.path.remove(_minilang_dir)

from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ASTNode:
    linha: int
    coluna: int


@dataclass
class ProgramNode(ASTNode):
    nome: str
    declaracoes: List[ASTNode]
    comandos: List[ASTNode]


@dataclass
class VarDeclNode(ASTNode):
    nome: str
    tipo: str


@dataclass
class ParamNode(ASTNode):
    nome: str
    tipo: str


@dataclass
class ProcedureDeclNode(ASTNode):
    nome: str
    parametros: List[ParamNode]
    declaracoes: List[VarDeclNode]
    comandos: List[ASTNode]


@dataclass
class AssignStmtNode(ASTNode):
    identificador: str
    expressao: ASTNode


@dataclass
class CallStmtNode(ASTNode):
    identificador: str
    argumentos: List[ASTNode]


@dataclass
class IfStmtNode(ASTNode):
    condicao: ASTNode
    entao_comandos: List[ASTNode]
    senao_comandos: Optional[List[ASTNode]]


@dataclass
class WhileStmtNode(ASTNode):
    condicao: ASTNode
    comandos: List[ASTNode]


@dataclass
class ReadStmtNode(ASTNode):
    identificador: str


@dataclass
class WriteStmtNode(ASTNode):
    expressao: ASTNode


@dataclass
class BinaryOpNode(ASTNode):
    esquerda: ASTNode
    operador: str
    direita: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    operador: str
    operando: ASTNode


@dataclass
class LiteralNode(ASTNode):
    valor: Any
    tipo: str


@dataclass
class VarAccessNode(ASTNode):
    nome: str


def formatar_ast(no: ASTNode, nivel: int = 0) -> str:
    espaco = "  " * nivel

    if isinstance(no, ProgramNode):
        linhas = [f"{espaco}Programa '{no.nome}' [linha {no.linha}, col {no.coluna}]:"]
        if no.declaracoes:
            linhas.append(f"{espaco}  Declarações:")
            for decl in no.declaracoes:
                linhas.append(formatar_ast(decl, nivel + 2))
        if no.comandos:
            linhas.append(f"{espaco}  Comandos:")
            for cmd in no.comandos:
                linhas.append(formatar_ast(cmd, nivel + 2))
        return "\n".join(linhas)

    if isinstance(no, VarDeclNode):
        return f"{espaco}VarDecl: {no.nome}: {no.tipo} [linha {no.linha}, col {no.coluna}]"

    if isinstance(no, ParamNode):
        return f"{espaco}Param: {no.nome}: {no.tipo} [linha {no.linha}, col {no.coluna}]"

    if isinstance(no, ProcedureDeclNode):
        linhas = [f"{espaco}Procedimento '{no.nome}' [linha {no.linha}, col {no.coluna}]:"]
        if no.parametros:
            linhas.append(f"{espaco}  Parâmetros:")
            for param in no.parametros:
                linhas.append(formatar_ast(param, nivel + 2))
        if no.declaracoes:
            linhas.append(f"{espaco}  Declarações locais:")
            for decl in no.declaracoes:
                linhas.append(formatar_ast(decl, nivel + 2))
        if no.comandos:
            linhas.append(f"{espaco}  Corpo:")
            for cmd in no.comandos:
                linhas.append(formatar_ast(cmd, nivel + 2))
        return "\n".join(linhas)

    if isinstance(no, AssignStmtNode):
        linhas = [
            f"{espaco}Atribuicao: {no.identificador} = [linha {no.linha}, col {no.coluna}]",
            formatar_ast(no.expressao, nivel + 1),
        ]
        return "\n".join(linhas)

    if isinstance(no, CallStmtNode):
        linhas = [f"{espaco}ChamadaProcedimento: {no.identificador}() [linha {no.linha}, col {no.coluna}]"]
        if no.argumentos:
            linhas.append(f"{espaco}  Argumentos:")
            for arg in no.argumentos:
                linhas.append(formatar_ast(arg, nivel + 2))
        return "\n".join(linhas)

    if isinstance(no, IfStmtNode):
        linhas = [
            f"{espaco}Se [linha {no.linha}, col {no.coluna}]:",
            f"{espaco}  Condição:",
            formatar_ast(no.condicao, nivel + 2),
            f"{espaco}  Então:",
        ]
        for cmd in no.entao_comandos:
            linhas.append(formatar_ast(cmd, nivel + 2))
        if no.senao_comandos is not None:
            linhas.append(f"{espaco}  Senão:")
            for cmd in no.senao_comandos:
                linhas.append(formatar_ast(cmd, nivel + 2))
        return "\n".join(linhas)

    if isinstance(no, WhileStmtNode):
        linhas = [
            f"{espaco}Enquanto [linha {no.linha}, col {no.coluna}]:",
            f"{espaco}  Condição:",
            formatar_ast(no.condicao, nivel + 2),
            f"{espaco}  Comandos:",
        ]
        for cmd in no.comandos:
            linhas.append(formatar_ast(cmd, nivel + 2))
        return "\n".join(linhas)

    if isinstance(no, ReadStmtNode):
        return f"{espaco}Leia: {no.identificador} [linha {no.linha}, col {no.coluna}]"

    if isinstance(no, WriteStmtNode):
        linhas = [
            f"{espaco}Escreva [linha {no.linha}, col {no.coluna}]:",
            formatar_ast(no.expressao, nivel + 1),
        ]
        return "\n".join(linhas)

    if isinstance(no, BinaryOpNode):
        linhas = [
            f"{espaco}BinaryOp: ({no.operador}) [linha {no.linha}, col {no.coluna}]",
            formatar_ast(no.esquerda, nivel + 1),
            formatar_ast(no.direita, nivel + 1),
        ]
        return "\n".join(linhas)

    if isinstance(no, UnaryOpNode):
        linhas = [
            f"{espaco}UnaryOp: ({no.operador}) [linha {no.linha}, col {no.coluna}]",
            formatar_ast(no.operando, nivel + 1),
        ]
        return "\n".join(linhas)

    if isinstance(no, LiteralNode):
        return f"{espaco}Literal: {no.valor!r} ({no.tipo}) [linha {no.linha}, col {no.coluna}]"

    if isinstance(no, VarAccessNode):
        return f"{espaco}Var: {no.nome} [linha {no.linha}, col {no.coluna}]"

    return f"{espaco}Desconhecido({no})"
