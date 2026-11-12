"""
DNS Packet Builder & Parser
============================
Implements DNS message format as per RFC 1035.
Manually constructs and parses DNS packets in binary format.

DNS Message Format:
    +---------------------+
    |       Header        |  12 bytes (fixed)
    +---------------------+
    |      Question       |  Variable length
    +---------------------+
    |       Answer        |  Variable length (Resource Records)
    +---------------------+
    |      Authority      |  Variable length (Resource Records)
    +---------------------+
    |      Additional     |  Variable length (Resource Records)
    +---------------------+

Author: Harshit
Subject: Computer Networks (2nd Year)
"""

import struct
import random

# ============================================================
# DNS Record Type Constants (RFC 1035 + extensions)
# ============================================================
RECORD_TYPES = {
    'A': 1,        # IPv4 Address
    'NS': 2,       # Nameserver
    'CNAME': 5,    # Canonical Name (Alias)
    'SOA': 6,      # Start of Authority
    'MX': 15,      # Mail Exchange
    'TXT': 16,     # Text Record
    'AAAA': 28,    # IPv6 Address
}

# Reverse mapping: number -> name
RECORD_TYPE_NAMES = {v: k for k, v in RECORD_TYPES.items()}

# DNS Response Codes
RCODE_NAMES = {
    0: 'NOERROR',    # No error
    1: 'FORMERR',    # Format error
    2: 'SERVFAIL',   # Server failure
    3: 'NXDOMAIN',   # Non-existent domain
    4: 'NOTIMP',     # Not implemented
    5: 'REFUSED',    # Query refused
}

# DNS Class
CLASS_IN = 1  # Internet


class DNSHeader:
    """
    DNS Header — 12 bytes fixed size
    
    Structure (each row = 16 bits):
        ID      : 16-bit identifier (match request/response)
        FLAGS   : QR(1) | Opcode(4) | AA(1) | TC(1) | RD(1) | RA(1) | Z(3) | RCODE(4)
        QDCOUNT : Number of questions
        ANCOUNT : Number of answer records
        NSCOUNT : Number of authority records
        ARCOUNT : Number of additional records
    """
    
    def __init__(self, id=None, flags=0, qd_count=0, an_count=0, ns_count=0, ar_count=0):
        self.id = id if id is not None else random.randint(0, 65535)
        self.flags = flags
        self.qd_count = qd_count
        self.an_count = an_count
        self.ns_count = ns_count
        self.ar_count = ar_count
    
    # --- Flag extraction properties ---
    @property
    def qr(self):
        """Query (0) or Response (1)"""
        return (self.flags >> 15) & 1
    
    @property
    def opcode(self):
        """Operation code: 0=Query, 1=IQuery, 2=Status"""
        return (self.flags >> 11) & 0xF
    
    @property
    def aa(self):
        """Authoritative Answer flag"""
        return (self.flags >> 10) & 1
    
    @property
    def tc(self):
        """Truncation flag (message was truncated)"""
        return (self.flags >> 9) & 1
    
    @property
    def rd(self):
        """Recursion Desired"""
        return (self.flags >> 8) & 1
    
    @property
    def ra(self):
        """Recursion Available"""
        return (self.flags >> 7) & 1
    
    @property
    def rcode(self):
        """Response Code"""
        return self.flags & 0xF
    
    @property
    def rcode_name(self):
        return RCODE_NAMES.get(self.rcode, f'UNKNOWN({self.rcode})')
    
    def to_bytes(self):
        """Serialize header to 12 bytes (network byte order / big-endian)"""
        return struct.pack('!HHHHHH',
            self.id,
            self.flags,
            self.qd_count,
            self.an_count,
            self.ns_count,
            self.ar_count
        )
    
    @classmethod
    def from_bytes(cls, data):
        """Parse 12 bytes into DNSHeader"""
        fields = struct.unpack('!HHHHHH', data[:12])
        return cls(
            id=fields[0],
            flags=fields[1],
            qd_count=fields[2],
            an_count=fields[3],
            ns_count=fields[4],
            ar_count=fields[5]
        )
    
    def __repr__(self):
        flags = []
        if self.qr: flags.append('QR')
        if self.aa: flags.append('AA')
        if self.tc: flags.append('TC')
        if self.rd: flags.append('RD')
        if self.ra: flags.append('RA')
        return (f"DNSHeader(id={self.id}, flags=[{' '.join(flags)}], "
                f"rcode={self.rcode_name}, "
                f"qd={self.qd_count}, an={self.an_count}, "
                f"ns={self.ns_count}, ar={self.ar_count})")


