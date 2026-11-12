# 🎓 Computer Networks — DNS Resolver Viva Cheatsheet

> Quick revision notes for lab viva, presentation, and project defense.

---

## ⚡ 30-Second Elevator Pitch

> *"Good morning/afternoon, Sir. My project is a **Custom DNS Resolver from scratch** built in Python.*  
> *Instead of relying on third-party libraries, we implemented the **RFC 1035 protocol using raw UDP socket programming** and manual binary packet serialization.*  
> *It supports both **Iterative and Recursive** resolution, multi-record lookups (A, AAAA, MX, NS, CNAME), a **TTL-based in-memory cache**, and provides both a CLI with step-by-step resolution tracing and an interactive Web Dashboard."*

---

## 🎯 Top 10 Rapid-Fire Viva Questions

### 1. Which transport layer protocol does DNS use, and on which port?
* **Answer:** **UDP on Port 53** by default for standard queries because it is connectionless and fast (no 3-way handshake). It falls back to **TCP on Port 53** for responses over 512 bytes (indicated by the `TC` truncation bit) or zone transfers (AXFR).

### 2. What are the 13 Root DNS servers?
* **Answer:** They are labeled `a.root-servers.net` through `m.root-servers.net`. They are the top of the DNS namespace tree and provide referrals to Top-Level Domain (TLD) servers (like `.com`, `.org`, `.in`). (Managed via Anycast routing globally).

### 3. What is the difference between Iterative and Recursive DNS resolution?
* **Answer:**
  * **Recursive (`RD=1`):** The resolver asks a public DNS (e.g., 8.8.8.8) to do all the work and return the final answer.
  * **Iterative (`RD=0`):** The resolver itself queries Root ➔ TLD ➔ Authoritative nameservers step-by-step using referrals.

### 4. What is the structure of a DNS Header?
* **Answer:** Fixed **12 bytes**:
  * `ID` (2 bytes): Matches query with response.
  * `Flags` (2 bytes): QR (Query/Response), Opcode, AA (Authoritative Answer), TC (Truncated), RD (Recursion Desired), RA (Recursion Available), RCODE.
  * `QDCOUNT` (2 bytes): Question Count.
  * `ANCOUNT` (2 bytes): Answer Count.
  * `NSCOUNT` (2 bytes): Authority Count.
  * `ARCOUNT` (2 bytes): Additional Count.

### 5. How are domain names encoded in DNS queries?
* **Answer:** In length-prefixed label format (QNAME). Each label is preceded by its byte length and terminated by a zero byte `0x00`.
  * Example: `"www.google.com"` ➔ `\x03www\x06google\x03com\x00`.

### 6. What is DNS Compression and why is it needed?
* **Answer:** RFC 1035 compression avoids repeating domain names. If the first 2 bits of a length byte are `11` (`0xC0`), the remaining 14 bits are an offset pointer to where that domain name already appeared earlier in the packet.

### 7. What is TTL (Time-To-Live)?
* **Answer:** A 32-bit integer in Resource Records that defines how many seconds a cached record is valid. When TTL expires, the cache must evict the record and query the authoritative server again.

### 8. What are Glue Records?
* **Answer:** IP addresses of nameservers provided in the **Additional Section** of a referral. Without glue records, an infinite chicken-and-egg loop would occur if the nameserver domain is within the zone being queried.

### 9. What is NXDOMAIN?
* **Answer:** RCODE 3 (`Non-Existent Domain`). It indicates that the queried domain name does not exist according to the authoritative nameserver.

### 10. What are the common DNS attacks and defenses?
* **Answer:**
  * **DNS Spoofing / Cache Poisoning:** Attacker responds before the real server with a forged IP. (Defended by randomized Transaction IDs, random source ports, and DNSSEC).
  * **DNS Amplification (DDoS):** Small UDP request yields a huge response directed at a victim IP.

---

## 💻 Commands to Demonstrate Live

1. **Iterative Trace Demo:**
   ```bash
   python3 cli.py github.com A --trace
   ```
2. **Speed / Caching Demo (Run twice):**
   ```bash
   python3 cli.py google.com
   python3 cli.py google.com   # Shows "Cache Hit" and 0.0ms!
   ```
3. **Compare vs System DNS:**
   ```bash
   python3 cli.py google.com --compare
   ```
4. **Web UI:**
   ```bash
   python3 web_ui.py
   # Open http://localhost:8080
   ```
