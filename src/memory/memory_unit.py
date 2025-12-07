"""
内存管理单元实现 - 同学B负责
"""
import sys
from typing import List, Dict, Optional
from interfaces.types import MemoryMap

# ========== 内存管理单元 - 同学B负责 ==========
class MemoryUnit:
    """内存管理单元，负责内存读写和栈操作"""
    
    def __init__(self, memory_size: int = 10000):
        # 内存以字节数组形式存储，每个元素一个字节（0-255）
        self.memory: List[int] = [0] * memory_size
        self.memory_size = memory_size
        
    def load_program(self, input_lines: List[str]) -> bool:
        """加载程序到内存 - 同学B负责"""
        try:
            for line in input_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # 解析格式: "0x000: 30f20a00000000000000 |   irmovq $10,%rdx"
                if '|' in line:
                    line = line.split('|')[0].strip()
                
                if ':' not in line:
                    continue
                
                addr_str, inst_str = line.split(':', 1)
                addr_str = addr_str.strip()
                inst_str = inst_str.strip().replace(' ', '')  # 移除所有空格
                
                if not addr_str or not inst_str:
                    continue
                
                try:
                    address = int(addr_str, 16)  # 16进制转10进制
                    
                    # 确保指令字符串长度为偶数
                    if len(inst_str) % 2 != 0:
                        inst_str = '0' + inst_str  # 前面补0
                    
                    # 每2个字符是一个字节
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
        """从内存读取8字节数据（小端法）- 同学B负责"""
        if not self._check_address_bounds(address, 8):
            return None
        #if address % 8 != 0:
        #    return None
            
        # 小端法读取8字节
        value = 0
        for i in range(8):
            byte_value = self.memory[address + i]
            value |= (byte_value << (i * 8))
        
        # 处理有符号数（补码）
        if value & (1 << 63):
            value = value - (1 << 64)
            
        return value
    
    def write_memory_64(self, address: int, value: int) -> bool:
        """向内存写入8字节数据（小端法）- 同学B负责"""
        if not self._check_address_bounds(address, 8):
            return False
        if address % 8 != 0:
            return False
        
        # 处理有符号数
        if value < 0:
            value = (1 << 64) + value
        
        # 小端法写入8字节
        for i in range(8):
            byte_value = (value >> (i * 8)) & 0xFF
            self.memory[address + i] = byte_value
            
        return True
    
    def push_value(self, value: int, rsp: int) -> Optional[int]:
        """值压栈，返回新的栈指针 - 同学B负责"""
        new_rsp = rsp - 8
        if not self.write_memory_64(new_rsp, value):
            return None
        return new_rsp
    
    def pop_value(self, rsp: int) -> Optional[tuple]:
        """值出栈，返回(值, 新栈指针) - 同学B负责"""
        value = self.read_memory_64(rsp)
        if value is None:
            return None
        new_rsp = rsp + 8
        return (value, new_rsp)
    
    def extract_immediate(self, start_address: int) -> Optional[int]:
        """提取立即数（小端法）- 同学B负责"""
        return self.read_memory_64(start_address)
    
    def get_nonzero_memory(self) -> MemoryMap:
        """获取所有非零内存（8字节对齐）- 同学B负责"""
        nonzero_mem: MemoryMap = {}
        
        # 每8字节检查一次
        for addr in range(0, self.memory_size, 8):
            # 检查是否在内存边界内
            if addr + 8 > self.memory_size:
                break
                
            # 读取8字节值
            value = self.read_memory_64(addr)
            if value is not None and value != 0:
                nonzero_mem[addr] = value
                    
        return nonzero_mem
    
    def read_byte(self, address: int) -> Optional[int]:
        """读取单个字节 - 同学B负责"""
        if not self._check_address_bounds(address):
            return None
        return self.memory[address]
    
    def write_byte(self, address: int, value: int) -> bool:
        """写入单个字节 - 同学B负责"""
        if not self._check_address_bounds(address):
            return False
        if value < 0 or value > 255:
            return False
            
        self.memory[address] = value
        return True
    
    def _check_address_bounds(self, address: int, size: int = 1) -> bool:
        """检查地址边界 - 同学B负责"""
        return 0 <= address < self.memory_size and (address + size) <= self.memory_size