class DNSQuestion:
    """
    DNS Question Section
    
    Format:
        QNAME  : Sequence of labels (length-prefixed), terminated by 0x00
        QTYPE  : 2 bytes — record type (A=1, AAAA=28, MX=15, etc.)
        QCLASS : 2 bytes — usually IN (Internet) = 1
    """
    
    def __init__(self, name, qtype='A', qclass=CLASS_IN):
        self.name = name
        self.qtype = RECORD_TYPES.get(qtype, qtype) if isinstance(qtype, str) else qtype
        self.qclass = qclass
    
    @property
    def qtype_name(self):
        return RECORD_TYPE_NAMES.get(self.qtype, f'TYPE{self.qtype}')
    
    def to_bytes(self):
        """
        Encode question to bytes.
        Domain name encoding (QNAME):
            "www.google.com" → b'\x03www\x06google\x03com\x00'
            Each label is prefixed with its length byte.
        """
        encoded = encode_domain_name(self.name)
        encoded += struct.pack('!HH', self.qtype, self.qclass)
        return encoded
    
    def __repr__(self):
        return f"DNSQuestion(name={self.name}, type={self.qtype_name})"


class DNSRecord:
    """
    DNS Resource Record (used in Answer, Authority, Additional sections)
    
    Format:
        NAME     : Domain name (may use compression pointers)
        TYPE     : 2 bytes — record type
        CLASS    : 2 bytes — class (usually IN=1)
        TTL      : 4 bytes — time to live (seconds)
        RDLENGTH : 2 bytes — length of RDATA
        RDATA    : Variable — record-type-specific data
    """
    
    def __init__(self, name, rtype, rclass, ttl, rdata_raw, rdata_parsed=None):
        self.name = name
        self.rtype = rtype
        self.rclass = rclass
        self.ttl = ttl
        self.rdata_raw = rdata_raw
        self.rdata = rdata_parsed  # Human-readable parsed data
    
    @property
    def rtype_name(self):
        return RECORD_TYPE_NAMES.get(self.rtype, f'TYPE{self.rtype}')
    
    def __repr__(self):
        return (f"DNSRecord(name={self.name}, type={self.rtype_name}, "
                f"ttl={self.ttl}, data={self.rdata})")


class DNSPacket:
    """
    Complete DNS Packet — combines Header + Questions + Resource Records
    """
    
    def __init__(self, header=None, questions=None, answers=None, 
                 authority=None, additional=None):
        self.header = header or DNSHeader()
        self.questions = questions or []
        self.answers = answers or []
        self.authority = authority or []
        self.additional = additional or []
    
    def __repr__(self):
        return (f"DNSPacket(\n"
                f"  header={self.header}\n"
                f"  questions={self.questions}\n"
                f"  answers={self.answers}\n"
                f"  authority={self.authority}\n"
                f"  additional={self.additional}\n"
                f")")


# ============================================================
# Encoding Functions
# ============================================================

