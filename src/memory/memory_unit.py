"""
内存管理单元 - 带缓存版本
简化缓存策略：写穿透 + 写不分配
"""
import sys
from typing import List, Dict, Optional, Tuple
from interfaces.types import MemoryMap

class CacheLine:
    def __init__(self, line_size: int = 8):
        self.valid: bool = False
        self.tag: int = 0
        self.data: List[int] = [0] * line_size
        self.address: int = 0

class Cache:
    # 直接映射缓存
    def __init__(self, cache_size: int = 1024, line_size: int = 8):
        self.cache_size = cache_size
        self.line_size = line_size
        self.num_lines = cache_size // line_size
        
        self.lines: List[CacheLine] = [CacheLine(line_size) for _ in range(self.num_lines)]
        
        self.hits = 0
        self.misses = 0
        self.accesses = 0
        
        # 计算偏移量和索引的位数
        self.offset_bits = line_size.bit_length() - 1
        self.index_bits = self.num_lines.bit_length() - 1
        
        self.offset_mask = (1 << self.offset_bits) - 1
        self.index_mask = (1 << self.index_bits) - 1
    
    def get_index_and_tag(self, address: int) -> Tuple[int, int]:
        index = (address >> self.offset_bits) & self.index_mask
        tag = address >> (self.offset_bits + self.index_bits)
        return index, tag
    
    def read_byte(self, address: int, memory: Dict[int, int]) -> Optional[int]:
        self.accesses += 1
        
        index, tag = self.get_index_and_tag(address)
        line = self.lines[index]

        if line.valid and line.tag == tag:
            self.hits += 1
            offset = address & self.offset_mask
            return line.data[offset]
        else:
            self.misses += 1
            return self._load_line(address, memory)
    
    def write_byte(self, address: int, value: int, memory: Dict[int, int]) -> bool:
        self.accesses += 1
        
        index, tag = self.get_index_and_tag(address)
        line = self.lines[index]
        offset = address & self.offset_mask
        
        # 写穿透：直接写入内存
        memory[address] = value
        
        # 如果缓存行有效且标签匹配，也更新缓存
        if line.valid and line.tag == tag:
            self.hits += 1
            line.data[offset] = value
        else:
            # 写不分配：未命中时不加载缓存行
            self.misses += 1
        
        return True
    
    def _load_line(self, address: int, memory: Dict[int, int]) -> Optional[int]:
        base_addr = address & ~self.offset_mask
        
        index, tag = self.get_index_and_tag(address)
        line = self.lines[index]
        
        for i in range(self.line_size):
            load_addr = base_addr + i
            # 从Map读取，如果不存在则返回0
            line.data[i] = memory.get(load_addr, 0)

        line.valid = True
        line.tag = tag
        line.address = base_addr

        offset = address & self.offset_mask
        return line.data[offset]
    def get_stats(self) -> Dict[str, float]:
        hit_rate = (self.hits / self.accesses * 100) if self.accesses > 0 else 0
        return {
            "accesses": self.accesses,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate
        }

class MemoryUnit:
    # 带缓存，使用Map存储内存
    
    def __init__(self, cache_size: int = 1024):
        self.memory: Dict[int, int] = {}
        
        self.cache = Cache(cache_size=cache_size, line_size=8)
        
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
                        # 直接写入内存Map
                        self.memory[write_addr] = byte_value
                        # 如果该地址在缓存中，也需要更新
                        self._update_cache_if_present(write_addr, byte_value)
                            
                except ValueError:
                    continue
            return True
            
        except Exception as e:
            print(f"加载程序错误: {e}", file=sys.stderr)
            return False
    
    def _update_cache_if_present(self, address: int, value: int):
        index, tag = self.cache.get_index_and_tag(address)
        line = self.cache.lines[index]
        
        if line.valid and line.tag == tag:
            offset = address & self.cache.offset_mask
            line.data[offset] = value
    
    def read_memory_64(self, address: int) -> Optional[int]:
        if address < 0:
            return None
        
        value = 0
        for i in range(8):
            byte_value = self.read_byte(address + i)
            if byte_value is None:
                return None
            value |= (byte_value << (i * 8))
        
        if value & (1 << 63):
            value = value - (1 << 64)
            
        return value
    
    def write_memory_64(self, address: int, value: int) -> bool:
        if address < 0:
            return False

        if address % 8 != 0:
            return False
        
        if value < 0:
            value = (1 << 64) + value

        for i in range(8):
            byte_value = (value >> (i * 8)) & 0xFF
            if not self.write_byte(address + i, byte_value):
                return False
                
        return True
    
    def push_value(self, value: int, rsp: int) -> Optional[int]:
        new_rsp = rsp - 8
        if new_rsp < 0:
            return None
        
        if not self.write_memory_64(new_rsp, value):
            return None
        return new_rsp
    
    def pop_value(self, rsp: int) -> Optional[tuple]:
        if rsp < 0:
            return None
            
        value = self.read_memory_64(rsp)
        if value is None:
            return None
        new_rsp = rsp + 8
        return (value, new_rsp)
    
    def extract_immediate(self, start_address: int) -> Optional[int]:
        return self.read_memory_64(start_address)
    
    def get_nonzero_memory(self) -> MemoryMap:
        # 写穿透策略下，内存已经是同步的，不需要刷新
        
        nonzero_mem: MemoryMap = {}

        used_addresses = set(self.memory.keys())

        aligned_addresses = set()
        for addr in used_addresses:
            base_addr = addr & ~0x7
            aligned_addresses.add(base_addr)

        for base_addr in aligned_addresses:
            value = 0
            has_nonzero = False

            for i in range(8):
                addr = base_addr + i
                byte_value = self.memory.get(addr, 0)
                if byte_value != 0:
                    has_nonzero = True
                value |= (byte_value << (i * 8))

            if has_nonzero:
                if value & (1 << 63):
                    value = value - (1 << 64)
                nonzero_mem[base_addr] = value

        return dict(sorted(nonzero_mem.items()))
    
    def read_byte(self, address: int) -> Optional[int]:
        if address < 0:
            return None
        
        return self.cache.read_byte(address, self.memory)
    
    def write_byte(self, address: int, value: int) -> bool:
        if address < 0:
            return False
            
        if value < 0 or value > 255:
            return False

        return self.cache.write_byte(address, value, self.memory)
    
    def _check_address_bounds(self, address: int, size: int = 1) -> bool:
        if address < 0:
            return False
        return True
    
    def get_cache_stats(self) -> Dict[str, float]:
        return self.cache.get_stats()

    
    def get_memory_usage(self) -> Dict[str, int]:
        return {
            "total_bytes_allocated": len(self.memory),
            "min_address": min(self.memory.keys()) if self.memory else 0,
            "max_address": max(self.memory.keys()) if self.memory else 0,
        }
    
    def get_memory_dump(self, start_addr: int = 0, end_addr: int = 100) -> Dict[int, int]:
        result = {}
        for addr in range(start_addr, end_addr + 1):
            result[addr] = self.memory.get(addr, 0)
        return result