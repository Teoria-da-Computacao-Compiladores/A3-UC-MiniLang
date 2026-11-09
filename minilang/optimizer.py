import os
import sys

_minilang_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_minilang_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)
while _minilang_dir in sys.path:
    sys.path.remove(_minilang_dir)

from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional

from minilang.ast import (
    ASTNode,
    AssignStmtNode,
    BinaryOpNode,
    CallStmtNode,
    IfStmtNode,
    LiteralNode,
    ProcedureDeclNode,
    ProgramNode,
    UnaryOpNode,
    VarAccessNode,
    WhileStmtNode,
    WriteStmtNode,
)
from minilang.interpreter import (
    aplicar_binaria,
    aplicar_unaria,
    formatar_valor,
    normalizar_operador,
)

DOBRAMENTO = "dobramento de constantes"
ALGEBRICA = "simplificação algébrica"
CODIGO_MORTO = "eliminação de código morto"

TIPOS_OTIMIZACAO = (DOBRAMENTO, ALGEBRICA, CODIGO_MORTO)


@dataclass(frozen=True)
class Otimizacao:
    tipo: str
    linha: int
    coluna: int
    descricao: str

    def __str__(self) -> str:
        return f"[linha {self.linha}, coluna {self.coluna}] {self.tipo}: {self.descricao}"


def _e_inteiro(no: ASTNode, valor: int) -> bool:
    return (
        isinstance(no, LiteralNode)
        and isinstance(no.valor, int)
        and not isinstance(no.valor, bool)
        and no.valor == valor
    )


def _e_booleano(no: ASTNode, valor: bool) -> bool:
    return isinstance(no, LiteralNode) and isinstance(no.valor, bool) and no.valor is valor


def _e_literal(no: ASTNode) -> bool:
    return isinstance(no, LiteralNode)


def _sem_falha(no: ASTNode) -> bool:
    if isinstance(no, (LiteralNode, VarAccessNode)):
        return True
    if isinstance(no, UnaryOpNode):
        return _sem_falha(no.operando)
    if isinstance(no, BinaryOpNode):
        if normalizar_operador(no.operador) in ("/", "%"):
            if not (_e_literal(no.direita) and not _e_inteiro(no.direita, 0)):
                return False
        return _sem_falha(no.esquerda) and _sem_falha(no.direita)
    return False


def _texto(no: ASTNode) -> str:
    if isinstance(no, LiteralNode):
        return formatar_valor(no.valor)
    if isinstance(no, VarAccessNode):
        return no.nome
    if isinstance(no, UnaryOpNode):
        return f"{normalizar_operador(no.operador)} {_texto(no.operando)}"
    if isinstance(no, BinaryOpNode):
        return f"({_texto(no.esquerda)} {normalizar_operador(no.operador)} {_texto(no.direita)})"
    return type(no).__name__


def _copiar(no: ASTNode, **mudancas: Any) -> ASTNode:
    novo = replace(no, **mudancas)
    novo.tipo_inferido = no.tipo_inferido
    return novo


def _literal(valor: Any, modelo: ASTNode) -> LiteralNode:
    tipo = "booleano" if isinstance(valor, bool) else "inteiro"
    novo = LiteralNode(modelo.linha, modelo.coluna, valor, tipo)
    novo.tipo_inferido = tipo
    return novo