def encode_domain_name(domain):
    """
    Encode domain name into DNS wire format.
    
    Example:
        "www.google.com" → b'\\x03www\\x06google\\x03com\\x00'
    
    Each label (part between dots) is preceded by a byte
    indicating its length. The sequence ends with a zero byte.
    """
    parts = domain.rstrip('.').split('.')
    encoded = b''
    for part in parts:
        length = len(part)
        if length > 63:
            raise ValueError(f"Label too long (max 63): {part}")
        encoded += bytes([length]) + part.encode('ascii')
    encoded += b'\x00'  # Terminator
    return encoded


# ============================================================
# Decoding Functions
# ============================================================

def decode_domain_name(data, offset):
    """
    Decode a domain name from DNS wire format, handling compression pointers.
    
    DNS Name Compression (RFC 1035 Section 4.1.4):
        If the first two bits of a length byte are '11', the remaining
        14 bits form a pointer to where the name continues in the packet.
        This avoids repeating common suffixes like '.com'.
    
    Returns:
        (domain_name: str, new_offset: int)
    """
    labels = []
    jumped = False
    original_offset = offset
    max_jumps = 20  # Prevent infinite loops
    jumps = 0
    
    while True:
        if offset >= len(data):
            break
            
        length = data[offset]
        
        # Check for compression pointer (first 2 bits = 11)
        if (length & 0xC0) == 0xC0:
            if not jumped:
                original_offset = offset + 2
            # Pointer: next 14 bits = offset in packet
            pointer = struct.unpack('!H', data[offset:offset+2])[0] & 0x3FFF
            offset = pointer
            jumped = True
            jumps += 1
            if jumps > max_jumps:
                raise ValueError("Too many compression pointer jumps")
            continue
        
        # Zero length = end of name
        if length == 0:
            offset += 1
            break
        
        # Regular label
        offset += 1
        label = data[offset:offset+length].decode('ascii', errors='replace')
        labels.append(label)
        offset += length
    
    domain = '.'.join(labels)
    
    if jumped:
        return domain, original_offset
    else:
        return domain, offset


def parse_rdata(rtype, rdata_raw, full_packet, rdata_offset):
    """
    Parse RDATA based on record type into human-readable format.
    
    Each record type has its own RDATA format:
        A     : 4 bytes → IPv4 address
        AAAA  : 16 bytes → IPv6 address
        NS    : Domain name (compressed)
        CNAME : Domain name (compressed)
        MX    : 2-byte preference + domain name
        TXT   : Length-prefixed text strings
        SOA   : Complex structure with multiple fields
    """
    if rtype == RECORD_TYPES['A']:
        # A record: 4 bytes → "x.x.x.x"
        if len(rdata_raw) >= 4:
            return '.'.join(str(b) for b in rdata_raw[:4])
    
    elif rtype == RECORD_TYPES['AAAA']:
        # AAAA record: 16 bytes → IPv6 address
        if len(rdata_raw) >= 16:
            parts = struct.unpack('!8H', rdata_raw[:16])
            return ':'.join(f'{p:04x}' for p in parts)
    
    elif rtype in (RECORD_TYPES['NS'], RECORD_TYPES['CNAME']):
        # NS/CNAME: domain name (may use compression)
        name, _ = decode_domain_name(full_packet, rdata_offset)
        return name
    
    elif rtype == RECORD_TYPES['MX']:
        # MX: 2-byte preference + domain name
        preference = struct.unpack('!H', rdata_raw[:2])[0]
        exchange, _ = decode_domain_name(full_packet, rdata_offset + 2)
        return f"{preference} {exchange}"
    
    elif rtype == RECORD_TYPES['TXT']:
        # TXT: one or more length-prefixed strings
        texts = []
        pos = 0
        while pos < len(rdata_raw):
            txt_len = rdata_raw[pos]
            pos += 1
            texts.append(rdata_raw[pos:pos+txt_len].decode('utf-8', errors='replace'))
            pos += txt_len
        return ' '.join(texts)
    
    elif rtype == RECORD_TYPES['SOA']:
        # SOA: primary NS + admin mailbox + 5 x 32-bit timers
        mname, pos = decode_domain_name(full_packet, rdata_offset)
        rname, pos = decode_domain_name(full_packet, pos)
        serial, refresh, retry, expire, minimum = struct.unpack(
            '!IIIII', full_packet[pos:pos+20]
        )
        return f"{mname} {rname} {serial} {refresh} {retry} {expire} {minimum}"
    
    # Fallback: hex representation
    return rdata_raw.hex()


