"""
控制流单元实现 - 同学C负责
"""
import sys
import json
from typing import List, Dict
from interfaces.types import CPUState, CPUStatus, Instruction
from memory.memory_unit import MemoryUnit
from execution.execution_unit import ExecutionUnit

# ========== 控制流单元 - 同学C负责 ==========
class ControlUnit:
    """控制流单元，负责程序执行流程和状态管理"""
    
    def __init__(self, memory: MemoryUnit, execution: ExecutionUnit):
        self.memory = memory
        self.execution = execution
        self.PC = 0
        self.status = CPUStatus.AOK
        self.execution_log: List[CPUState] = []
    
    def load_program(self, input_lines: List[str]) -> bool:
        """加载程序 - 同学C负责"""
        return self.memory.load_program(input_lines)
    
    def step(self) -> CPUState:
        """执行一个指令周期 - 同学C负责"""
        if self.status != CPUStatus.AOK:
            return self.generate_state_log()
        
        try:
            # 1. 取指和解码
            instr = self.execution.decode_instruction(self.PC, self.memory)
            instr_type = self.execution.instruction_set.get(instr.opcode, '')
            
            # 2. 执行
            if instr_type == 'halt':
                self.status = CPUStatus.HLT
                
            elif instr_type == 'nop':
                self.PC += instr.length
                
            elif instr_type == 'rrmovq' or instr.opcode[0] == '2':
                # 条件传送指令
                self.execution.execute_conditional_move(instr)
                self.PC += instr.length
                
            elif instr_type in ['irmovq', 'rmmovq', 'mrmovq']:
                # 数据传送指令
                if not self.execution.execute_move(instr, self.memory):
                    self.status = CPUStatus.ADR
                else:
                    self.PC += instr.length
                    
            elif instr_type in ['addq', 'subq', 'andq', 'xorq']:
                # 算术运算指令
                self.execution.execute_arithmetic(instr)
                self.PC += instr.length
                
            elif instr_type == 'pushq':
                if not self.execute_pushq(instr):
                    self.status = CPUStatus.ADR
                else:
                    self.PC += instr.length
                    
            elif instr_type == 'popq':
                if not self.execute_popq(instr):
                    self.status = CPUStatus.ADR
                else:
                    self.PC += instr.length
                    
            elif instr_type == 'call':
                if not self.execute_call(instr):
                    self.status = CPUStatus.ADR
                    
            elif instr_type == 'ret':
                if not self.execute_ret():
                    self.status = CPUStatus.ADR
                    
            elif instr.opcode[0] == '7':  # 跳转指令
                if not self.execute_jump(instr):
                    self.PC += instr.length
                    
            else:
                self.status = CPUStatus.INS
                
        except Exception as e:
            print(f"执行指令错误 at PC={self.PC}: {e}", file=sys.stderr)
            self.status = CPUStatus.INS
        
        return self.generate_state_log()
    
    def run_until_halt(self) -> List[CPUState]:
        """运行程序直到停机 - 同学C负责"""
        self.execution_log.clear()
        
        while self.status == CPUStatus.AOK:
            state = self.step()
            self.execution_log.append(state)
            
            if self.status != CPUStatus.AOK:
                break
        
        return self.execution_log
    
    def execute_jump(self, instr: Instruction) -> bool:
        """执行跳转指令 - 同学C负责"""
        jump_type = self.execution.instruction_set.get(instr.opcode, '')
        
        if self.check_jump_condition(jump_type):
            self.PC = instr.immediate
            return True
            
        return False
    
    def execute_call(self, instr: Instruction) -> bool:
        """执行call指令 - 同学C负责"""
        # 将返回地址压栈
        return_address = self.PC + instr.length
        
        # 获取当前栈指针
        rsp = self.execution.get_register_value(4)  # %rsp是索引4
        
        # 压栈
        new_rsp = self.memory.push_value(return_address, rsp)
        if new_rsp is None:
            return False
        
        # 更新栈指针
        self.execution.set_register_value(4, new_rsp)
        
        # 跳转到目标地址
        self.PC = instr.immediate
        return True
    
    def execute_ret(self) -> bool:
        """执行ret指令 - 同学C负责"""
        # 获取当前栈指针
        rsp = self.execution.get_register_value(4)
        
        # 出栈获取返回地址
        result = self.memory.pop_value(rsp)
        if result is None:
            return False
            
        return_address, new_rsp = result
        
        # 更新栈指针
        self.execution.set_register_value(4, new_rsp)
        
        # 跳转到返回地址
        self.PC = return_address
        return True
    
    def execute_pushq(self, instr: Instruction) -> bool:
        """执行pushq指令 - 同学C负责"""
        # 获取源寄存器值
        value = self.execution.get_register_value(instr.rA)
        
        # 获取当前栈指针
        rsp = self.execution.get_register_value(4)
        
        # 计算新的栈指针（栈向下增长）
        new_rsp = rsp - 8
        
        # 尝试写入内存
        success = self.memory.write_memory_64(new_rsp, value)
        
        # 关键：无论内存写入是否成功，都要更新栈指针
        # 这是Y86-64的语义：即使内存访问失败，rsp也会被更新
        self.execution.set_register_value(4, new_rsp)
        
        return success  # 返回内存写入是否成功
    
    def execute_popq(self, instr: Instruction) -> bool:
        """执行popq指令 - 同学C负责"""
        # 获取当前栈指针
        rsp = self.execution.get_register_value(4)
        
        # 出栈
        result = self.memory.pop_value(rsp)
        if result is None:
            return False
            
        value, new_rsp = result
        
        # 更新栈指针和目标寄存器
        self.execution.set_register_value(4, new_rsp)
        self.execution.set_register_value(instr.rA, value)
        return True
    
    def check_jump_condition(self, jump_type: str) -> bool:
        """检查跳转条件 - 同学C负责"""
        cc = self.execution.get_condition_codes()
        ZF = cc['ZF']
        SF = cc['SF']
        OF = cc['OF']
        
        if jump_type == 'jmp':
            return True
        elif jump_type == 'jle':
            return ZF or (SF != OF)
        elif jump_type == 'jl':
            return (SF != OF)
        elif jump_type == 'je':
            return ZF
        elif jump_type == 'jne':
            return not ZF
        elif jump_type == 'jge':
            return (SF == OF)
        elif jump_type == 'jg':
            return (not ZF) and (SF == OF)
            
        return False
    
    def generate_state_log(self) -> CPUState:
        """生成状态日志 - 同学C负责（修复格式）"""
        # 获取寄存器状态（按正确答案的顺序）
        registers_raw = self.execution.get_all_registers()
        
        # 按照正确答案的顺序重新排列
        registers = {
            "r10": registers_raw.get("r10", 0),
            "r11": registers_raw.get("r11", 0),
            "r12": registers_raw.get("r12", 0),
            "r13": registers_raw.get("r13", 0),
            "r14": registers_raw.get("r14", 0),
            "r8": registers_raw.get("r8", 0),
            "r9": registers_raw.get("r9", 0),
            "rax": registers_raw.get("rax", 0),
            "rbp": registers_raw.get("rbp", 0),
            "rbx": registers_raw.get("rbx", 0),
            "rcx": registers_raw.get("rcx", 0),
            "rdi": registers_raw.get("rdi", 0),
            "rdx": registers_raw.get("rdx", 0),
            "rsi": registers_raw.get("rsi", 0),
            "rsp": registers_raw.get("rsp", 512)  # 注意：初始rsp=512
        }
        
        # 获取内存非零值
        memory_raw = self.memory.get_nonzero_memory()
        
        # 关键：按字符串键的字典序排序，而不是数值排序
        # 先将所有地址转换为字符串
        memory_items = [(str(addr), memory_raw[addr]) for addr in memory_raw.keys()]
        
        # 按字符串键排序
        memory_items.sort(key=lambda x: x[0])
        
        # 构建排序后的字典
        memory = dict(memory_items)
        
        # 获取条件码
        condition_codes_raw = self.execution.get_condition_codes()
        condition_codes = {
            "OF": condition_codes_raw.get("OF", 0),
            "SF": condition_codes_raw.get("SF", 0),
            "ZF": condition_codes_raw.get("ZF", 1)
        }
        
        return {
            "CC": condition_codes,
            "MEM": memory,
            "PC": self.PC,
            "REG": registers,
            "STAT": self.status.value
        }