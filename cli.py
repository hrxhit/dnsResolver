#!/usr/bin/env python3
"""
DNS Resolver CLI
==================
Beautiful command-line interface with dig-style output.

Usage:
    python cli.py google.com                # Basic A record query
    python cli.py google.com MX             # Query MX records
    python cli.py google.com A --trace      # Show resolution trace
    python cli.py google.com --recursive    # Use recursive mode
    python cli.py google.com --compare      # Compare with system DNS
    python cli.py --interactive             # Interactive mode
    python cli.py --cache-stats             # Show cache statistics

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

import argparse
import sys
import time

from dns_resolver import DNSResolver
from dns_cache import DNSCache
from dns_packet import RECORD_TYPES, RECORD_TYPE_NAMES
from utils import (
    Colors, bold, success, error, warning, info, dim,
    format_record_type, format_ttl, print_separator,
    BANNER, Timer, PUBLIC_DNS_SERVERS
)


def print_header(domain, qtype, mode):
    """Print query header in dig-style format"""
    print()
    print(f"{bold(';; DNS RESOLVER')} — {info(f'{mode.upper()} mode')}")
    print_separator('─', 60)
    print(f"{dim(';; QUESTION SECTION:')}")
    print(f"  {bold(domain)}    IN    {format_record_type(qtype)}")
    print_separator('─', 60)


def print_answers(result):
    """Print answer section in dig-style format"""
    if result.answers:
        print(f"\n{dim(';; ANSWER SECTION:')} ({len(result.answers)} records)")
        for record in result.answers:
            ttl_str = format_ttl(record.ttl)
            rtype = format_record_type(record.rtype_name)
            name = record.name
            data = record.rdata or record.rdata_raw.hex()
            print(f"  {name:<30s}  {ttl_str:>8s}  IN  {rtype}  {Colors.BOLD}{data}{Colors.RESET}")
    else:
        print(f"\n{warning(';; NO ANSWER')}")


def print_authority(result):
    """Print authority section"""
    if result.authority:
        print(f"\n{dim(';; AUTHORITY SECTION:')} ({len(result.authority)} records)")
        for record in result.authority:
            ttl_str = format_ttl(record.ttl)
            rtype = format_record_type(record.rtype_name)
            data = record.rdata or record.rdata_raw.hex()
            print(f"  {record.name:<30s}  {ttl_str:>8s}  IN  {rtype}  {data}")


def print_additional(result):
    """Print additional section"""
    if result.additional:
        print(f"\n{dim(';; ADDITIONAL SECTION:')} ({len(result.additional)} records)")
        for record in result.additional:
            ttl_str = format_ttl(record.ttl)
            rtype = format_record_type(record.rtype_name)
            data = record.rdata or record.rdata_raw.hex()
            print(f"  {record.name:<30s}  {ttl_str:>8s}  IN  {rtype}  {data}")


def print_trace(result):
    """Print resolution trace (like dig +trace)"""
    if not result.steps:
        return
    
    print(f"\n{bold(';; RESOLUTION TRACE:')}")
    print_separator('═', 60)
    
    for i, step in enumerate(result.steps, 1):
        if step.from_cache:
            icon = "💾"
            server = f"{Colors.GREEN}Local Cache{Colors.RESET}"
        else:
            icon = "🌐"
            server = f"{step.server_name} ({Colors.CYAN}{step.server_ip}{Colors.RESET})"
        
        print(f"  {icon} Step {i}: Query {bold(step.query_domain)} {step.query_type}")
        print(f"     └─ Server: {server}")
        print(f"        Time:   {step.elapsed_ms:.1f}ms")
        
        if step.response:
            resp = step.response
            if resp.answers:
                for ans in resp.answers:
                    print(f"        Answer: {Colors.GREEN}{ans.rdata}{Colors.RESET} ({ans.rtype_name})")
            if resp.authority:
                ns_records = [r for r in resp.authority if r.rtype == 2]
                if ns_records:
                    ns_names = [r.rdata for r in ns_records[:3]]
                    print(f"        Referral → {', '.join(ns_names)}")
        print()


def print_stats(result):
    """Print query statistics"""
    print_separator('─', 60)
    
    status_color = Colors.GREEN if result.success else Colors.RED
    status_text = "NOERROR" if result.success else (result.error or result.rcode_name)
    
    print(f"  {dim('Status:')}  {status_color}{status_text}{Colors.RESET}")
    print(f"  {dim('Time:')}    {bold(f'{result.total_time_ms:.1f}ms')}")
    print(f"  {dim('Steps:')}   {len(result.steps)}")
    
    if result.from_cache:
        print(f"  {dim('Source:')}  {success('Cache Hit ✓')}")
    
    print_separator('─', 60)


def print_cache_stats(cache):
    """Print cache statistics"""
    stats = cache.get_stats()
    
    print(f"\n{bold('📊 DNS Cache Statistics')}")
    print_separator('═', 40)
    print(f"  Entries:     {stats['total_entries']} / {stats['max_size']}")
    print(f"  Hits:        {Colors.GREEN}{stats['hits']}{Colors.RESET}")
    print(f"  Misses:      {Colors.RED}{stats['misses']}{Colors.RESET}")
    print(f"  Hit Rate:    {bold(stats['hit_rate'])}")
    print(f"  Evictions:   {stats['evictions']}")
    print(f"  Total Queries: {stats['total_queries']}")
    print_separator('═', 40)
    
    entries = cache.get_all_entries()
    if entries:
        print(f"\n{bold('Cached Entries:')}")
        for entry in entries:
            domain = entry['domain']
            rtype = entry['type']
            ttl = format_ttl(entry['ttl_remaining'])
            hits = entry['hits']
            records = [str(r.rdata) for r in entry['records'] if hasattr(r, 'rdata')]
            print(f"  {domain:<30s} {rtype:6s} TTL={ttl:>8s}  Hits={hits}  → {', '.join(records[:3])}")


def print_comparison(results, domain):
    """Print comparison between resolution methods"""
    print(f"\n{bold(f'⚡ Performance Comparison for {domain}')}")
    print_separator('═', 65)
    print(f"  {'Method':<20s} {'Time':>10s} {'Answers':>10s} {'Steps':>8s} {'Cached':>8s}")
    print_separator('─', 65)
    
    for method, data in results.items():
        time_str = f"{data['time_ms']:.1f}ms"
        answers = len(data.get('answers', []))
        steps = data.get('steps', '-')
        cached = '✓' if data.get('from_cache') else '✗'
        
        if data.get('error'):
            time_str = error('ERROR')
        
        # Color the fastest green
        print(f"  {method.capitalize():<20s} {time_str:>10s} {answers:>10d} {str(steps):>8s} {cached:>8s}")
    
    print_separator('═', 65)
    
    # Show IP addresses
    for method, data in results.items():
        ips = data.get('answers', [])
        if ips:
            print(f"  {method.capitalize()}: {', '.join(str(ip) for ip in ips[:5])}")


def interactive_mode(resolver):
    """Interactive DNS query mode"""
    print(BANNER)
    print(f"{info('Type a domain name to resolve. Commands:')}")
    print(f"  {bold('domain [TYPE]')}    — Query domain (e.g., google.com MX)")
    print(f"  {bold('trace domain')}    — Show resolution trace")
    print(f"  {bold('compare domain')} — Compare with system DNS")
    print(f"  {bold('cache')}           — Show cache statistics")
    print(f"  {bold('clear')}           — Clear cache")
    print(f"  {bold('exit / quit')}     — Exit")
    print()
    
    while True:
        try:
            prompt = f"{Colors.CYAN}dns>{Colors.RESET} "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue
            
            parts = user_input.split()
            cmd = parts[0].lower()
            
            if cmd in ('exit', 'quit', 'q'):
                print(success("\n👋 Goodbye!"))
                break
            
            elif cmd == 'cache':
                print_cache_stats(resolver.cache)
                continue
            
            elif cmd == 'clear':
                resolver.cache.clear()
                print(success("Cache cleared!"))
                continue
            
            elif cmd == 'trace':
                if len(parts) < 2:
                    print(error("Usage: trace <domain> [TYPE]"))
                    continue
                domain = parts[1]
                qtype = parts[2].upper() if len(parts) > 2 else 'A'
                
                result = resolver.resolve(domain, qtype, mode='iterative')
                print_header(domain, qtype, 'iterative')
                print_trace(result)
                print_answers(result)
                print_stats(result)
                continue
            
            elif cmd == 'compare':
                if len(parts) < 2:
                    print(error("Usage: compare <domain> [TYPE]"))
                    continue
                domain = parts[1]
                qtype = parts[2].upper() if len(parts) > 2 else 'A'
                
                comparison = resolver.compare_with_system(domain, qtype)
                print_comparison(comparison, domain)
                continue
            
            # Regular query
            domain = parts[0]
            qtype = parts[1].upper() if len(parts) > 1 else 'A'
            mode = 'recursive'
            
            # Check for flags
            if '--iterative' in parts or '-i' in parts:
                mode = 'iterative'
            
            show_trace = '--trace' in parts or '-t' in parts
            
            result = resolver.resolve(domain, qtype, mode=mode)
            print_header(domain, qtype, mode)
            
            if show_trace:
                print_trace(result)
            
            print_answers(result)
            print_authority(result)
            print_stats(result)
            
        except KeyboardInterrupt:
            print(f"\n{success('👋 Goodbye!')}")
            break
        except Exception as e:
            print(error(f"Error: {e}"))


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='🔍 DNS Resolver — Computer Networks Project',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py google.com                    # A record lookup
  python cli.py google.com MX                 # MX record lookup
  python cli.py google.com A --trace          # Show resolution steps
  python cli.py google.com --mode iterative   # Iterative resolution
  python cli.py google.com --compare          # Compare with system DNS
  python cli.py --interactive                 # Interactive mode
        """
    )
    
    parser.add_argument('domain', nargs='?', help='Domain name to resolve')
    parser.add_argument('type', nargs='?', default='A',
                        help='Record type (A, AAAA, MX, NS, CNAME, TXT)')
    parser.add_argument('--mode', '-m', choices=['iterative', 'recursive'],
                        default='recursive', help='Resolution mode')
    parser.add_argument('--trace', '-t', action='store_true',
                        help='Show resolution trace')
    parser.add_argument('--compare', '-c', action='store_true',
                        help='Compare with system DNS')
    parser.add_argument('--server', '-s', default=None,
                        help='DNS server to use (for recursive mode)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode')
    parser.add_argument('--cache-stats', action='store_true',
                        help='Show cache statistics')
    
    args = parser.parse_args()
    
    # Create resolver
    cache = DNSCache()
    resolver = DNSResolver(cache=cache, verbose=args.verbose)
    
    # Interactive mode
    if args.interactive:
        interactive_mode(resolver)
        return
    
    # Need a domain for non-interactive mode
    if not args.domain:
        print(BANNER)
        print(f"{info('Usage:')} python cli.py <domain> [type] [options]")
        print(f"{info('Interactive:')} python cli.py --interactive")
        print(f"\n{dim('Run with --help for all options')}")
        return
    
    domain = args.domain
    qtype = args.type.upper()
    
    # Comparison mode
    if args.compare:
        comparison = resolver.compare_with_system(domain, qtype)
        print_comparison(comparison, domain)
        return
    
    # Regular resolution
    if args.trace:
        args.mode = 'iterative'  # Trace only makes sense with iterative
    
    result = resolver.resolve(domain, qtype, mode=args.mode)
    
    print_header(domain, qtype, args.mode)
    
    if args.trace:
        print_trace(result)
    
    print_answers(result)
    print_authority(result)
    print_additional(result)
    print_stats(result)


if __name__ == '__main__':
    main()

