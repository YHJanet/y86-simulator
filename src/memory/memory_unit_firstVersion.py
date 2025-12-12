import sys
from typing import List, Dict, Optional
from interfaces.types import MemoryMap

class MemoryUnit:
    # 内存管理单元，负责内存读写和栈操作
    
    def __init__(self, memory_size: int = 10000):
        self.memory: List[int] = [0] * memory_size
        self.memory_size = memory_size
        
    def load_program(self, input_lines: List[str]) -> bool:
        try:
            for line in input_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '|' in line:
                    line = line.split('|')[0].strip()
                
                if ':' not in line:
                    continue
                
                addr_str, inst_str = line.split(':', 1)
                addr_str = addr_str.strip()
                inst_str = inst_str.strip().replace(' ', '')
                
                if not addr_str or not inst_str:
                    continue
                
                try:
                    address = int(addr_str, 16)
                    
                    if len(inst_str) % 2 != 0:
                        inst_str = '0' + inst_str
                    
                    for i in range(0, len(inst_str), 2):
                        byte_str = inst_str[i:i+2]
                        byte_value = int(byte_str, 16)
                        
                        write_addr = address + i//2
                        if write_addr < self.memory_size:
                            self.memory[write_addr] = byte_value
                            
                except ValueError:
                    continue
            return True
            
        except Exception as e:
            print(f"加载程序错误: {e}", file=sys.stderr)
            return False
    
    def read_memory_64(self, address: int) -> Optional[int]:
        # 小端法读取8字节数据
        if not self._check_address_bounds(address, 8):
            return None

        value = 0
        for i in range(8):
            byte_value = self.memory[address + i]
            value |= (byte_value << (i * 8))
        
        if value & (1 << 63):
            value = value - (1 << 64)
            
        return value
    
    def write_memory_64(self, address: int, value: int) -> bool:
        # 小端法向内存写入8字节数据
        if not self._check_address_bounds(address, 8):
            return False
        if address % 8 != 0:
            return False
        
        if value < 0:
            value = (1 << 64) + value
        
        for i in range(8):
            byte_value = (value >> (i * 8)) & 0xFF
            self.memory[address + i] = byte_value
            
        return True
    
    def push_value(self, value: int, rsp: int) -> Optional[int]:
        # 值压栈
        new_rsp = rsp - 8
        if not self.write_memory_64(new_rsp, value):
            return None
        return new_rsp
    
    def pop_value(self, rsp: int) -> Optional[tuple]:
        # 值出栈
        value = self.read_memory_64(rsp)
        if value is None:
            return None
        new_rsp = rsp + 8
        return (value, new_rsp)
    
    def extract_immediate(self, start_address: int) -> Optional[int]:
        return self.read_memory_64(start_address)
    
    def get_nonzero_memory(self) -> MemoryMap:
        # 获取所有非零内存
        nonzero_mem: MemoryMap = {}
        
        for addr in range(0, self.memory_size, 8):
            if addr + 8 > self.memory_size:
                break
                
            value = self.read_memory_64(addr)
            if value is not None and value != 0:
                nonzero_mem[addr] = value
                    
        return nonzero_mem
    
    def read_byte(self, address: int) -> Optional[int]:
        if not self._check_address_bounds(address):
            return None
        return self.memory[address]
    
    def write_byte(self, address: int, value: int) -> bool:
        if not self._check_address_bounds(address):
            return False
        if value < 0 or value > 255:
            return False
            
        self.memory[address] = value
        return True
    
    def _check_address_bounds(self, address: int, size: int = 1) -> bool:
        return 0 <= address < self.memory_size and (address + size) <= self.memory_size