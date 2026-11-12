# 🌐 Custom DNS Resolver from Scratch

> **Computer Networks (B.Tech CSE Project)**  
> Built with **Python** using **Raw UDP Sockets** & **Manual Binary Packet Construction** (RFC 1035).  
> *Zero External DNS Libraries (`dnspython`, `scapy`, etc. are NOT used).*

---

## 📌 1. Project Overview

### What is this? (In Simple Terms)
Computers on the internet do not understand human-readable names like `google.com` or `github.com`. They only communicate using numerical IP addresses like `142.250.195.14`. 

A **DNS (Domain Name System) Resolver** acts like the internet's phonebook: you provide a domain name, and it tracks down the corresponding IP address by querying servers across the global DNS hierarchy.

### What did we build?
Usually, operating systems and libraries resolve domain names behind the scenes as a black box. **In this project, we opened and rebuilt that black box from first principles:**
1. **Binary Packet Construction:** We encode human-readable domain strings into RFC 1035 binary wire-format (12-byte header, QNAME label-length encoding, etc.).
2. **Raw UDP Socket Communication:** We create low-level datagram sockets and talk directly to live Root, TLD, and Authoritative servers on port 53.
3. **Response Parsing:** We unpack incoming binary datagrams, handle DNS label compression pointers, and extract Resource Records (A, AAAA, MX, NS, CNAME, TXT).
4. **Resolution Engine:** Implements both **Iterative** (Root ➔ TLD ➔ Authoritative referral loop) and **Recursive** resolution modes.
5. **In-Memory TTL Cache:** Caches records in RAM with automatic TTL expiration to reduce redundant network traffic.
6. **Multi-Interface Access:** Interactive CLI with `dig`-style trace formatting, a real-time Web Dashboard (Flask), and a Local DNS Server on port 5353.

---

## 📚 2. Major Computer Networks (CN) Topics Covered

This project directly demonstrates core concepts from standard Computer Networks university curricula:

| # | CN Topic | Syllabus Area | How It Is Implemented in Code |
|---|----------|---------------|--------------------------------|
| **1** | **Application Layer (DNS Protocol)** | Unit 2 / Application Layer | Full implementation of RFC 1035 message structure (Header, Question, Answer, Authority, Additional sections). |
| **2** | **Transport Layer (UDP over Port 53)** | Unit 3 / Transport Layer | Uses `socket.SOCK_DGRAM` to send connectionless datagrams to live nameservers. |
| **3** | **Socket Programming** | Lab Practical / Networking | Creating, binding, sending, timing out, and receiving over IPv4 sockets via Python's native `socket` module. |
| **4** | **Distributed Hierarchical Architecture** | DNS Architecture | Iterative query resolution traversing the 13 global Root servers (`a.root-servers.net` to `m.root-servers.net`), TLD servers, and Authoritative nameservers. |
| **5** | **Iterative vs. Recursive Resolution** | DNS Mechanics | Implemented both: client-driven referral stepping (Iterative) and server-delegated resolution (Recursive). |
| **6** | **Caching & Time-to-Live (TTL)** | Performance / Latency | Local thread-safe cache that honors record TTLs and expires stale entries, reducing query time from ~300ms to **0.0ms**. |
| **7** | **Client-Server Architecture** | Network Models | Resolver acts as a client querying public DNS, and as a server (`dns_server.py`) serving queries to tools like `dig`. |
| **8** | **Bitwise & Binary Protocol Encoding** | Protocol Design | Bitwise flag manipulation (QR, Opcode, AA, TC, RD, RA, RCODE) and byte packing via `struct.pack/unpack`. |

---

## 🚀 3. How to Run Guide

### Prerequisites
- Python 3.8+
- Flask (only needed for the Web UI dashboard)

```bash
# 1. Clone repository
git clone https://github.com/hrxhit/dnsResolver.git
cd dnsResolver

# 2. Install minimal dependencies
pip install -r requirements.txt
```

---

### Option A: Command Line Interface (CLI)

The CLI offers terminal output formatted like Unix `dig`:

