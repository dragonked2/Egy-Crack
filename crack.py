import os
import signal
import coincurve
from Crypto.Hash import keccak
import binascii
import time
import requests
from tqdm import tqdm
from colorama import init, Fore, Back, Style
from concurrent.futures import ThreadPoolExecutor
import random

init(autoreset=True)


class EthereumAddressGenerator:
    def __init__(self, start_index, ethereum_addresses, output_file_path, sequential_mode, discord_webhook):
        self.start_index = start_index
        self.ethereum_addresses = ethereum_addresses
        self.output_file_path = output_file_path
        self.discord_webhook = discord_webhook
        self.matched_addresses = 0
        self.progress_bar = None
        self.sequential_mode = sequential_mode
        self.last_generated_key = None

    def generate_ethereum_addresses(self):
        index = self.start_index
        increment = 1000000 if self.sequential_mode else 10000000000
        start_time = time.time()
        try:
            with ThreadPoolExecutor() as executor, \
                    tqdm(total=len(self.ethereum_addresses), unit=" address", ncols=80, unit_scale=True,
                         bar_format="{percentage:3.0f}%Total Generated Keys :/{total_fmt} | Elapsed:{elapsed}:Speed:{rate_fmt}") as pbar:
                self.progress_bar = pbar
                futures = []
                while self.matched_addresses < len(self.ethereum_addresses):
                    private_key = format(index, "064x")
                    future = executor.submit(self.check_ethereum_address, private_key)
                    futures.append(future)
                    index += increment
                    pbar.update(increment)
                    if self.sequential_mode:
                        self.last_generated_key = private_key

                # Wait for all futures to complete
                for future in futures:
                    future.result()

        except KeyboardInterrupt:
            elapsed_time = time.time() - start_time
            pbar.close()
            print(f"\n\n{Fore.GREEN}Script stopped by user. Elapsed time: {elapsed_time:.2f} seconds.")
            print("Press Enter to continue...")
            input()
            os.system('cls' if os.name == 'nt' else 'clear')
            self.display_interrupted_status(elapsed_time)

    def check_ethereum_address(self, private_key):
        ethereum_address = self.generate_ethereum_address(private_key)
        if ethereum_address and ethereum_address.lower() in [address.lower() for address in self.ethereum_addresses]:
            self.send_to_discord(private_key, ethereum_address)
            self.write_match_to_file(private_key, ethereum_address)
            self.display_match(private_key, ethereum_address)

    def generate_ethereum_address(self, private_key):
        try:
            private_key_bytes = bytes.fromhex(private_key)
            public_key = coincurve.PrivateKey(private_key_bytes).public_key
            public_key_bytes = public_key.format(compressed=False)
            keccak_hash = keccak.new(digest_bits=256)
            keccak_hash.update(public_key_bytes[1:])
            ethereum_address = "0x" + binascii.hexlify(keccak_hash.digest()[-20:]).decode()
            return ethereum_address
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred while generating the Ethereum address: {str(e)}")
            return None

    def write_match_to_file(self, private_key, ethereum_address):
        try:
            with open(self.output_file_path, "a") as output_file:
                output_file.write(f"PrivateKey: {private_key}\n")
                output_file.write(f"EthereumAddress: {ethereum_address}\n\n")
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred while writing the match to the output file: {str(e)}")

    def send_to_discord(self, private_key, ethereum_address):
        try:
            if self.discord_webhook:
                message = f"Match!:{private_key}:{ethereum_address}"
                payload = {"content": message}
                response = requests.post(self.discord_webhook, json=payload)
                if response.status_code == 204:
                    print(f"\n{Fore.GREEN}Match found! Sent to Discord.")
                else:
                    print(
                        f"\n{Fore.RED}An error occurred while sending the match to Discord. Status Code: {response.status_code}")
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred while sending the match to Discord: {str(e)}")

    def display_match(self, private_key, ethereum_address):
        self.matched_addresses += 1
        if self.progress_bar:
            self.progress_bar.set_postfix_str(
                f"Match found! Current Key: {self.last_generated_key}, Private Key: {private_key}, Ethereum Address: {ethereum_address}")

    def display_interrupted_status(self, elapsed_time):
        print(f"\n{Fore.GREEN}Script stopped by user. Elapsed time: {elapsed_time:.2f} seconds.")
        print("Press Enter to continue...")
        input()

    def exit_gracefully(self, signum, frame):
        if self.progress_bar:
            self.progress_bar.close()
        self.display_interrupted_status(0)


def display_logo():
    logo = """
██████╗ ██╗      █████╗ ██████╗ ██████╗ ██╗     ███████╗
██╔══██╗██║     ██╔══██╗██╔══██╗██╔══██╗██║     ██╔════╝
██║  ██║██║     ███████║██████╔╝██████╔╝██║     █████╗  
██║  ██║██║     ██╔══██║██╔═══╝ ██╔═══╝ ██║     ██╔══╝  
██████╔╝███████╗██║  ██║██║     ██║     ███████╗███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚══════╝
"""
    print(Fore.RED + Back.WHITE + Style.BRIGHT + logo)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def exit_gracefully(signum, frame):
    clear_screen()
    print(Fore.GREEN + "Script stopped by user.")
    exit()


def get_mode_choice():
    while True:
        choice = input("Select mode:\n1. Sequential\n2. Random\nEnter choice (1/2): ")
        if choice in ["1", "2"]:
            return choice


def main():
    try:
        clear_screen()
        display_logo()

        print(Fore.YELLOW + "Welcome to EgyCrack - Ethereum Address Generator")
        print(Fore.YELLOW + "Telegram: Egy-Crack\n")

        start_index = int(input("Enter the start index: "))

        ethereum_address_file = input("Enter the path to the file containing Ethereum addresses: ")
        output_file_path = input("Enter the path for the output file: ")

        discord_webhook = None
        if input("Do you want to enable Discord notifications? (y/n): ").lower() == "y":
            discord_webhook = input("Enter your Discord webhook URL: ")

        mode_choice = get_mode_choice()

        sequential_mode = True if mode_choice == "1" else False

        with open(ethereum_address_file, "r") as address_file:
            ethereum_addresses = [line.strip() for line in address_file]

        generator = EthereumAddressGenerator(start_index, ethereum_addresses, output_file_path, sequential_mode,
                                             discord_webhook)

        signal.signal(signal.SIGINT, generator.exit_gracefully)

        generator.generate_ethereum_addresses()

    except Exception as e:
        print(f"\n{Fore.RED}An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
