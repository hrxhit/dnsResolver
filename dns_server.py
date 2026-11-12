"""
Local DNS Server
==================
A DNS server that listens on port 5353 and uses our resolver to answer queries.

This demonstrates the Server-side of the Client-Server model in DNS.
Real DNS servers listen on port 53 — we use 5353 to avoid needing root privileges.

How it works:
1. Server binds to UDP port 5353
2. Client sends a DNS query packet
3. Server parses the query
4. Server resolves the domain using our resolver
5. Server builds a response packet and sends it back

You can test it with:
    dig @127.0.0.1 -p 5353 google.com

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

import socket
import struct
import threading
import signal
import sys
import time

from dns_packet import (
    build_query, parse_response, encode_domain_name,
    DNSHeader, DNSQuestion, DNSRecord, DNSPacket,
    RECORD_TYPES, CLASS_IN
)
from dns_resolver import DNSResolver
from dns_cache import DNSCache
from utils import (
    setup_logger, bold, success, error, warning, info, dim,
    Colors, Timer, print_separator
)

# Server configuration
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 5353  # Non-privileged port (real DNS uses 53)
BUFFER_SIZE = 4096


def build_response_packet(query_data, answers, authority=None, additional=None):
    """
    Build a DNS response packet from the original query.
    
    Response packet reuses the query's ID and Question section,
    adds our answer records, and sets appropriate flags.
    
    Args:
        query_data: Original query bytes (to extract ID and Question)
        answers: List of DNSRecord objects
        authority: List of authority DNSRecord objects
        additional: List of additional DNSRecord objects
    
    Returns:
        bytes — Complete DNS response packet
    """
    authority = authority or []
    additional = additional or []
    
    # Parse original query header
    original_header = DNSHeader.from_bytes(query_data)
    
    # Build response header
    # Flags: QR=1 (response), RD=1 (recursion desired), RA=1 (recursion available)
    flags = 0x8180  # Standard response, recursion available
    
    if not answers:
        # NXDOMAIN if no answers
        flags = 0x8183  # QR=1, RD=1, RA=1, RCODE=3
    
    response_header = DNSHeader(
        id=original_header.id,
        flags=flags,
        qd_count=original_header.qd_count,
        an_count=len(answers),
        ns_count=len(authority),
        ar_count=len(additional),
    )
    
    # Start building response
    response = response_header.to_bytes()
    
    # Copy question section from query (skip header = 12 bytes)
    # Parse question to find its end
    offset = 12
    for _ in range(original_header.qd_count):
        # Skip QNAME
        while offset < len(query_data):
            length = query_data[offset]
            if length == 0:
                offset += 1
                break
            if (length & 0xC0) == 0xC0:
                offset += 2
                break
            offset += 1 + length
        # Skip QTYPE + QCLASS
        offset += 4
    
    # Add question section from original query
    response += query_data[12:offset]
    
    # Add answer records
    for record in answers:
        response += _encode_record(record)
    
    # Add authority records
    for record in authority:
        response += _encode_record(record)
    
    # Add additional records
    for record in additional:
        response += _encode_record(record)
    
    return response


def _encode_record(record):
    """Encode a DNSRecord into wire format"""
    encoded = encode_domain_name(record.name)
    encoded += struct.pack('!HHI', record.rtype, record.rclass, record.ttl)
    
    # Encode RDATA based on type
    if record.rtype == RECORD_TYPES.get('A', 1) and record.rdata:
        # A record: IP address → 4 bytes
        parts = record.rdata.split('.')
        rdata = bytes(int(p) for p in parts)
    elif record.rtype == RECORD_TYPES.get('AAAA', 28) and record.rdata:
        # AAAA: IPv6 → 16 bytes
        parts = record.rdata.split(':')
        rdata = b''.join(int(p, 16).to_bytes(2, 'big') for p in parts)
    elif record.rtype in (RECORD_TYPES.get('NS', 2), RECORD_TYPES.get('CNAME', 5)):
        # NS/CNAME: domain name
        rdata = encode_domain_name(record.rdata) if record.rdata else record.rdata_raw
    elif record.rtype == RECORD_TYPES.get('MX', 15) and record.rdata:
        # MX: preference + domain
        parts = record.rdata.split(' ', 1)
        preference = int(parts[0])
        exchange = parts[1] if len(parts) > 1 else ''
        rdata = struct.pack('!H', preference) + encode_domain_name(exchange)
    elif record.rtype == RECORD_TYPES.get('TXT', 16) and record.rdata:
        # TXT: length-prefixed string
        txt_bytes = record.rdata.encode('utf-8')
        rdata = bytes([len(txt_bytes)]) + txt_bytes
    else:
        rdata = record.rdata_raw if record.rdata_raw else b''
    
    encoded += struct.pack('!H', len(rdata))
    encoded += rdata
    
    return encoded


class DNSServer:
    """
    Local DNS Server using UDP.
    
    Demonstrates:
    - Socket programming (UDP server)
    - Client-Server architecture
    - DNS message handling
    - Multi-threaded request handling
    """
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT, verbose=False):
        self.host = host
        self.port = port
        self.verbose = verbose
        self.logger = setup_logger('dns_server', verbose=verbose)
        self.resolver = DNSResolver(verbose=verbose)
        self.running = False
        self.sock = None
        self.query_count = 0
        self.start_time = None
    
    def start(self):
        """Start the DNS server"""
        # Create UDP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind((self.host, self.port))
        except OSError as e:
            print(error(f"Cannot bind to {self.host}:{self.port} — {e}"))
            sys.exit(1)
        
        self.running = True
        self.start_time = time.time()
        
        print(f"\n{bold('🖥️  DNS Server Started')}")
        print_separator('═', 50)
        print(f"  {dim('Listening on:')} {info(f'{self.host}:{self.port}')}")
        print(f"  {dim('Protocol:')}     UDP")
        print(f"  {dim('Resolver:')}     Iterative + Cache")
        print_separator('═', 50)
        print(f"\n{dim('Test with:')} dig @{self.host} -p {self.port} google.com")
        print(f"{dim('Press Ctrl+C to stop')}\n")
        
        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Main server loop
        while self.running:
            try:
                self.sock.settimeout(1.0)
                data, client_addr = self.sock.recvfrom(BUFFER_SIZE)
                
                # Handle query in a new thread
                thread = threading.Thread(
                    target=self._handle_query,
                    args=(data, client_addr),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.logger.error(f"Server error: {e}")
    
    def _handle_query(self, data, client_addr):
        """Handle a single DNS query"""
        self.query_count += 1
        query_num = self.query_count
        
        try:
            with Timer("Query") as timer:
                # Parse the incoming query
                query = parse_response(data)  # Same format for queries
                
                if not query.questions:
                    return
                
                question = query.questions[0]
                domain = question.name
                qtype = question.qtype_name
                
                self.logger.info(
                    f"[{query_num}] {Colors.CYAN}{client_addr[0]}:{client_addr[1]}{Colors.RESET} "
                    f"→ {bold(domain)} {format_type_colored(qtype)}"
                )
                
                # Resolve the query
                result = self.resolver.resolve(domain, qtype, mode='iterative')
                
                # Build response
                response_data = build_response_packet(
                    data, result.answers, result.authority, result.additional
                )
                
                # Send response back to client
                self.sock.sendto(response_data, client_addr)
            
            # Log result
            cached = f" {Colors.GREEN}[CACHE]{Colors.RESET}" if result.from_cache else ""
            answer_count = len(result.answers)
            
            self.logger.info(
                f"[{query_num}] ← {answer_count} answers, "
                f"{timer.elapsed_str}{cached}"
            )
            
        except Exception as e:
            self.logger.error(f"[{query_num}] Error handling query: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print(f"\n\n{warning('Shutting down...')}")
        self.running = False
        
        uptime = time.time() - self.start_time if self.start_time else 0
        
        print(f"\n{bold('📊 Server Statistics')}")
        print_separator('─', 40)
        print(f"  Queries handled:  {self.query_count}")
        print(f"  Uptime:           {int(uptime)}s")
        print(f"  Cache: {self.resolver.cache}")
        print_separator('─', 40)
        
        if self.sock:
            self.sock.close()
        sys.exit(0)


def format_type_colored(qtype):
    """Color-code record types"""
    colors = {
        'A': Colors.GREEN,
        'AAAA': Colors.BLUE,
        'MX': Colors.MAGENTA,
        'NS': Colors.YELLOW,
        'CNAME': Colors.CYAN,
        'TXT': Colors.WHITE,
    }
    color = colors.get(qtype, Colors.WHITE)
    return f"{color}{qtype}{Colors.RESET}"


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='🖥️ Local DNS Server')
    parser.add_argument('--host', default=DEFAULT_HOST, help='Host to bind to')
    parser.add_argument('--port', '-p', type=int, default=DEFAULT_PORT, help='Port to listen on')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    server = DNSServer(host=args.host, port=args.port, verbose=args.verbose)
    server.start()


if __name__ == '__main__':
    main()

