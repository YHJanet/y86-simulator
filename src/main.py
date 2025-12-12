#!/usr/bin/env python3
import sys
import json
from memory.memory_unit import MemoryUnit
from execution.execution_unit import ExecutionUnit
from control.control_unit import ControlUnit


def main() -> int:
    try:
        memory = MemoryUnit()          
        execution = ExecutionUnit()    
        control = ControlUnit(memory, execution)  
        
        input_lines = sys.stdin.readlines()
        
        if not control.load_program(input_lines):
            print("错误: 无法加载程序", file=sys.stderr)
            return 1
        
        execution_log = control.run_until_halt()
        
        print(json.dumps(execution_log, indent=4))
            
        return 0
        
    except Exception as e:
        print(f"程序错误: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())