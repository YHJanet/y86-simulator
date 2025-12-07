"""
数据类型定义 - 三人共同确定
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, TypedDict, Union


class CPUStatus(Enum):
    """CPU状态码枚举"""
    AOK = 1  # 正常
    HLT = 2  # 停机
    ADR = 3  # 非法地址
    INS = 4  # 非法指令


@dataclass
class Instruction:
    """指令数据结构"""
    opcode: str
    length: int
    rA: int = 0
    rB: int = 0
    immediate: int = 0
    address: int = 0


# 类型定义
CPUState = TypedDict('CPUState', {
    'PC': int,
    'REG': Dict[str, int],
    'MEM': Dict[int, int],
    'CC': Dict[str, int],
    'STAT': int
})

RegisterMap = Dict[str, int]
MemoryMap = Dict[int, int]
ConditionCodes = Dict[str, int]


# 寄存器名称映射
REGISTER_NAMES = [
    'rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi',
    'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14'
]

# 指令集映射
INSTRUCTION_SET = {
    '00': 'halt', '10': 'nop',
    '20': 'rrmovq', '21': 'cmovle', '22': 'cmovl', '23': 'cmove',
    '24': 'cmovne', '25': 'cmovge', '26': 'cmovg',
    '30': 'irmovq', '40': 'rmmovq', '50': 'mrmovq',
    '60': 'addq', '61': 'subq', '62': 'andq', '63': 'xorq',
    '70': 'jmp', '71': 'jle', '72': 'jl', '73': 'je',
    '74': 'jne', '75': 'jge', '76': 'jg',
    '80': 'call', '90': 'ret', 'A0': 'pushq', 'B0': 'popq'
}