#### 1. Basic A Record Query:
```bash
python3 cli.py google.com
```

#### 2. Resolution Trace (Root ➔ TLD ➔ Authoritative Step-by-Step):
> 🔥 *Best command for live demonstration & viva presentation.*
```bash
python3 cli.py github.com A --trace
```

#### 3. Query Specific Record Types (MX, AAAA, NS, TXT):
```bash
python3 cli.py google.com MX
python3 cli.py google.com AAAA
python3 cli.py cloudflare.com NS
```

#### 4. Compare Performance with Operating System DNS:
```bash
python3 cli.py facebook.com --compare
```

#### 5. Interactive Shell Mode:
```bash
python3 cli.py --interactive
```
*(Inside the shell: type domain names, `trace <domain>`, `cache`, `clear`, or `exit`)*

---

### Option B: Web UI Dashboard

Run the visual dashboard with step-by-step resolution timelines, cache statistics, and interactive query forms:

```bash
python3 web_ui.py
```
Open in your browser: **[http://localhost:8080](http://localhost:8080)**  
*(If port 8080 is busy, pass any port: `python3 web_ui.py --port 5050`)*

---

### Option C: Standalone Local DNS Server (Port 5353)

Your PC can act as a local DNS server answering queries from system utilities:

```bash
python3 dns_server.py
```

In another terminal, test it with standard `dig`:
```bash
dig @127.0.0.1 -p 5353 google.com
```

---

## 🏗️ 4. Architecture & Packet Flow

```
                      [User / CLI / Web UI]
                                │
                                ▼
                       [DNS Cache Check]
                        │             │
              (Hit: 0ms)│             │(Miss)
                        ▼             ▼
                 [Return IP]    [Build DNS Query]
                                (12B Header + QNAME)
                                      │
                                      ▼
                             [UDP Socket (Port 53)]
                                      │
                 ┌────────────────────┴────────────────────┐
                 ▼                                         ▼
       [Iterative Resolution]                   [Recursive Resolution]
        1. Ask Root Server                       1. Send query to 8.8.8.8
           (Referral to TLD)                        with RD=1 flag
        2. Ask TLD Server                        2. Public DNS resolves chain
           (Referral to Authoritative)           3. Returns final answer in 1 trip
        3. Ask Authoritative Server
           (Returns Answer IP)
                 │                                         │
                 └────────────────────┬────────────────────┘
                                      ▼
                           [Parse Binary Response]
                                      │
                                      ▼
                           [Store in Cache with TTL]
                                      │
                                      ▼
                           [Output Final IP Records]
```

---

## 🎯 5. Top 5 Core Questions (Viva & Evaluation Ready)

These are the 5 foundational Computer Networks questions upon which this entire project is built, along with ideal technical answers:

### Q1. Why does DNS use UDP instead of TCP by default?
* **Answer:**
  1. **Speed & Latency:** UDP is connectionless. It avoids the 3-way TCP handshake (`SYN -> SYN-ACK -> ACK`), making resolution almost instantaneous (single round-trip time).
  2. **Message Size:** Standard DNS queries and replies are small (historically $\le 512$ bytes), fitting neatly within a single UDP datagram without packet fragmentation.
  3. **Server Scalability:** Root and authoritative DNS servers handle billions of requests per second. Maintaining persistent TCP state connections for every query would exhaust server memory and file descriptors.
  *Note:* DNS falls back to TCP (Port 53) when responses exceed 512 bytes (indicated by the `TC` - Truncation flag) or during Zone Transfers (AXFR).

---

### Q2. What is the fundamental difference between Iterative and Recursive DNS Resolution?
* **Answer:**
  * **Recursive Resolution:** The client shifts the entire burden of resolution onto the contacted DNS server (e.g., Google `8.8.8.8` or Cloudflare `1.1.1.1`) by setting the `RD=1` (Recursion Desired) bit in the header. The server traverses the hierarchy on the client's behalf and returns the final answer.
  * **Iterative Resolution:** The client sets `RD=0`. The contacted server does not resolve further; instead, it returns a referral—saying *"I do not know the answer, but ask this next server."* The client itself queries the Root server, gets referred to the Top-Level Domain (TLD) server (e.g., `.com`), gets referred to the Authoritative nameserver (e.g., `ns1.google.com`), and finally fetches the answer.
  * **In this project:** We implemented both modes. You can see the exact iterative referrals using `python3 cli.py <domain> --trace`.

---

### Q3. How does DNS message binary packing (RFC 1035) work, and what is DNS Name Compression?
* **Answer:**
  * A DNS message has a fixed **12-byte header**:
    * `ID` (16 bits): Transaction identifier matching request with response.
    * `Flags` (16 bits): `QR` (0=Query, 1=Response), `Opcode` (4 bits), `AA` (Authoritative Answer), `TC` (Truncation), `RD` (Recursion Desired), `RA` (Recursion Available), and `RCODE` (4 bits for error codes like NOERROR or NXDOMAIN).
    * `QDCOUNT`, `ANCOUNT`, `NSCOUNT`, `ARCOUNT` (16 bits each): Section record counters.
  * **Domain Name Encoding:** Domains are not stored as plain strings. Labels are prefixed with their length byte: `"www.google.com"` becomes `\x03www\x06google\x03com\x00`.
  * **Compression Pointers:** Domain names repeat often in answers. To save bandwidth, if the first two bits of a length byte are `11` (`0xC0`), the remaining 14 bits represent an offset pointing to an earlier position in the packet where the name was already written. Our parser specifically detects and follows these compression offsets.

---

### Q4. What is the role of TTL (Time-To-Live) and how does Caching prevent DNS amplification/congestion?
* **Answer:**
  * **TTL** is a 32-bit integer inside each Resource Record specifying how many seconds the record may be cached locally before being considered stale.
  * **Why it matters:** Without caching, every single HTTP request, image, or API call would trigger a trip to root and authoritative nameservers.
  * **In our project:** We implemented `DNSCache` with automatic expiry:
    * First query: ~300ms (Network round trips).
    * Second query (within TTL): **0.0ms** (Instant RAM lookup).
    * When current time $> \text{creation time} + \text{TTL}$, the cache evicts the record and requests fresh authoritative data.

---

### Q5. What are the different DNS Record Types and what purposes do they serve?
* **Answer:**
  * **`A` (Type 1):** Maps a hostname to an IPv4 address (32 bits, e.g., `142.250.195.14`).
  * **`AAAA` (Type 28):** Maps a hostname to an IPv6 address (128 bits, e.g., `2a00:1450:4001:830::200e`).
  * **`CNAME` (Type 5):** Canonical Name (Alias). Points one domain name to another domain name instead of directly to an IP.
  * **`NS` (Type 2):** Name Server record. Delegates a DNS zone to authoritative nameservers.
  * **`MX` (Type 15):** Mail Exchange record. Specifies the mail server responsible for accepting emails for the domain, with priority preferences.
  * **`TXT` (Type 16):** Arbitrary text data, commonly used for domain verification, SPF (Sender Policy Framework), and DKIM email security.

---

## 📁 6. Project Structure

```
dnsResolver/
├── dns_packet.py          # RFC 1035 binary packet builder & parser
├── dns_resolver.py        # Core resolver (Iterative + Recursive logic)
├── dns_cache.py           # Thread-safe TTL cache with hit/miss statistics
├── dns_server.py          # UDP server listening on port 5353 (serves dig)
├── cli.py                 # Feature-rich command line interface
├── web_ui.py              # Flask Web UI application
├── templates/
│   └── index.html         # Modern dark-themed dashboard template
├── utils.py               # Root servers list, terminal colors, timers
├── requirements.txt       # Project dependencies (Flask)
├── .gitignore             # Standard git ignore file
└── README.md              # Comprehensive project documentation
```

---

## 👨‍💻 Author

* **Harshit Sharma**  
* GitHub: [@hrxhit](https://github.com/hrxhit)  
* Computer Networks — 3rd Year B.Tech / CSE
