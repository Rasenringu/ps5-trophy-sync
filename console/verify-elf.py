"""Inspect compiled startup hook; does not execute or send the ELF."""
import subprocess
import re
import sys
from pathlib import Path

elf = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'artifacts/console/final-ui/TrophySync.elf'
output = subprocess.check_output(['llvm-objdump-18', '-d', str(elf)], text=True)
hook = re.search(r'<__patch_init>:\n(.*?)(?=\n\n)', output, re.S)
assert hook, 'Read-only startup override is missing'
instructions = hook.group(1)
assert 'retq' in instructions and 'call' not in instructions and 'mov' not in instructions, instructions
assert re.search(r'callq.*<__patch_init>', output), 'CRT does not call the inspected override'
print('PASS: ELF startup __patch_init resolves to a no-write return hook')
print(instructions.strip())
