# Flip-Flop: A Single-Bit CTF in Intel-Based Status Registers

## Creating the Flip-Flop

```bash
# Generate a flag (txt, png, ...)
echo -n "{0xThiebaut_is_hiding_in_the_carry_flag}" > ./inflag.bin

# Generate the Flip-Flop's C code
python3 ./encode.py ./inflag.bin > ./flip-flop.c

# Compile the C code with stripped function names
gcc -s ./flip-flop.c -o ./flip-flop

# And optionnaly make it executable
chmod +x ./flip-flop
```

## Solving the Flip-Flop

One way to solve the challenge is by using Cutter and Radare2.  
Using cutter, identify the `CLC` and `STC` operations nested in the Flip-Flop's main function. Assuming these are located at `0x123` and `0xabc`, proceed as follow.

```bash
# Create a virtual environment
python3 -m venv venv
source ./venv/bin/activate

# Install the Radare2 binding
pip install -r requirements.txt

# Launch the decoding script, and grab a coffee
python3 decode.py ./flip-flop 0x123 0xabc > ./outflag.bin
```
