from eth_account import Account
import os
import sys
from secrets import token_bytes
from tqdm import tqdm
import math

def generate_ethereum_wallet(existing_addresses):
    while True:
        private_key = token_bytes(32).hex()
        account = Account.from_key(private_key)
        address = account.address.lower()[2:]
        if address not in existing_addresses:
            existing_addresses.add(address)
            return address, private_key

def load_addresses(filename="first_half1.txt"):
    addresses_set = set()
    try:
        print(f"Loading addresses from {filename}...")
        with open(filename, "r", encoding="latin-1") as file:
            addresses_set.update(line.strip().lower() for line in file)
    except (UnicodeDecodeError, FileNotFoundError) as e:
        print(f"Error loading addresses from {filename}: {e}")
        sys.exit(1)
    return addresses_set

def check_and_save_match(formatted_address, private_key, output_filename="matches.txt"):
    with open(output_filename, "a", encoding="utf-8") as output_file:
        output_file.write(f"Match Found\n"
                          f"  Address: {formatted_address}\n"
                          f"  Private Key: {private_key}\n\n")

def generate_and_check_addresses(args, max_matches=10):
    addresses_set, existing_addresses = args
    matches_found = 0
    try:
        with tqdm(desc="Processing", unit=" address", ncols=100, dynamic_ncols=True) as progress_bar:
            speed_multiplier = math.sqrt(len(addresses_set))  # Adjust speed based on the number of loaded addresses
            while matches_found < max_matches:
                formatted_address, private_key = generate_ethereum_wallet(existing_addresses)

                # Add additional actions if needed
                if formatted_address in addresses_set:
                    check_and_save_match(formatted_address, private_key)
                    matches_found += 1

                progress_bar.update(speed_multiplier)  # Update progress bar with adjusted speed

    except KeyboardInterrupt:
        print("\nScript stopped by the user.")
        sys.exit(0)

def main():
    addresses_set = load_addresses()
    if not addresses_set:
        print("No addresses loaded. Exiting.")
        sys.exit(1)

    print(f"Loaded {len(addresses_set)} addresses from the file.")

    try:
        existing_addresses = set()
        args = (addresses_set, existing_addresses)
        generate_and_check_addresses(args)

    except KeyboardInterrupt:
        print("\nScript stopped by the user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