class Otimizador:
    def __init__(self) -> None:
        self.registros: List[Otimizacao] = []

    @property
    def total(self) -> int:
        return len(self.registros)

    def contagem(self) -> Dict[str, int]:
        resultado = {tipo: 0 for tipo in TIPOS_OTIMIZACAO}
        for registro in self.registros:
            resultado[registro.tipo] += 1
        return resultado

    def _registrar(self, tipo: str, no: ASTNode, descricao: str) -> None:
        self.registros.append(Otimizacao(tipo, no.linha, no.coluna, descricao))

    def otimizar(self, programa: ProgramNode) -> ProgramNode:
        declaracoes = [self._declaracao(declaracao) for declaracao in programa.declaracoes]
        comandos = self._comandos(programa.comandos)
        return _copiar(programa, declaracoes=declaracoes, comandos=comandos)

    def _declaracao(self, no: ASTNode) -> ASTNode:
        if isinstance(no, ProcedureDeclNode):
            return _copiar(no, comandos=self._comandos(no.comandos))
        return no

    def _comandos(self, comandos: List[ASTNode]) -> List[ASTNode]:
        resultado: List[ASTNode] = []
        for comando in comandos:
            resultado.extend(self._comando(comando))
        return resultado

    def _comando(self, no: ASTNode) -> List[ASTNode]:
        if isinstance(no, AssignStmtNode):
            return [_copiar(no, expressao=self._expressao(no.expressao))]

        if isinstance(no, CallStmtNode):
            return [_copiar(no, argumentos=[self._expressao(arg) for arg in no.argumentos])]

        if isinstance(no, WriteStmtNode):
            return [_copiar(no, expressao=self._expressao(no.expressao))]

        if isinstance(no, IfStmtNode):
            return self._condicional(no)

        if isinstance(no, WhileStmtNode):
            condicao = self._expressao(no.condicao)
            if _e_booleano(condicao, False):
                self._registrar(
                    CODIGO_MORTO,
                    no,
                    "laço 'enquanto' com condição sempre falsa removido",
                )
                return []
            return [_copiar(no, condicao=condicao, comandos=self._comandos(no.comandos))]

        return [no]

    def _condicional(self, no: IfStmtNode) -> List[ASTNode]:
        condicao = self._expressao(no.condicao)
        entao = self._comandos(no.entao_comandos)
        senao = self._comandos(no.senao_comandos) if no.senao_comandos is not None else None

        if _e_booleano(condicao, True):
            detalhe = "ramo 'senão' inalcançável removido" if no.senao_comandos is not None else "teste removido"
            self._registrar(CODIGO_MORTO, no, f"condição do 'se' sempre verdadeira: {detalhe}")
            return entao

        if _e_booleano(condicao, False):
            self._registrar(CODIGO_MORTO, no, "condição do 'se' sempre falsa: ramo 'então' inalcançável removido")
            return senao or []

        return [_copiar(no, condicao=condicao, entao_comandos=entao, senao_comandos=senao)]

    def _expressao(self, no: ASTNode) -> ASTNode:
        if isinstance(no, UnaryOpNode):
            return self._unaria(no)
        if isinstance(no, BinaryOpNode):
            return self._binaria(no)
        return no

    def _unaria(self, no: UnaryOpNode) -> ASTNode:
        operando = self._expressao(no.operando)
        operador = normalizar_operador(no.operador)

        if _e_literal(operando):
            valor = aplicar_unaria(operador, operando.valor)
            novo = _literal(valor, no)
            self._registrar(
                DOBRAMENTO, no, f"'{operador} {_texto(operando)}' calculado em compilação: {formatar_valor(valor)}"
            )
            return novo

        if isinstance(operando, UnaryOpNode) and normalizar_operador(operando.operador) == operador:
            interno = _texto(operando.operando)
            self._registrar(
                ALGEBRICA, no, f"'{operador} {operador} {interno}' simplificado para '{interno}'"
            )
            return operando.operando

        return _copiar(no, operando=operando)

    def _binaria(self, no: BinaryOpNode) -> ASTNode:
        esquerda = self._expressao(no.esquerda)
        direita = self._expressao(no.direita)
        operador = normalizar_operador(no.operador)
        original = f"{_texto(esquerda)} {operador} {_texto(direita)}"

        if _e_literal(esquerda) and _e_literal(direita):
            try:
                valor = aplicar_binaria(operador, esquerda.valor, direita.valor)
            except ZeroDivisionError:
                pass
            else:
                self._registrar(
                    DOBRAMENTO, no, f"'{original}' calculado em compilação: {formatar_valor(valor)}"
                )
                return _literal(valor, no)

        simplificado = self._simplificar(operador, esquerda, direita, no)
        if simplificado is not None:
            self._registrar(ALGEBRICA, no, f"'{original}' simplificado para '{_texto(simplificado)}'")
            return simplificado

        return _copiar(no, esquerda=esquerda, direita=direita)

    def _simplificar(
        self, operador: str, esquerda: ASTNode, direita: ASTNode, no: BinaryOpNode
    ) -> Optional[ASTNode]:
        if operador == "+":
            if _e_inteiro(direita, 0):
                return esquerda
            if _e_inteiro(esquerda, 0):
                return direita

        elif operador == "-":
            if _e_inteiro(direita, 0):
                return esquerda

        elif operador == "*":
            if _e_inteiro(direita, 1):
                return esquerda
            if _e_inteiro(esquerda, 1):
                return direita
            if _e_inteiro(direita, 0) and _sem_falha(esquerda):
                return _literal(0, no)
            if _e_inteiro(esquerda, 0) and _sem_falha(direita):
                return _literal(0, no)

        elif operador == "/":
            if _e_inteiro(direita, 1):
                return esquerda

        elif operador == "%":
            if _e_inteiro(direita, 1) and _sem_falha(esquerda):
                return _literal(0, no)

        elif operador == "e":
            if _e_booleano(esquerda, True):
                return direita
            if _e_booleano(direita, True):
                return esquerda
            if _e_booleano(esquerda, False):
                return _literal(False, no)
            if _e_booleano(direita, False) and _sem_falha(esquerda):
                return _literal(False, no)

        elif operador == "ou":
            if _e_booleano(esquerda, False):
                return direita
            if _e_booleano(direita, False):
                return esquerda
            if _e_booleano(esquerda, True):
                return _literal(True, no)
            if _e_booleano(direita, True) and _sem_falha(esquerda):
                return _literal(True, no)

        return None
