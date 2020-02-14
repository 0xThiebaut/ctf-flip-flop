#!/usr/bin/env python

"""encode.py: An encoder for 0xThiebaut's 'Flip-Flop' challenge."""

import argparse
import math
import random
import sys


def split(i):
    """
    Split an number into two parts.

    :param int i: The number to split.
    :rtype: (int, int)
    """
    a = i // 2
    b = i - a
    return a, b


def explode(s, i):
    """
    Explode the number i into a tree such that each split part is added to the set s.

    explode(7) will extract the parts as follow...

    7 = (3+4) = ((1+2)+(2+2)) = ((1+(1+1))+((1+1)+(1+1)))

    ...and result in the set (7,3,4,1,2).

    :param set s: The set of parts.
    :param int i:  The number to explode into a tree.
    """
    s.add(i)
    if i > 1:
        a, b = split(i)
        explode(s, a)
        explode(s, b)


def complete(s):
    """
    Complete a set of numbers to ensure each number's tree is part of the set.

    :param set s: A set of numbers.
    """
    tree = set()
    for i in s:
        explode(tree, i)
    s.update(tree)


def call(op, times):
    """
    Generate a C function call.

    call('foo', 7) = 'foo7()'

    :param str op: The operation type.
    :param int times: The level of the tree to invoke.
    :return str: A C function call.
    """
    return f'{op}{times}()'


def function(op, times):
    """
    Generate a C function.

    :param str op: The operation type.
    :param int times: The level of the tree to invoke.
    :return str: A C function.
    """
    signature = call(op, times)
    if times > 1:
        a, b = split(times)
        acall = f'{call(op, a)};'
        bcall = f'{call(op, b)};'
        calls = [acall, bcall]
        if op != 'NOP':
            noise = f'{call("NOP", random.randint(1, 10))};'
            calls.append(noise)
        random.sample(calls, len(calls))
        body = '\r\n'.join([f'\t{c}' for c in calls])
    else:
        body = f'#ifdef DEBUG\r\n\tprintf("{op}");\r\n#endif\r\n\t__asm__("{op}");'
    return f'void {signature}{{\r\n{body}\r\n}}'


class Encoder:
    """
    Encoder generates the C code for the flip-flop challenge.
    """

    def __init__(self, input, bytes=1, noise=25):
        """
        Create a new encoder for the flip-flop challenge.

        :param BinaryIO input: The content to encode.
        :param int bytes: The number of bytes to read at once.
        :param int noise: A percentage of noise (0<noise<100).
        """
        # Configuration
        self.bytes = bytes
        self.noise = noise
        # Buffer info
        self.last = -1
        self.count = 0
        # Set of existing operations
        self.clcs = set()
        self.stcs = set()
        self.nops = set(range(1, 11))
        # List of calls to make
        self.calls = list()
        # Process the input
        bytes = input.read(self.bytes)
        while len(bytes) > 0:
            for byte in bytes:
                for i in range(8):
                    bit = (byte & (0b10000000 >> i)) >> (7 - i)
                    self.__add_bit(bit)
            bytes = input.read(self.bytes)
        self.flush()
        complete(self.clcs)
        complete(self.stcs)
        complete(self.nops)

    def __add_bit(self, bit):
        """
        Adds a bit to the C file.

        :param int bit: The bit to add.
        """
        if self.last == -1:
            self.last = bit
            self.count += 1
        elif self.last == bit:
            self.count += 1
        else:
            self.__add_bits(self.last, self.count)
            self.last = bit
            self.count = 1

    def __add_bits(self, bit, times):
        """
        Adds a bit multiple times to the C file.

        :param int bit: The bit to add.
        :param int times: The tree level.
        """
        if bit == 1:
            self.stcs.add(times)
            self.calls.append(call('STC', times))
        elif bit == 0:
            self.clcs.add(times)
            self.calls.append(call('CLC', times))

    def flush(self):
        """
        Flushed the buffer of pending bits.
        """
        self.__add_bits(self.last, self.count)
        self.last = -1
        self.count = 0

    def generate(self):
        """
        Generate the C code.
        :return str: The flip-flop challenge's C file.
        """
        # Generate functions and signatures
        signatures = set()
        funcs = set()
        for nop in self.nops:
            signatures.add(f'void {call("NOP", nop)};')
            funcs.add(function('NOP', nop))
        for clc in self.clcs:
            signatures.add(f'void {call("CLC", clc)};')
            funcs.add(function('CLC', clc))
        for stc in self.stcs:
            signatures.add(f'void {call("STC", stc)};')
            funcs.add(function('STC', stc))
        # Randomise the declaration order
        random.sample(signatures, len(signatures))
        declarations = '\r\n\r\n'.join(signatures)
        # Generate the main function's noise
        noisiness = len(self.calls) / 100 * self.noise
        noisiness = math.floor(noisiness)
        for _ in range(noisiness):
            times = random.randint(1, len(self.nops))
            index = random.randint(0, len(self.calls))
            self.calls.insert(index, call('NOP', times))
        # Generate the main function
        calls = '\r\n'.join([f'\t{c};' for c in self.calls])
        funcs.add(f'int main() {{\r\n\tprintf("Ready, Set, ");\r\n{calls}\r\n\tprintf("Done!\\r\\n");\r\n\treturn 0;\r\n}}')
        body = '\r\n\r\n'.join(funcs)
        # Randomise the functions
        random.sample(funcs, len(funcs))
        # Assemble the C file
        return f'#include <stdio.h>\r\n\r\n{declarations}\r\n\r\n{body}'


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Encode 0xThiebaut\'s "Flip-Flop" challenge.')
    parser.add_argument('-i', '--input', metavar='FILE', type=str,
                        help='The input file used as flag to insert.')
    parser.add_argument('-n', '--noise', metavar='N', type=int,
                        help='The noise percentage (0<N<100).', default=25)
    parser.add_argument('-o', '--output', metavar='FILE', type=str,
                        help='The output file used to save the "Flip-Flop" challenge\'s C source code.')
    args = parser.parse_args()

    # Check if we read from a file or stdin
    if hasattr(args, 'input') and args.input is not None and len(args.input) > 0:
        # Open the file in read-only (r) binary mode (b)
        input = open(args.input, 'rb')
    else:
        input = sys.stdin.buffer

    # Encode the file
    e = Encoder(input)

    # Check if we write to another file or stdout
    if hasattr(args, 'output') and args.output is not None and len(args.output) > 0:
        # Create a new file if it doesn't exist (x) in binary mode (b)
        output = open(args.output, 'xb')
    else:
        output = sys.stdout.buffer

    # Write the generated C file to the output and close it
    output.write(e.generate().encode())
    input.close()
    output.close()
