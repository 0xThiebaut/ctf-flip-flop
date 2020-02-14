#!/usr/bin/env python

"""decode.py: A decoder for 0xThiebaut's 'Flip-Flop' challenge."""

import argparse
import json
import sys

import r2pipe

if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser(description='Decode 0xThiebaut\'s "Flip-Flop" challenge.')
    parser.add_argument('file', metavar='FILE', type=str,
                        help='The input "Flip-Flop" file.')
    parser.add_argument('breakpoint', metavar='ADDR', type=str, nargs='+',
                        help='The address of a flip or flop on which to break.')
    parser.add_argument('-o', '--output', metavar='FILE', type=str,
                        help='The output file used to save the extracted flag.')
    parser.add_argument('-c', '--count', metavar='N', type=int, default=128,
                        help='The chunk length used to optimise disk writes.')
    args = parser.parse_args()

    # Open the binary
    r2 = r2pipe.open(args.file)
    # Define all the breakpoints
    for bp in args.breakpoint:
        r2.cmd(f'db {bp}')
    # Reload the file for debugging
    r2.cmd('ood')

    # Check if we write to a file or stdout
    if hasattr(args, 'output') and args.output is not None:
        # Create a new file if it doesn't exist (x) in binary mode (b)
        output = open(args.output, 'xb')
    else:
        output = sys.stdout.buffer

    # Initialize our local variables
    count = 0
    byte = 0
    chunk = []

    # Loop the debugging
    while True:
        # Continue debugging until interruption
        r2.cmd('dc')
        # Get the debugged process' status
        target = json.loads(r2.cmd('dij'))
        # If the execution completed, break loop
        if 'type' in target and target['type'] == 'exit-pid':
            # Flush any incomplete byte
            if count > 0:
                chunk.append(byte)
            # Flush any incomplete chunk
            if len(chunk) > 0:
                output.write(bytes(chunk))
            break
        else:
            # Perform a single stop to trigger the flip or flop
            r2.cmd('ds')
            # Get the value of the "rflags" register.
            registers = json.loads(r2.cmd('drj'))
            rflags = registers['rflags']
            # Append the bit by left-shifting and or-ing.
            byte <<= 1
            byte |= int((rflags & 1) != 0)
            count += 1
            # If the byte is complete, flush
            if count == 8:
                chunk.append(byte)
                count = 0
                byte = 0
            # If the chunk is complete, flush
            if len(chunk) == args.count:
                output.write(bytes(chunk))
                chunk = []

    # Close our output
    output.close()
