import sys
from typing import Dict, Optional, List
from interfaces.types import Instruction, RegisterMap, ConditionCodes
from memory.memory_unit import MemoryUnit

class ExecutionUnit:
    # 指令执行单元，负责指令解码和算术运算
    
    def __init__(self):
        self.registers: List[int] = [0] * 15
        self.registers[4] = 0
        
        self.ZF: int = 1
        self.SF: int = 0
        self.OF: int = 0
        
        self.instruction_set = {
            '00': 'halt', '10': 'nop',
            '20': 'rrmovq', '21': 'cmovle', '22': 'cmovl', '23': 'cmove',
            '24': 'cmovne', '25': 'cmovge', '26': 'cmovg',
            '30': 'irmovq', '40': 'rmmovq', '50': 'mrmovq',
            '60': 'addq', '61': 'subq', '62': 'andq', '63': 'xorq',
            '70': 'jmp', '71': 'jle', '72': 'jl', '73': 'je',
            '74': 'jne', '75': 'jge', '76': 'jg',
            '80': 'call', '90': 'ret', 'A0': 'pushq', 'B0': 'popq'
        }
    
    def decode_instruction(self, pc: int, memory: MemoryUnit) -> Instruction:
        # 解码指令
        try:
            opcode_byte = memory.read_byte(pc)
            if opcode_byte is None:
                raise ValueError(f"无法读取地址 {pc} 的操作码")
                
            opcode = f"{opcode_byte:02X}"
            
            if opcode not in self.instruction_set:
                raise ValueError(f"未知操作码: {opcode}")
            
            instr_type = self.instruction_set[opcode]
            instr = Instruction(opcode=opcode, length=1, address=pc)
            
            if instr_type == 'rrmovq' or opcode[0] == '2':
                instr.length = 2
                byte2 = memory.read_byte(pc + 1)
                if byte2 is not None:
                    instr.rA = (byte2 >> 4) & 0xF
                    instr.rB = byte2 & 0xF
                    
            elif instr_type == 'irmovq':
                instr.length = 10
                byte2 = memory.read_byte(pc + 1)
                if byte2 is not None:
                    instr.rB = byte2 & 0xF
                imm = memory.extract_immediate(pc + 2)
                if imm is not None:
                    instr.immediate = imm
                    
            elif instr_type in ['rmmovq', 'mrmovq']:
                instr.length = 10
                byte2 = memory.read_byte(pc + 1)
                if byte2 is not None:
                    instr.rA = (byte2 >> 4) & 0xF
                    instr.rB = byte2 & 0xF
                imm = memory.extract_immediate(pc + 2)
                if imm is not None:
                    instr.immediate = imm
                    
            elif instr_type in ['addq', 'subq', 'andq', 'xorq']:
                instr.length = 2
                byte2 = memory.read_byte(pc + 1)
                if byte2 is not None:
                    instr.rA = (byte2 >> 4) & 0xF
                    instr.rB = byte2 & 0xF
                    
            elif opcode[0] == '7' or instr_type == 'call':
                instr.length = 9
                imm = memory.extract_immediate(pc + 1)
                if imm is not None:
                    instr.immediate = imm
                    
            elif instr_type in ['pushq', 'popq']:
                instr.length = 2
                byte2 = memory.read_byte(pc + 1)
                if byte2 is not None:
                    instr.rA = (byte2 >> 4) & 0xF
                    
            elif instr_type == 'nop':
                instr.length = 1
                
            elif instr_type == 'halt':
                instr.length = 1
                
            elif instr_type == 'ret':
                instr.length = 1
                
            return instr
            
        except Exception as e:
            print(f"解码指令错误 at PC={pc}: {e}", file=sys.stderr)
            return Instruction(opcode='00', length=1, address=pc)
    
    def execute_arithmetic(self, instr: Instruction) -> bool:
        # 执行算术运算指令
        instr_type = self.instruction_set.get(instr.opcode)
        
        if instr_type == 'addq':
            return self.execute_addq(instr.rA, instr.rB)
        elif instr_type == 'subq':
            return self.execute_subq(instr.rA, instr.rB)
        elif instr_type == 'andq':
            return self.execute_andq(instr.rA, instr.rB)
        elif instr_type == 'xorq':
            return self.execute_xorq(instr.rA, instr.rB)
            
        return False
    
    def execute_addq(self, rA: int, rB: int) -> bool:
        # 执行addq指令
        valA = self.get_register_value(rA)
        valB = self.get_register_value(rB)
        result = valB + valA
        
        self.set_register_value(rB, result)
        self.update_condition_codes(result, valA, valB, 'add')
        return True
    
    def execute_subq(self, rA: int, rB: int) -> bool:
        # 执行subq指令
        valA = self.get_register_value(rA)
        valB = self.get_register_value(rB)
        result = valB - valA
        
        self.set_register_value(rB, result)
        self.update_condition_codes(result, valA, valB, 'sub')
        return True
    
    def execute_andq(self, rA: int, rB: int) -> bool:
        # 执行andq指令
        valA = self.get_register_value(rA)
        valB = self.get_register_value(rB)
        result = valB & valA
        
        self.set_register_value(rB, result)
        self.update_condition_codes(result, valA, valB, 'and')
        return True
    
    def execute_xorq(self, rA: int, rB: int) -> bool:
        # 执行xorq指令
        valA = self.get_register_value(rA)
        valB = self.get_register_value(rB)
        result = valB ^ valA
        
        self.set_register_value(rB, result)
        self.update_condition_codes(result, valA, valB, 'xor')
        return True
    
    def execute_move(self, instr: Instruction, memory: MemoryUnit) -> bool:
        # 执行数据传送指令
        instr_type = self.instruction_set.get(instr.opcode)
        
        if instr_type == 'rrmovq':
            return self.execute_rrmovq(instr.rA, instr.rB)
        elif instr_type == 'irmovq':
            return self.execute_irmovq(instr.rB, instr.immediate)
        elif instr_type == 'rmmovq':
            return self.execute_rmmovq(instr.rA, instr.rB, instr.immediate, memory)
        elif instr_type == 'mrmovq':
            return self.execute_mrmovq(instr.rA, instr.rB, instr.immediate, memory)
            
        return False
    
    def execute_rrmovq(self, rA: int, rB: int) -> bool:
        self.set_register_value(rB, self.get_register_value(rA))
        return True
    
    def execute_irmovq(self, rB: int, immediate: int) -> bool:
        self.set_register_value(rB, immediate)
        return True
    
    def execute_rmmovq(self, rA: int, rB: int, offset: int, memory: MemoryUnit) -> bool:
        address = self.get_register_value(rB) + offset
        value = self.get_register_value(rA)
        return memory.write_memory_64(address, value)
    
    def execute_mrmovq(self, rA: int, rB: int, offset: int, memory: MemoryUnit) -> bool:
        address = self.get_register_value(rB) + offset
        value = memory.read_memory_64(address)
        if value is not None:
            self.set_register_value(rA, value)
            return True
        return False
    
    def execute_conditional_move(self, instr: Instruction) -> bool:
        # 执行条件传送指令
        condition_code = instr.opcode[1]
        
        condition_met = False
        if condition_code == '0':
            condition_met = True
        elif condition_code == '1':
            condition_met = self.ZF or (self.SF != self.OF)
        elif condition_code == '2':
            condition_met = (self.SF != self.OF)
        elif condition_code == '3':
            condition_met = self.ZF
        elif condition_code == '4':
            condition_met = not self.ZF
        elif condition_code == '5':
            condition_met = (self.SF == self.OF)
        elif condition_code == '6':
            condition_met = (not self.ZF) and (self.SF == self.OF)
        
        if condition_met:
            self.set_register_value(instr.rB, self.get_register_value(instr.rA))
            
        return True
    
    def update_condition_codes(self, result: int, valA: int, valB: int, operation: str):
        # 更新条件码
        self.ZF = 1 if result == 0 else 0
        self.SF = 1 if result < 0 else 0
        
        if operation == 'add':
            self.OF = 1 if ((valA > 0 and valB > 0 and result < 0) or 
                           (valA < 0 and valB < 0 and result > 0)) else 0
        elif operation == 'sub':
            if (valB >= 0 and valA < 0 and result < 0) or \
               (valB < 0 and valA >= 0 and result > 0):
                self.OF = 1
            else:
                self.OF = 0
        else:
            self.OF = 0
    
    def get_register_value(self, reg_index: int) -> int:
        if 0 <= reg_index < len(self.registers):
            return self.registers[reg_index]
        return 0
    
    def set_register_value(self, reg_index: int, value: int) -> bool:
        if 0 <= reg_index < len(self.registers):
            self.registers[reg_index] = value
            return True
        return False
    
    def get_all_registers(self) -> RegisterMap:
        reg_names = [
            'rax', 'rcx', 'rdx', 'rbx', 'rsp', 'rbp', 'rsi', 'rdi',
            'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14'
        ]
        return {name: self.registers[i] for i, name in enumerate(reg_names)}
    
    def get_condition_codes(self) -> ConditionCodes:
        return {'ZF': self.ZF, 'SF': self.SF, 'OF': self.OF}