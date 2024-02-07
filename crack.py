from eth_account import Account
import signal
import os
from pybloom_live import BloomFilter

def load_target_addresses(file_path):
    target_addresses = BloomFilter(capacity=990000000, error_rate=0.001)

    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as file:
            for line in file:
                address = line.strip().lower()  # Convert to lowercase
                if address.startswith("0x"):
                    target_addresses.add(address[2:])  # Exclude "0x" prefix

    return target_addresses

def generate_ethereum_address(target_addresses=None, output_file_path=None):
    try:
        while True:
            # Generate a new Ethereum account
            account = Account.create()

            # Extract the address and private key
            address = account.address[2:].lower()  # Exclude "0x" prefix and convert to lowercase
            private_key = account._private_key.hex()

            print("Ethereum Address:", address)
            print("Private Key:", private_key)

            # Check for a match using the Bloom filter
            if target_addresses and address in target_addresses:
                print("Match found for target address. Saving results to file...")
                save_results_to_file(output_file_path, address, private_key)

            print()

    except KeyboardInterrupt:
        print("\nScript interrupted. Exiting gracefully.")

def save_results_to_file(output_file_path, address, private_key):
    with open(output_file_path, 'a') as results_file:
        results_file.write(f"Address: {address}, Private Key: {private_key}\n")

if __name__ == "__main__":
    target_addresses = load_target_addresses("address.txt")
    output_file_path = "match_results.txt"

    # Handle graceful termination on CTRL+C
    signal.signal(signal.SIGINT, lambda signal, frame: exit())

    generate_ethereum_address(target_addresses, output_file_path)
