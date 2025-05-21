"""
This script is for educational and authorized testing only.
Unauthorized access to systems you do not own is illegal.

Author assumes no liability for any misuse or damage.
"""

import sys
import argparse
from pprint import pprint


def parse_args():
    parser = argparse.ArgumentParser(description="WP-EZ-Bruteforcer - Simple POC script to exploit unprotected wordpress website. EDUCATIONNAL PURPOSE ONLY")
    parser.add_argument('--i-agree', action='store_true', help='Confirm you are running at your own risk, are authorized to run this script and you do not plan to do illegal stuff.')
    parser.add_argument('--domain', type=str, help='Target domain (e.g. example.com)')

    args = parser.parse_args()

    if not args.i_agree:
        print("❌ You must add --i-agree to confirm you are authorized to test.")
        sys.exit(1)

    if not args.domain:
        print("❌ You must provide a --domain to scan.")
        sys.exit(1)

    return args





# Alias cuz FI
def die():
    sys.exit()


# Prepend the protocol to the domain if not already specified. HTTPS by default.
def normalize_domain(domain):
    if not domain.startswith("http://") and not domain.startswith("https://"):
        return "https://" + domain  # default to HTTPS
    return domain

# print for objects
def dump(var):
    pprint(vars(var))