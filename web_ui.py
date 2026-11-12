"""
DNS Resolver Web Dashboard
============================
Flask-based web UI for querying DNS and viewing results.

Features:
- Query any domain with any record type
- Toggle between iterative and recursive resolution
- View resolution trace with step-by-step visualization
- Cache statistics dashboard
- Performance comparison

Run:
    python web_ui.py
    Open: http://localhost:5000

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

from flask import Flask, render_template, request, jsonify
import time
import json

from dns_resolver import DNSResolver
from dns_cache import DNSCache
from dns_packet import RECORD_TYPES

app = Flask(__name__)

# Shared resolver instance
cache = DNSCache()
resolver = DNSResolver(cache=cache)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/resolve', methods=['POST'])
def api_resolve():
    """
    API endpoint for DNS resolution.
    
    Request JSON:
        {
            "domain": "google.com",
            "type": "A",
            "mode": "iterative"
        }
    
    Response JSON:
        {
            "success": true,
            "domain": "google.com",
            "answers": [...],
            "trace": [...],
            "time_ms": 123.4,
            "from_cache": false
        }
    """
    data = request.get_json()
    domain = data.get('domain', '').strip()
    qtype = data.get('type', 'A').upper()
    mode = data.get('mode', 'recursive')
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
    
    try:
        result = resolver.resolve(domain, qtype, mode=mode)
        
        # Format answers
        answers = []
        for record in result.answers:
            answers.append({
                'name': record.name,
                'type': record.rtype_name,
                'ttl': record.ttl,
                'data': record.rdata or record.rdata_raw.hex(),
            })
        
        # Format trace
        trace = []
        for step in result.steps:
            step_data = {
                'server_ip': step.server_ip,
                'server_name': step.server_name,
                'domain': step.query_domain,
                'type': step.query_type,
                'time_ms': round(step.elapsed_ms, 1),
                'from_cache': step.from_cache,
            }
            if step.response:
                step_data['answer_count'] = len(step.response.answers)
                step_data['authority_count'] = len(step.response.authority)
                if step.response.answers:
                    step_data['answers'] = [
                        {'type': r.rtype_name, 'data': r.rdata}
                        for r in step.response.answers
                    ]
                if step.response.authority:
                    ns_records = [r for r in step.response.authority if r.rtype == 2]
                    step_data['referrals'] = [r.rdata for r in ns_records[:3]]
            trace.append(step_data)
        
        # Format authority
        authority = []
        for record in result.authority:
            authority.append({
                'name': record.name,
                'type': record.rtype_name,
                'ttl': record.ttl,
                'data': record.rdata or record.rdata_raw.hex(),
            })
        
        return jsonify({
            'success': result.success,
            'domain': result.domain,
            'query_type': result.query_type,
            'mode': mode,
            'answers': answers,
            'authority': authority,
            'trace': trace,
            'time_ms': round(result.total_time_ms, 1),
            'from_cache': result.from_cache,
            'rcode': result.rcode_name,
            'error': result.error,
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare', methods=['POST'])
def api_compare():
    """Compare resolution methods"""
    data = request.get_json()
    domain = data.get('domain', '').strip()
    qtype = data.get('type', 'A').upper()
    
    if not domain:
        return jsonify({'success': False, 'error': 'Domain is required'}), 400
    
    try:
        comparison = resolver.compare_with_system(domain, qtype)
        
        # Format for JSON
        formatted = {}
        for method, result in comparison.items():
            formatted[method] = {
                'time_ms': round(result['time_ms'], 1),
                'answers': [str(a) for a in result.get('answers', [])],
                'steps': result.get('steps', '-'),
                'from_cache': result.get('from_cache', False),
                'error': result.get('error'),
            }
        
        return jsonify({'success': True, 'comparison': formatted})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/cache')
def api_cache():
    """Get cache statistics"""
    stats = cache.get_stats()
    entries = cache.get_all_entries()
    
    formatted_entries = []
    for entry in entries:
        formatted_entries.append({
            'domain': entry['domain'],
            'type': entry['type'],
            'ttl_remaining': entry['ttl_remaining'],
            'hits': entry['hits'],
            'records': [str(r.rdata) for r in entry['records'] if hasattr(r, 'rdata')],
        })
    
    return jsonify({
        'stats': stats,
        'entries': formatted_entries,
    })


@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """Clear the cache"""
    cache.clear()
    return jsonify({'success': True, 'message': 'Cache cleared'})


import argparse
import os

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='🌐 DNS Resolver Web Dashboard')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to run web UI on (default: 8080)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    args = parser.parse_args()

    print("\n🌐 DNS Resolver Web Dashboard")
    print("=" * 40)
    print(f"  Open: http://localhost:{args.port}")
    print("=" * 40)
    app.run(debug=True, host=args.host, port=args.port)


