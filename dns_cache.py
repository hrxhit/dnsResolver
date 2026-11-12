"""
DNS Cache System
=================
TTL-based in-memory cache for DNS records.

Caching is crucial in DNS because:
1. Reduces latency — no need to re-query for frequently accessed domains
2. Reduces network traffic — fewer packets on the wire
3. Reduces load on DNS servers — especially root & TLD servers

Each cached record has a TTL (Time To Live) value that determines
how long it stays valid. After TTL expires, the record is evicted
and a fresh query is made.

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

import time
import threading


class CacheEntry:
    """
    A single cache entry storing DNS records with TTL expiry.
    
    Attributes:
        records: List of DNSRecord objects
        expire_time: Unix timestamp when this entry expires
        created_at: When the entry was cached
        hit_count: Number of cache hits
    """
    
    def __init__(self, records, ttl):
        self.records = records
        self.ttl = ttl
        self.created_at = time.time()
        self.expire_time = self.created_at + ttl
        self.hit_count = 0
    
    def is_expired(self):
        """Check if the TTL has expired"""
        return time.time() > self.expire_time
    
    def remaining_ttl(self):
        """Get remaining TTL in seconds"""
        remaining = self.expire_time - time.time()
        return max(0, int(remaining))
    
    def __repr__(self):
        status = "EXPIRED" if self.is_expired() else f"TTL={self.remaining_ttl()}s"
        return f"CacheEntry(records={len(self.records)}, {status}, hits={self.hit_count})"


class DNSCache:
    """
    Thread-safe TTL-based DNS Cache.
    
    How it works:
    ┌─────────────────────────────────────────┐
    │              DNS Cache                   │
    │                                          │
    │  Key: (domain, record_type)             │
    │  Value: CacheEntry(records, TTL)        │
    │                                          │
    │  ┌──────────────────────────────┐       │
    │  │ ("google.com", "A")          │       │
    │  │  → [142.250.195.14]          │       │
    │  │  TTL: 245s remaining         │       │
    │  └──────────────────────────────┘       │
    │  ┌──────────────────────────────┐       │
    │  │ ("gmail.com", "MX")          │       │
    │  │  → [5 gmail-smtp-in.l.goo..] │       │
    │  │  TTL: 3400s remaining        │       │
    │  └──────────────────────────────┘       │
    └─────────────────────────────────────────┘
    """
    
    def __init__(self, max_size=1000):
        self._cache = {}
        self._max_size = max_size
        self._lock = threading.Lock()
        
        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
    
    def _make_key(self, domain, record_type):
        """Create cache key from domain and record type"""
        return (domain.lower().rstrip('.'), str(record_type).upper())
    
    def get(self, domain, record_type):
        """
        Look up records in cache.
        
        Args:
            domain: Domain name (e.g., "google.com")
            record_type: Record type string (e.g., "A", "MX")
        
        Returns:
            List of DNSRecord objects if found and not expired, else None
        """
        key = self._make_key(domain, record_type)
        
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired():
                # TTL expired — remove from cache
                del self._cache[key]
                self._misses += 1
                self._evictions += 1
                return None
            
            # Cache hit!
            entry.hit_count += 1
            self._hits += 1
            return entry.records
    
    def put(self, domain, record_type, records, ttl=None):
        """
        Store records in cache.
        
        Args:
            domain: Domain name
            record_type: Record type string
            records: List of DNSRecord objects
            ttl: Time to live in seconds. If None, uses minimum TTL from records.
        """
        if not records:
            return
        
        # Determine TTL
        if ttl is None:
            # Use the minimum TTL from the records
            ttls = [r.ttl for r in records if hasattr(r, 'ttl') and r.ttl > 0]
            ttl = min(ttls) if ttls else 300  # Default 5 minutes
        
        key = self._make_key(domain, record_type)
        
        with self._lock:
            # Evict if cache is full
            if len(self._cache) >= self._max_size and key not in self._cache:
                self._evict_expired()
                if len(self._cache) >= self._max_size:
                    # Remove oldest entry
                    oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
                    del self._cache[oldest_key]
                    self._evictions += 1
            
            self._cache[key] = CacheEntry(records, ttl)
    
    def _evict_expired(self):
        """Remove all expired entries"""
        expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
        for key in expired_keys:
            del self._cache[key]
            self._evictions += 1
    
    def clear(self):
        """Clear entire cache"""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0
    
    def get_stats(self):
        """
        Get cache statistics.
        
        Returns:
            dict with total entries, hits, misses, hit rate, evictions
        """
        with self._lock:
            total_queries = self._hits + self._misses
            hit_rate = (self._hits / total_queries * 100) if total_queries > 0 else 0
            
            return {
                'total_entries': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.1f}%",
                'evictions': self._evictions,
                'total_queries': total_queries,
            }
    
    def get_all_entries(self):
        """Get all non-expired cache entries for display"""
        with self._lock:
            entries = []
            for (domain, rtype), entry in self._cache.items():
                if not entry.is_expired():
                    entries.append({
                        'domain': domain,
                        'type': rtype,
                        'records': entry.records,
                        'ttl_remaining': entry.remaining_ttl(),
                        'hits': entry.hit_count,
                    })
            return entries
    
    def __len__(self):
        with self._lock:
            return len(self._cache)
    
    def __repr__(self):
        stats = self.get_stats()
        return (f"DNSCache(entries={stats['total_entries']}, "
                f"hit_rate={stats['hit_rate']}, "
                f"hits={stats['hits']}, misses={stats['misses']})")


# ============================================================
# Quick Test
# ============================================================

if __name__ == '__main__':
    cache = DNSCache()
    
    # Simulate caching
    class FakeRecord:
        def __init__(self, data, ttl=300):
            self.rdata = data
            self.ttl = ttl
        def __repr__(self):
            return f"Record({self.rdata})"
    
    # Put some records
    cache.put('google.com', 'A', [FakeRecord('142.250.195.14')], ttl=300)
    cache.put('github.com', 'A', [FakeRecord('140.82.121.3')], ttl=60)
    
    # Get from cache
    result = cache.get('google.com', 'A')
    print(f"Cache hit: {result}")
    
    result = cache.get('unknown.com', 'A')
    print(f"Cache miss: {result}")
    
    # Stats
    print(f"\nCache stats: {cache.get_stats()}")
    print(f"Cache: {cache}")

