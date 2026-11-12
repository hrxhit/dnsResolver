"""
DNS Resolver Engine
====================
The core resolver that performs DNS resolution using raw UDP sockets.

Supports two modes of resolution:
1. Iterative Resolution — queries Root → TLD → Authoritative step by step
2. Recursive Resolution — sends a single query to a public DNS server

Transport Layer: Uses UDP (port 53) for DNS queries.
    - UDP is connectionless → faster, less overhead
    - DNS messages are typically < 512 bytes → fit in single UDP datagram
    - If response is truncated (TC flag), can fall back to TCP

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

import socket
import time
import random

from dns_packet import (
    build_query, parse_response, DNSPacket,
    RECORD_TYPES, RECORD_TYPE_NAMES
)
from dns_cache import DNSCache
from utils import (
    setup_logger, Timer, Colors, colorize,
    ROOT_SERVERS, PUBLIC_DNS_SERVERS,
    bold, success, warning, error, info, dim
)

# DNS port number (well-known port)
DNS_PORT = 53

# Default timeout for DNS queries (seconds)
DEFAULT_TIMEOUT = 5

# Maximum number of resolution steps (prevent infinite loops)
MAX_ITERATIONS = 30


class ResolutionStep:
    """Records a single step in the resolution process for tracing"""
    
    def __init__(self, server_ip, server_name, query_domain, query_type, 
                 response=None, elapsed_ms=0, from_cache=False):
        self.server_ip = server_ip
        self.server_name = server_name
        self.query_domain = query_domain
        self.query_type = query_type
        self.response = response
        self.elapsed_ms = elapsed_ms
        self.from_cache = from_cache
    
    def __repr__(self):
        src = "CACHE" if self.from_cache else self.server_ip
        return f"Step({self.query_domain} {self.query_type} → {src}, {self.elapsed_ms:.1f}ms)"


class ResolutionResult:
    """Complete result of a DNS resolution"""
    
    def __init__(self):
        self.domain = ""
        self.query_type = ""
        self.answers = []          # Final answer records
        self.authority = []        # Authority records
        self.additional = []       # Additional records
        self.steps = []            # Resolution trace
        self.total_time_ms = 0     # Total resolution time
        self.from_cache = False    # Whether result came from cache
        self.rcode = 0             # Response code
        self.rcode_name = "NOERROR"
        self.error = None          # Error message if failed
    
    @property
    def success(self):
        return self.error is None and self.rcode == 0


class DNSResolver:
    """
    DNS Resolver — performs domain name resolution.
    
    Resolution Flow (Iterative):
    ┌──────────┐     ┌──────────────┐     ┌─────────────┐     ┌───────────────┐
    │  Client  │────▶│ Root Server  │────▶│ TLD Server  │────▶│ Authoritative │
    │          │     │ (knows TLDs) │     │ (knows auth)│     │  (has answer) │
    │          │◀────│              │◀────│             │◀────│               │
    └──────────┘     └──────────────┘     └─────────────┘     └───────────────┘
        Query            Referral           Referral              Answer
    
    Resolution Flow (Recursive):
    ┌──────────┐     ┌──────────────┐
    │  Client  │────▶│ Public DNS   │  (e.g., 8.8.8.8)
    │          │◀────│ (does all    │  Handles the entire
    └──────────┘     │  the work)   │  resolution chain
                     └──────────────┘
    """
    
    def __init__(self, cache=None, timeout=DEFAULT_TIMEOUT, verbose=False):
        self.cache = cache or DNSCache()
        self.timeout = timeout
        self.verbose = verbose
        self.logger = setup_logger('resolver', verbose=verbose)
    
    def query_server(self, server_ip, domain, qtype='A', timeout=None):
        """
        Send a DNS query to a specific server using UDP socket.
        
        This is the core networking function that:
        1. Creates a UDP socket
        2. Builds a DNS query packet
        3. Sends it to the DNS server on port 53
        4. Receives and parses the response
        
        Args:
            server_ip: IP address of DNS server
            domain: Domain name to query
            qtype: Record type ('A', 'AAAA', 'MX', etc.)
            timeout: Query timeout in seconds
        
        Returns:
            (DNSPacket, elapsed_ms) or (None, elapsed_ms) on failure
        """
        timeout = timeout or self.timeout
        
        # Build the query packet
        packet_bytes, txn_id = build_query(domain, qtype, recursion_desired=False)
        
        # Create UDP socket
        # AF_INET = IPv4, SOCK_DGRAM = UDP (datagram socket)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        try:
            start = time.perf_counter()
            
            # Send query to DNS server on port 53
            sock.sendto(packet_bytes, (server_ip, DNS_PORT))
            
            # Receive response (max 4096 bytes)
            data, addr = sock.recvfrom(4096)
            
            elapsed_ms = (time.perf_counter() - start) * 1000
            
            # Parse the response
            response = parse_response(data)
            
            # Verify transaction ID matches
            if response.header.id != txn_id:
                self.logger.warning(f"Transaction ID mismatch! Expected {txn_id}, got {response.header.id}")
                return None, elapsed_ms
            
            return response, elapsed_ms
            
        except socket.timeout:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.logger.warning(f"Timeout querying {server_ip} for {domain}")
            return None, elapsed_ms
            
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000 if 'start' in locals() else 0
            self.logger.error(f"Error querying {server_ip}: {e}")
            return None, elapsed_ms
            
        finally:
            sock.close()
    
    def resolve_iterative(self, domain, qtype='A'):
        """
        Perform iterative DNS resolution.
        
        How it works:
        1. Start with a random root server
        2. Query it → get referral to TLD server
        3. Query TLD server → get referral to authoritative server
        4. Query authoritative → get the final answer
        5. Follow CNAME chains if needed
        
        This mimics how a real DNS resolver works — we manually
        walk down the DNS hierarchy tree.
        
        Args:
            domain: Domain to resolve
            qtype: Record type
        
        Returns:
            ResolutionResult with answers and trace
        """
        result = ResolutionResult()
        result.domain = domain
        result.query_type = qtype
        
        total_timer = Timer("Total Resolution")
        total_timer.__enter__()
        
        # Check cache first
        cached = self.cache.get(domain, qtype)
        if cached:
            result.answers = cached
            result.from_cache = True
            result.steps.append(ResolutionStep(
                'cache', 'Local Cache', domain, qtype, from_cache=True
            ))
            total_timer.__exit__(None, None, None)
            result.total_time_ms = total_timer.elapsed_ms
            self.logger.info(f"Cache hit for {domain} {qtype}")
            return result
        
        # Start with a random root server
        root_name, root_ip = random.choice(ROOT_SERVERS)
        current_servers = [(root_name, root_ip)]
        
        iterations = 0
        current_domain = domain
        
        while iterations < MAX_ITERATIONS:
            iterations += 1
            
            # Try each server in the current list
            response = None
            step = None
            
            for server_name, server_ip in current_servers:
                self.logger.debug(f"Querying {server_name} ({server_ip}) for {current_domain} {qtype}")
                
                resp, elapsed = self.query_server(server_ip, current_domain, qtype)
                
                step = ResolutionStep(
                    server_ip, server_name, current_domain, qtype,
                    response=resp, elapsed_ms=elapsed
                )
                result.steps.append(step)
                
                if resp:
                    response = resp
                    break
            
            if response is None:
                result.error = f"All servers failed for {current_domain}"
                break
            
            # Check response code
            if response.header.rcode != 0:
                result.rcode = response.header.rcode
                result.rcode_name = response.header.rcode_name
                if response.header.rcode == 3:  # NXDOMAIN
                    result.error = f"Domain not found (NXDOMAIN): {current_domain}"
                else:
                    result.error = f"Server error: {response.header.rcode_name}"
                break
            
            # Case 1: We got answers!
            if response.answers:
                # Check for CNAME — need to follow the chain
                cname_records = [r for r in response.answers if r.rtype == RECORD_TYPES.get('CNAME', 5)]
                target_records = [r for r in response.answers if r.rtype == RECORD_TYPES.get(qtype, 0)]
                
                if target_records:
                    # Got the actual answer
                    result.answers = response.answers
                    result.authority = response.authority
                    result.additional = response.additional
                    
                    # Cache the result
                    self.cache.put(domain, qtype, target_records)
                    break
                
                elif cname_records:
                    # Follow CNAME chain
                    result.answers.extend(cname_records)
                    cname_target = cname_records[0].rdata
                    self.logger.info(f"Following CNAME: {current_domain} → {cname_target}")
                    current_domain = cname_target
                    # Reset to root servers for CNAME target
                    root_name, root_ip = random.choice(ROOT_SERVERS)
                    current_servers = [(root_name, root_ip)]
                    continue
                
                else:
                    # Got answers but not the type we want
                    result.answers = response.answers
                    break
            
            # Case 2: Got referral (authority section has NS records)
            if response.authority:
                ns_records = [r for r in response.authority if r.rtype == RECORD_TYPES.get('NS', 2)]
                
                if ns_records:
                    # Build list of servers to query next
                    next_servers = []
                    
                    # First, try to find IPs in additional section (glue records)
                    additional_ips = {}
                    for r in response.additional:
                        if r.rtype == RECORD_TYPES.get('A', 1):
                            additional_ips[r.name.lower()] = r.rdata
                    
                    for ns in ns_records:
                        ns_name = ns.rdata
                        if ns_name and ns_name.lower() in additional_ips:
                            next_servers.append((ns_name, additional_ips[ns_name.lower()]))
                        elif ns_name:
                            # Need to resolve NS name — use recursive query to public DNS
                            ns_ip = self._resolve_ns_ip(ns_name)
                            if ns_ip:
                                next_servers.append((ns_name, ns_ip))
                    
                    if next_servers:
                        current_servers = next_servers
                        continue
                
                # No useful referral
                result.authority = response.authority
                result.additional = response.additional
                break
            
            # Case 3: Empty response
            result.error = f"Empty response from {current_servers[0][0]}"
            break
        
        if iterations >= MAX_ITERATIONS:
            result.error = "Maximum iterations reached"
        
        total_timer.__exit__(None, None, None)
        result.total_time_ms = total_timer.elapsed_ms
        
        return result
    
    def _resolve_ns_ip(self, ns_name):
        """
        Helper: resolve an NS server's IP using a public DNS server.
        Used when glue records are not provided in the referral.
        """
        try:
            packet_bytes, txn_id = build_query(ns_name, 'A', recursion_desired=True)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            # Use Google DNS for this helper query
            sock.sendto(packet_bytes, ('8.8.8.8', DNS_PORT))
            data, _ = sock.recvfrom(4096)
            sock.close()
            
            response = parse_response(data)
            for answer in response.answers:
                if answer.rtype == 1:  # A record
                    return answer.rdata
        except Exception:
            pass
        return None
    
    def resolve_recursive(self, domain, qtype='A', dns_server=None):
        """
        Perform recursive DNS resolution via a public DNS server.
        
        How it works:
        1. Send query to public DNS (e.g., 8.8.8.8) with RD flag set
        2. The public DNS does all the work (root → TLD → auth)
        3. We get back the final answer in one response
        
        This is simpler but relies on the public DNS server to
        perform the iterative resolution on our behalf.
        
        Args:
            domain: Domain to resolve
            qtype: Record type
            dns_server: DNS server IP (default: Google 8.8.8.8)
        
        Returns:
            ResolutionResult
        """
        result = ResolutionResult()
        result.domain = domain
        result.query_type = qtype
        
        total_timer = Timer("Recursive Resolution")
        total_timer.__enter__()
        
        # Check cache first
        cached = self.cache.get(domain, qtype)
        if cached:
            result.answers = cached
            result.from_cache = True
            result.steps.append(ResolutionStep(
                'cache', 'Local Cache', domain, qtype, from_cache=True
            ))
            total_timer.__exit__(None, None, None)
            result.total_time_ms = total_timer.elapsed_ms
            return result
        
        # Use provided server or default
        server_ip = dns_server or PUBLIC_DNS_SERVERS['Google']
        server_name = next(
            (name for name, ip in PUBLIC_DNS_SERVERS.items() if ip == server_ip),
            server_ip
        )
        
        # Build query with Recursion Desired (RD) flag
        packet_bytes, txn_id = build_query(domain, qtype, recursion_desired=True)
        
        # Create UDP socket and send
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.timeout)
        
        try:
            start = time.perf_counter()
            sock.sendto(packet_bytes, (server_ip, DNS_PORT))
            data, _ = sock.recvfrom(4096)
            elapsed = (time.perf_counter() - start) * 1000
            
            response = parse_response(data)
            
            step = ResolutionStep(
                server_ip, server_name, domain, qtype,
                response=response, elapsed_ms=elapsed
            )
            result.steps.append(step)
            
            result.answers = response.answers
            result.authority = response.authority
            result.additional = response.additional
            result.rcode = response.header.rcode
            result.rcode_name = response.header.rcode_name
            
            if response.header.rcode != 0:
                result.error = f"Server returned: {response.header.rcode_name}"
            
            # Cache successful results
            if result.success and result.answers:
                self.cache.put(domain, qtype, result.answers)
                
        except socket.timeout:
            result.error = f"Timeout querying {server_ip}"
            elapsed = (time.perf_counter() - start) * 1000
            result.steps.append(ResolutionStep(
                server_ip, server_name, domain, qtype, elapsed_ms=elapsed
            ))
        except Exception as e:
            result.error = str(e)
        finally:
            sock.close()
        
        total_timer.__exit__(None, None, None)
        result.total_time_ms = total_timer.elapsed_ms
        
        return result
    
    def resolve(self, domain, qtype='A', mode='iterative'):
        """
        Main resolve method — delegates to iterative or recursive.
        
        Args:
            domain: Domain to resolve
            qtype: Record type ('A', 'AAAA', 'MX', 'NS', 'CNAME', 'TXT')
            mode: 'iterative' or 'recursive'
        
        Returns:
            ResolutionResult
        """
        domain = domain.strip().rstrip('.')
        qtype = qtype.upper()
        
        if mode == 'iterative':
            return self.resolve_iterative(domain, qtype)
        elif mode == 'recursive':
            return self.resolve_recursive(domain, qtype)
        else:
            raise ValueError(f"Unknown mode: {mode}. Use 'iterative' or 'recursive'.")
    
    def compare_with_system(self, domain, qtype='A'):
        """
        Compare our resolver's performance with the system's DNS.
        
        Uses Python's socket.getaddrinfo() as the "system DNS" baseline
        and compares timing with our iterative and recursive modes.
        
        Returns:
            dict with comparison results
        """
        results = {}
        
        # Our iterative resolution
        with Timer("Iterative") as t1:
            iter_result = self.resolve(domain, qtype, mode='iterative')
        results['iterative'] = {
            'time_ms': t1.elapsed_ms,
            'answers': [r.rdata for r in iter_result.answers if hasattr(r, 'rdata')],
            'steps': len(iter_result.steps),
            'from_cache': iter_result.from_cache,
        }
        
        # Our recursive resolution
        with Timer("Recursive") as t2:
            rec_result = self.resolve(domain, qtype, mode='recursive')
        results['recursive'] = {
            'time_ms': t2.elapsed_ms,
            'answers': [r.rdata for r in rec_result.answers if hasattr(r, 'rdata')],
            'steps': len(rec_result.steps),
            'from_cache': rec_result.from_cache,
        }
        
        # System DNS resolution
        try:
            with Timer("System") as t3:
                addr_info = socket.getaddrinfo(domain, None)
                system_ips = list(set(info[4][0] for info in addr_info))
            results['system'] = {
                'time_ms': t3.elapsed_ms,
                'answers': system_ips,
            }
        except socket.gaierror as e:
            results['system'] = {
                'time_ms': 0,
                'answers': [],
                'error': str(e),
            }
        
        return results


# ============================================================
# Quick Test
# ============================================================

if __name__ == '__main__':
    print(f"\n{bold('🔍 DNS Resolver Engine — Quick Test')}\n")
    
    resolver = DNSResolver(verbose=True)
    
    # Test recursive resolution
    print(f"\n{info('═══ Recursive Resolution ═══')}")
    result = resolver.resolve('google.com', 'A', mode='recursive')
    print(f"Domain: {result.domain}")
    print(f"Status: {result.rcode_name}")
    print(f"Time: {result.total_time_ms:.1f}ms")
    print(f"Answers:")
    for ans in result.answers:
        print(f"  {ans.rtype_name:6s} {ans.rdata} (TTL: {ans.ttl}s)")
    
    # Test iterative resolution
    print(f"\n{info('═══ Iterative Resolution ═══')}")
    result = resolver.resolve('google.com', 'A', mode='iterative')
    print(f"Domain: {result.domain}")
    print(f"Status: {'OK' if result.success else result.error}")
    print(f"Time: {result.total_time_ms:.1f}ms")
    print(f"Steps: {len(result.steps)}")
    for i, step in enumerate(result.steps, 1):
        print(f"  {i}. {step.server_name} ({step.server_ip}) — {step.elapsed_ms:.1f}ms")
    print(f"Answers:")
    for ans in result.answers:
        print(f"  {ans.rtype_name:6s} {ans.rdata} (TTL: {ans.ttl}s)")

