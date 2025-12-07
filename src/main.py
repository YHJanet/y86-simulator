#!/usr/bin/env python3
"""
主程序 - 同学C整合
负责程序的入口和整体控制流
"""
import sys
import json
from memory.memory_unit import MemoryUnit
from execution.execution_unit import ExecutionUnit
from control.control_unit import ControlUnit


def main() -> int:
    """主函数 - 同学C负责"""
    try:
        # 1. 初始化各单元
        memory = MemoryUnit()          
        execution = ExecutionUnit()    
        control = ControlUnit(memory, execution)  
        
        # 2. 从标准输入读取程序
        input_lines = sys.stdin.readlines()
        
        # 3. 加载程序
        if not control.load_program(input_lines):
            print("错误: 无法加载程序", file=sys.stderr)
            return 1
        
        # 4. 运行模拟器，收集所有状态
        execution_log = control.run_until_halt()
        
        # 5. 输出结果为JSON数组
        print(json.dumps(execution_log, indent=4))
            
        return 0
        
    except Exception as e:
        print(f"程序错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())