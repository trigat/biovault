#!/usr/bin/python3

import os
import argparse
from threading import Thread
from itertools import cycle
from shutil import get_terminal_size
from time import sleep
import subprocess

# Author: Shain Lakin

pm3_path = "/Users/shain/Documents/tools/proxmark3/"
uid = "0478A5D2CD5280"
pre = '0' * 32

banner = """

"""


class Loader:
    def __init__(self, desc="Loading...", end="[+] Communicating with proxmark ... ", timeout=0.1):
        """
        A loader-like context manager

        Args:
            desc (str, optional): The loader's description. Defaults to "Loading...".
            end (str, optional): Final print. Defaults to "Done!...".
            timeout (float, optional): Sleep time between prints. Defaults to 0.1.
        """
        self.desc = desc
        self.end = end
        self.timeout = timeout

        self._thread = Thread(target=self._animate, daemon=True)
        self.steps = ["⢿", "⣻", "⣽", "⣾", "⣷", "⣯", "⣟", "⡿"]
        self.done = False

    def start(self):
        self._thread.start()
        return self

    def _animate(self):
        for c in cycle(self.steps):
            if self.done:
                break
            print(f"\r{self.desc} {c}", flush=True, end="")
            sleep(self.timeout)

    def __enter__(self):
        self.start()

    def stop(self):
        self.done = True
        cols = get_terminal_size((80, 20)).columns
        print("\r" + " " * cols, end="", flush=True)
        print(f"\r{self.end}", flush=True)

    def __exit__(self, exc_type, exc_value, tb):
        self.stop()


# Parse arguments
parser = argparse.ArgumentParser(description="", \
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-m", "--mode", type=str, default="r", help="Read/Write to vault")
parser.add_argument("-s", "--shred", action="store_true", help="Securely delete decrypted vault file")
parser.add_argument("-z", "--zero", action='store_true',  help="Zero sector with null bytes" )
args = parser.parse_args()

# Static strings
zero = f"{pm3_path}pm3 -c \'script run hf_i2c_plus_2k_utils -s 1 -m f -f zero.null\'"
aes_enc = f"openssl aes-256-cbc -salt -pbkdf2 -in vault.txt -out vault.txt.enc"
write_vault = f"{pm3_path}pm3 -c \'script run hf_i2c_plus_2k_utils -s 1 -m f -f vault.txt.enc\'"

dump_vault = f"{pm3_path}pm3 -c \'script run hf_i2c_plus_2k_utils -s 1 -m d\'" # >/dev/null 2>&1"
extract = f"/bin/cat {uid}.hex | awk -F \'{pre}\' \'{{print $2}}\' > dump.bin"
reverse_hex = "xxd -r -ps dump.bin > vault.txt.enc"
aes_dec = "openssl aes-256-cbc -d -pbkdf2 -in vault.txt.enc -out vault.txt.dec"
display = "csvtojson vault.txt.dec | jq"


# Process function
def proc(cmd):
    try:
        process = subprocess.Popen(f"{cmd}".split(), \
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()
    except KeyboardInterrupt:
        exit(0)


# Secure delete
def secure_delete(filename):
    try:
        subprocess.run(f"shred -u {filename}", shell=True, check=True)
    except Exception as e:
        print(f"[!] Failed to securely delete {filename}: {e}")


# Create null byte file
def zero_file():
    with open(f"zero.null", "w+b") as z:
        z.write(b"\0" * 3000)


# Delete files securely
def clean():
    if args.mode == 'w':
        secure_delete("vault.txt")
        secure_delete("vault.txt.enc")
        if args.zero:
            os.remove("zero.null")
    elif args.mode == 'r':
        os.remove(f"{uid}.hex")
        os.remove("dump.bin")
        secure_delete("vault.txt.enc")


# Loading function
def wait():
    loader = Loader("[+] Place proxmark on implant .. sleeping for 5").start()
    sleep(5)
    loader.stop()
    print("[+] Reading data ...")


def main():
    try:
        if args.shred:
            print("[+] Securely deleting decrypted vault file...")
            result = subprocess.run("shred -u vault.txt.dec", shell=True)
            if result.returncode == 0:
                print("[+] File shredded")
            return  # Exit after shredding
        if args.mode == 'r':
            tag_path = ("./" + uid + ".hex")
            wait()
            os.system(dump_vault)
            if os.path.exists(tag_path):
                os.system(extract)
                os.system(reverse_hex)
                proc(aes_dec)
                os.chmod("vault.txt.dec", 0o600)  # Read/write only for the owner
                print("[+] Decrypted file generated")
                clean()
            else:
                print("[!] Cannot read tag")
        elif args.mode == 'w':
            if args.zero:
                wait()
                zero_file()
                os.system(zero)
            proc(aes_enc)
            wait()
            # Run write_vault with error checking
            result = subprocess.run(write_vault, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:  # Check if an error occurred
                print(f"[-] Error: {result.stderr.decode().strip()}")
                print("[!] RFID chip might not be properly placed.")
                return  # Skip the clean() call and exit if there's an error
            clean()
    except Exception as e:
        print(e)
        exit(0)


main()
