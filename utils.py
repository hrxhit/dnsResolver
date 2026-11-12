"""
Utility Functions
==================
Logging, formatting, and helper functions for the DNS Resolver.

Author: Sarah
Subject: Computer Networks (2nd Year)
"""

import time
import logging
import sys

# ============================================================
# ANSI Color Codes for Terminal Output
# ============================================================
class Colors:
    """ANSI escape codes for colorful terminal output"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    
    # Regular colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'


def colorize(text, color):
    """Wrap text with ANSI color codes"""
    return f"{color}{text}{Colors.RESET}"


def bold(text):
    return colorize(text, Colors.BOLD)


def success(text):
    return colorize(text, Colors.GREEN)


def error(text):
    return colorize(text, Colors.RED)


def warning(text):
    return colorize(text, Colors.YELLOW)


def info(text):
    return colorize(text, Colors.CYAN)


def dim(text):
    return colorize(text, Colors.GRAY)


# ============================================================
# Banner
# ============================================================

BANNER = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║       ██████╗ ███╗   ██╗███████╗                        ║
║       ██╔══██╗████╗  ██║██╔════╝                        ║
║       ██║  ██║██╔██╗ ██║███████╗                        ║
║       ██║  ██║██║╚██╗██║╚════██║                        ║
║       ██████╔╝██║ ╚████║███████║                        ║
║       ╚═════╝ ╚═╝  ╚═══╝╚══════╝                        ║
║                                                          ║
║           🔍  DNS Resolver v1.0                          ║
║           Computer Networks Project                      ║
║           By: Sarah                                      ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
{Colors.RESET}"""


# ============================================================
# Logging Setup
# ============================================================

def setup_logger(name='dns_resolver', level=logging.INFO, verbose=False):
    """
    Set up a formatted logger.
    
    Args:
        name: Logger name
        level: Logging level
        verbose: If True, set to DEBUG
    
    Returns:
        logging.Logger instance
    """
    if verbose:
        level = logging.DEBUG
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler with custom formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        f'{Colors.GRAY}%(asctime)s{Colors.RESET} '
        f'[%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# ============================================================
# Timer Utility
# ============================================================

class Timer:
    """Context manager to measure execution time"""
    
    def __init__(self, label="Operation"):
        self.label = label
        self.start_time = None
        self.elapsed_ms = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
    
    @property
    def elapsed_str(self):
        if self.elapsed_ms is None:
            return "N/A"
        if self.elapsed_ms < 1:
            return f"{self.elapsed_ms * 1000:.0f}µs"
        elif self.elapsed_ms < 1000:
            return f"{self.elapsed_ms:.1f}ms"
        else:
            return f"{self.elapsed_ms / 1000:.2f}s"


# ============================================================
# Formatting Helpers
# ============================================================

def format_record_type(rtype_name):
    """Color-code record types for display"""
    colors = {
        'A': Colors.GREEN,
        'AAAA': Colors.BLUE,
        'MX': Colors.MAGENTA,
        'NS': Colors.YELLOW,
        'CNAME': Colors.CYAN,
        'TXT': Colors.WHITE,
        'SOA': Colors.RED,
    }
    color = colors.get(rtype_name, Colors.WHITE)
    return f"{color}{rtype_name:6s}{Colors.RESET}"


def format_ttl(ttl):
    """Format TTL value with units"""
    if ttl < 60:
        return f"{ttl}s"
    elif ttl < 3600:
        return f"{ttl // 60}m {ttl % 60}s"
    elif ttl < 86400:
        hours = ttl // 3600
        mins = (ttl % 3600) // 60
        return f"{hours}h {mins}m"
    else:
        days = ttl // 86400
        hours = (ttl % 86400) // 3600
        return f"{days}d {hours}h"


def print_separator(char='─', length=60):
    """Print a separator line"""
    print(dim(char * length))


def format_table_row(columns, widths):
    """Format a row with fixed-width columns"""
    parts = []
    for col, width in zip(columns, widths):
        parts.append(str(col).ljust(width))
    return '  '.join(parts)


# ============================================================
# Root DNS Servers
# ============================================================

# The 13 root DNS servers that form the backbone of the DNS system.
# Every iterative DNS resolution starts by querying one of these.
ROOT_SERVERS = [
    ('a.root-servers.net', '198.41.0.4'),
    ('b.root-servers.net', '170.247.170.2'),
    ('c.root-servers.net', '192.33.4.12'),
    ('d.root-servers.net', '199.7.91.13'),
    ('e.root-servers.net', '192.203.230.10'),
    ('f.root-servers.net', '192.5.5.241'),
    ('g.root-servers.net', '192.112.36.4'),
    ('h.root-servers.net', '198.97.190.53'),
    ('i.root-servers.net', '192.36.148.17'),
    ('j.root-servers.net', '192.58.128.30'),
    ('k.root-servers.net', '193.0.14.129'),
    ('l.root-servers.net', '199.7.83.42'),
    ('m.root-servers.net', '202.12.27.33'),
]

# Default public DNS servers for recursive resolution
PUBLIC_DNS_SERVERS = {
    'Google': '8.8.8.8',
    'Google Secondary': '8.8.4.4',
    'Cloudflare': '1.1.1.1',
    'Cloudflare Secondary': '1.0.0.1',
    'OpenDNS': '208.67.222.222',
    'Quad9': '9.9.9.9',
}


if __name__ == '__main__':
    print(BANNER)
    print(bold("Testing utilities..."))
    print(success("✓ Success message"))
    print(error("✗ Error message"))
    print(warning("⚠ Warning message"))
    print(info("ℹ Info message"))
    print()
    
    with Timer("Test") as t:
        time.sleep(0.05)
    print(f"Timer: {t.elapsed_str}")
    
    print(f"\nRoot Servers: {len(ROOT_SERVERS)}")
    for name, ip in ROOT_SERVERS[:3]:
        print(f"  {name} → {ip}")