def parse_resource_record(data, offset):
    """
    Parse a single Resource Record from the packet.
    
    Returns:
        (DNSRecord, new_offset)
    """
    # Parse name (may be compressed)
    name, offset = decode_domain_name(data, offset)
    
    # Parse fixed fields: TYPE(2) + CLASS(2) + TTL(4) + RDLENGTH(2) = 10 bytes
    rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', data[offset:offset+10])
    offset += 10
    
    # Extract raw RDATA
    rdata_raw = data[offset:offset+rdlength]
    rdata_offset = offset
    
    # Parse RDATA based on type
    rdata_parsed = parse_rdata(rtype, rdata_raw, data, rdata_offset)
    
    record = DNSRecord(name, rtype, rclass, ttl, rdata_raw, rdata_parsed)
    
    return record, offset + rdlength


# ============================================================
# Main Build & Parse Functions
# ============================================================

def build_query(domain, qtype='A', recursion_desired=True):
    """
    Build a complete DNS query packet.
    
    Args:
        domain: Domain name to query (e.g., "www.google.com")
        qtype: Query type ('A', 'AAAA', 'MX', 'NS', 'CNAME', 'TXT')
        recursion_desired: Set RD flag (ask server to do recursive resolution)
    
    Returns:
        (bytes, int) — (raw packet bytes, transaction ID)
    """
    # Build header
    # Flags: QR=0 (query), Opcode=0, RD=1 (if recursion desired)
    flags = 0x0100 if recursion_desired else 0x0000
    header = DNSHeader(flags=flags, qd_count=1)
    
    # Build question
    question = DNSQuestion(domain, qtype)
    
    # Assemble packet
    packet = header.to_bytes() + question.to_bytes()
    
    return packet, header.id


def parse_response(data):
    """
    Parse a complete DNS response packet.
    
    Args:
        data: Raw bytes of the DNS response
    
    Returns:
        DNSPacket with all sections parsed
    """
    # Parse header (first 12 bytes)
    header = DNSHeader.from_bytes(data)
    offset = 12
    
    # Parse question section
    questions = []
    for _ in range(header.qd_count):
        name, offset = decode_domain_name(data, offset)
        qtype, qclass = struct.unpack('!HH', data[offset:offset+4])
        offset += 4
        questions.append(DNSQuestion(name, qtype, qclass))
    
    # Parse answer section
    answers = []
    for _ in range(header.an_count):
        record, offset = parse_resource_record(data, offset)
        answers.append(record)
    
    # Parse authority section
    authority = []
    for _ in range(header.ns_count):
        record, offset = parse_resource_record(data, offset)
        authority.append(record)
    
    # Parse additional section
    additional = []
    for _ in range(header.ar_count):
        try:
            record, offset = parse_resource_record(data, offset)
            additional.append(record)
        except Exception:
            break  # Some additional records may have unsupported formats
    
    return DNSPacket(header, questions, answers, authority, additional)


# ============================================================
# Quick Test
# ============================================================

if __name__ == '__main__':
    # Build a query for google.com
    packet_bytes, txn_id = build_query('google.com', 'A')
    print(f"Built query packet ({len(packet_bytes)} bytes)")
    print(f"Transaction ID: {txn_id}")
    print(f"Hex: {packet_bytes.hex()}")
    
    # Decode the domain name encoding
    encoded = encode_domain_name('www.google.com')
    print(f"\nEncoded 'www.google.com': {encoded.hex()}")
    print(f"  = {encoded}")

