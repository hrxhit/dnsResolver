"""
Generate Ultra-Sleek Presentation & Viva Master Guide PDF
For Sarah Singh (Roll: 35615602724)
Computer Networks - DNS Resolver Project
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

OUTPUT_PDF = "/home/harshit/Desktop/DNS resolver/VIVA.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)

        # Header
        self.line(40, A4[1] - 32, A4[0] - 40, A4[1] - 32)
        self.drawString(40, A4[1] - 26, "CN Viva & Presentation Master Guide | Custom DNS Resolver")
        self.drawRightString(A4[0] - 40, A4[1] - 26, "Sarah Singh (Roll: 35615602724)")

        # Footer
        self.line(40, 32, A4[0] - 40, 32)
        self.drawString(40, 22, "Confidential Viva Preparation | Computer Networks 2024-28")
        self.drawRightString(A4[0] - 40, 22, f"Page {self._pageNumber} of {total_pages}")
        self.restoreState()


def build_guide():
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=44,
        bottomMargin=44
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SecH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'CodeSnippet',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#09090b'),
        spaceBefore=2,
        spaceAfter=4
    )

    story = []

    # Title Banner
    story.append(Paragraph("COMPUTER NETWORKS VIVA & PRESENTATION MASTER GUIDE", title_style))
    story.append(Paragraph("<b>Student:</b> Sarah Singh &bull; <b>Roll No:</b> 35615602724 &bull; <b>Project:</b> Custom DNS Resolver from Scratch", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0f172a"), spaceAfter=10))

    # =========================================================================
    # PART 0: THE 30-SECOND AURA OPENING SCRIPT
    # =========================================================================
    story.append(Paragraph("SECTION 0: THE 30-SECOND 'AURA' OPENING SCRIPT", h1_style))
    story.append(Paragraph("<i>Jab presentation start ho, bina hichkichaye confident hoke ye bolo. Teacher pehli line me hi impress ho jayega:</i>", body_style))
    
    pitch_text = (
        "<b>Exact English Script:</b><br/>"
        "“Good morning Sir/Ma'am, my project is a <b>Custom DNS Resolver built from scratch in Python</b>. "
        "Most developers resolve domains using black-box libraries like <i>dnspython</i> or system calls. "
        "In this project, I deliberately avoided all third-party libraries and implemented the <b>RFC 1035 wire-protocol "
        "directly over raw UDP datagram sockets (Port 53)</b>.<br/>"
        "It constructs binary packet headers, handles 14-bit DNS name compression pointers, implements an <b>Iterative "
        "Resolution loop</b> that manually queries the 13 global Root servers down to Authoritative nameservers, and features "
        "an in-memory <b>TTL caching engine</b> that drops latency from 380 milliseconds to <b>0.0 milliseconds</b>.”"
    )
    
    t_pitch = Table([[Paragraph(pitch_text, body_style)]], colWidths=[523])
    t_pitch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#3b82f6')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t_pitch)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 1: BILKUL DESI BASICS (No-BS Concepts)
    # =========================================================================
    story.append(Paragraph("SECTION 1: BILKUL DESI BASICS (No-BS Networking Concepts)", h1_style))
    
    basics = [
        ("1. DNS Kya Hai?", "Internet ki <b>Truecaller / Phonebook</b>. Insaan naam yaad rakhte hain (google.com), machines sirf number (IP address: 142.250.x.x) samajhti hain. DNS naam ko number me convert karta hai."),
        ("2. Packet Kya Hota Hai?", "Internet par data ek saath nahi behata, chhote-chhote lifaafe (envelopes) me jaata hai jise <b>Packet / Datagram</b> kehte hain. Isme do hisse hote hain: <b>Header</b> (lifaafe pe likha address aur flags) aur <b>Body / Data</b> (jo actual message hai)."),
        ("3. Port 53 Kya Hai?", "Computer ek building hai jisme 65,535 khidkiyan (ports) hain. DNS ka permanent adda <b>Port 53</b> hai. Saare DNS servers port 53 par khade hoke request ka intezaar karte hain."),
        ("4. UDP vs TCP?", "<b>TCP</b> phone call jaisa hai (pehle hello-hello 3-way handshake hoti hai, phir baat hoti hai - safe but slow).<br/><b>UDP</b> postcard jaisa hai (bina handshake seedha fek diya - super fast!). DNS ko fast hona zaroori hai, isliye DNS <b>UDP</b> use karta hai."),
    ]
    t_b_data = [[Paragraph(f"<b>{q}</b>", ParagraphStyle('BQ', parent=body_style, fontName='Helvetica-Bold', textColor=colors.HexColor('#1e40af'))),
                 Paragraph(ans, body_style)] for q, ans in basics]
    t_b = Table(t_b_data, colWidths=[130, 393])
    t_b.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_b)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 2: HAMARE PROJECT MEIN ASLIYAT MEIN HO KYA RAHA HAI?
    # =========================================================================
    story.append(Paragraph("SECTION 2: HAMARA PROJECT ASLIYAT MEIN KYA KARTA HAI? (Step-by-Step)", h1_style))
    flow_steps = (
        "<b>Jab hum likhte hain: <code>python3 cli.py github.com A --trace</code>, andar ye 5 steps hote hain:</b><br/>"
        "<b>Step 1 (Diary Check):</b> Code pehle apni RAM diary (Cache) me dekhta hai ki kya github.com pehle se hai? Agar haan, toh 0.0ms me answer wahi se de deta hai.<br/>"
        "<b>Step 2 (Packet Crafting):</b> Agar nahi mila, toh 'github.com' ko RFC 1035 format ke 28 hex bytes me pack karta hai (12-byte header + label bytes <code>\\x06github\\x03com\\x00</code>).<br/>"
        "<b>Step 3 (UDP Socket):</b> Python socket banata hai aur Internet ke 13 Root Servers me se ek (e.g. <code>198.41.0.4</code>) par packet UDP port 53 pe fekta hai.<br/>"
        "<b>Step 4 (Iterative Loop - Referral Chasing):</b><br/>"
        "&nbsp;&nbsp;&bull; <b>Root Server</b> bolta hai: <i>'Mujhe github nahi pata, par .com TLD server <code>192.52.178.30</code> se poocho.'</i><br/>"
        "&nbsp;&nbsp;&bull; <b>TLD Server</b> bolta hai: <i>'Main .com hoon, github ke authoritative nameserver <code>205.251.194.8</code> se poocho.'</i><br/>"
        "&nbsp;&nbsp;&bull; <b>Authoritative Server</b> bolta hai: <i>'Haan yeh lo github ka exact IP: <b>135.235.149.144</b>!'</i><br/>"
        "<b>Step 5 (Parsing & Caching):</b> Code raw binary bytes ko decode karta hai, IP nikaalta hai, diary (cache) me TTL expiry ke saath likhta hai, aur screen pe print karta hai."
    )
    t_flow = Table([[Paragraph(flow_steps, body_style)]], colWidths=[523])
    t_flow.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0fdf4')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#16a34a')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_flow)
    story.append(Spacer(1, 10))

    # =========================================================================
    # PART 3: TECH STACK & FILE ANATOMY
    # =========================================================================
    story.append(Paragraph("SECTION 3: FILE ANATOMY (Kon si file kya karti hai)", h1_style))
    files_data = [
        [Paragraph("<b>File Name</b>", ParagraphStyle('FH', parent=body_style, fontName='Helvetica-Bold')), 
         Paragraph("<b>Role in Project (Desi Samajh)</b>", ParagraphStyle('FH', parent=body_style, fontName='Helvetica-Bold')),
         Paragraph("<b>Key Code Concept</b>", ParagraphStyle('FH', parent=body_style, fontName='Helvetica-Bold'))],
        
        [Paragraph("<code>dns_packet.py</code>", code_style),
         Paragraph("<b>The Translator:</b> Domain string ko hex bytes me pack karta hai aur server se aane wale binary bytes ko decode karta hai.", body_style),
         Paragraph("<code>struct.pack('!HHHHHH')</code>, 0xC0 compression pointer parser.", body_style)],
        
        [Paragraph("<code>dns_resolver.py</code>", code_style),
         Paragraph("<b>The Engine / Postman:</b> Asli networking yahan hoti hai. UDP socket banata hai, port 53 pe bhejta hai, Root ➔ TLD ➔ Auth loop chalata hai.", body_style),
         Paragraph("<code>socket.socket(AF_INET, SOCK_DGRAM)</code>, Iterative while loop.", body_style)],

        [Paragraph("<code>dns_cache.py</code>", code_style),
         Paragraph("<b>The Memory Diary:</b> Resolved IPs ko TTL timestamp ke saath store karta hai taaki repeat query 0ms me ho sake.", body_style),
         Paragraph("Thread-safe dictionary, TTL expiration logic.", body_style)],

        [Paragraph("<code>cli.py</code>", code_style),
         Paragraph("<b>Terminal Interface:</b> Terminal me dig-style colored trace aur comparison output dikhata hai.", body_style),
         Paragraph("Argument parsing (<code>--trace</code>, <code>--compare</code>).", body_style)],

        [Paragraph("<code>web_ui.py</code>", code_style),
         Paragraph("<b>Visual Dashboard:</b> Flask web server jo localhost:8080 par aesthetic card-based UI dikhata hai.", body_style),
         Paragraph("Flask REST endpoints (<code>/api/resolve</code>, <code>/api/compare</code>).", body_style)],

        [Paragraph("<code>dns_server.py</code>", code_style),
         Paragraph("<b>Local Server Daemon:</b> PC ko port 5353 par mini DNS server bana deta hai (dig command isse baat kar sakti hai).", body_style),
         Paragraph("UDP socket bind to <code>127.0.0.1:5353</code>.", body_style)],
    ]
    t_files = Table(files_data, colWidths=[95, 238, 190])
    t_files.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_files)
    story.append(PageBreak())

    # =========================================================================
    # PART 4: TOP 10 VIVA QUESTIONS WITH AURA ANSWERS
    # =========================================================================
    story.append(Paragraph("SECTION 4: TOP 10 VIVA QUESTIONS + AURA ANSWERS (The Exam Lifesaver)", h1_style))
    story.append(Paragraph("<i>Har question ke do answer hain: ek normal concept, aur ek 'Aura Answer' (agar blank ho jao toh bina soche bas wahi bol dena!).</i>", body_style))
    story.append(Spacer(1, 4))

    viva_qa = [
        {
            "tag": "[IMPORTANT / MUST DO]", "color": "#dc2626",
            "q": "Q1. Tumne Python ki bani-banayi library (dnspython / scapy) kyu use nahi ki?",
            "ans": "Bani-banayi library sirf high-level call hoti hai jo andar ke binary protocol ko chhupa deti hai. Humne RFC 1035 wire format khud byte-by-byte struct module se banaya hai taaki Application Layer aur Transport Layer socket programming ki internal working prove ho sake.",
            "aura": "“Sir, dnspython use karne se to 2 line ka code banta. Main objective RFC 1035 binary wire-format aur raw UDP socket programming ko first principles se implement karna tha.”"
        },
        {
            "tag": "[CRITICAL CONCEPT]", "color": "#dc2626",
            "q": "Q2. DNS UDP kyu use karta hai, TCP kyu nahi?",
            "ans": "1. Speed: UDP connectionless hai, 3-way handshake ka overhead nahi hota. 2. Lightweight: DNS request < 512 bytes hoti hai toh single datagram me aati hai. 3. Scalability: Root servers par lakho connections ka TCP state rakhna impossible hai. (Note: TCP tab use hota hai jab response 512B se bada ho TC flag ke sath ya Zone Transfer AXFR ho).",
            "aura": "“Sir, UDP avoids the 3-way handshake latency overhead and standard DNS queries fit in a single 512-byte datagram. TCP is only reserved for zone transfers and truncated responses.”"
        },
        {
            "tag": "[MUST DO]", "color": "#16a34a",
            "q": "Q3. Iterative aur Recursive resolution me kya farak hai?",
            "ans": "<b>Recursive (RD=1):</b> Client ek server (8.8.8.8) ko bolta hai 'Mujhe final answer laake do, poora kaam tum karo'.<br/><b>Iterative (RD=0):</b> Client khud ek-ek karke Root ➔ TLD ➔ Authoritative ke paas jata hai referrals follow karte hue.",
            "aura": "“Sir, Recursive me delegation server par hoti hai with RD=1 bit, jabki Iterative me client khud Root, TLD aur Authoritative hierarchy ko referrals ke through walk karta hai.”"
        },
        {
            "tag": "[HIGH CHANCE]", "color": "#2563eb",
            "q": "Q4. TTL (Time-To-Live) kya hota hai aur tumhara cache kaise kaam karta hai?",
            "ans": "TTL ek 32-bit integer hai jo batata hai record kitne seconds valid rahega. Humara resolver resolved IP ko local dictionary me store karta hai. Agar time < TTL hai toh network pe jaye bina instant 0.0ms me return karta hai.",
            "aura": "“Sir, TTL prevents stale DNS entries and reduces root-server load. Our in-memory cache drops lookup latency from 380ms to sub-millisecond 0.0ms.”"
        },
        {
            "tag": "[EASY MARKS]", "color": "#16a34a",
            "q": "Q5. DNS Packet Header ka size aur structure kya hota hai?",
            "ans": "Exact 12 bytes fixed size: Transaction ID (16-bit), Flags (16-bit: QR, Opcode, AA, TC, RD, RA, RCODE), aur 4 section counters (QDCOUNT, ANCOUNT, NSCOUNT, ARCOUNT - har ek 16-bit).",
            "aura": "“Sir, exactly 12 bytes in big-endian network byte order containing a 16-bit ID, 16-bit control flags, and four 16-bit count fields.”"
        },
        {
            "tag": "[TRICKY QUESTION]", "color": "#d97706",
            "q": "Q6. Domain Name ko binary me kaise encode karte hain (QNAME)?",
            "ans": "Dots se split karke har label ke aage uski length ka byte lagate hain aur aakhri me zero byte (0x00) lagate hain. Jaise 'www.google.com' banta hai: \\x03www\\x06google\\x03com\\x00.",
            "aura": "“Sir, length-prefixed label format: each label is preceded by its 1-byte length and terminated with a null byte 0x00.”"
        },
        {
            "tag": "[HARD / PROFESSOR FAVORITE]", "color": "#dc2626",
            "q": "Q7. DNS Compression Pointer (0xC0) kya hota hai?",
            "ans": "Domain names baar-baar repeat hote hain. Space bachane ke liye RFC 1035 rule banata hai: Agar length byte ke pehle 2 bits '11' (hex 0xC0) hain, toh baaki ke 14 bits ek pointer hote hain jo packet ke purane offset ki taraf point karte hain jahan wo naam pehle likha tha.",
            "aura": "“Sir, if the first two bits are 11 (0xC0), the remaining 14 bits act as an offset pointer to a previously decoded name in the packet, preventing redundant string repetitions.”"
        },
        {
            "tag": "[CONCEPTUAL]", "color": "#2563eb",
            "q": "Q8. NXDOMAIN aur SERVFAIL me kya farak hai?",
            "ans": "<b>NXDOMAIN (RCODE 3):</b> Server chal raha hai, par domain exist hi nahi karta.<br/><b>SERVFAIL (RCODE 2):</b> Server par koi internal issue aa gaya (e.g. timeout ya misconfiguration) aur wo resolve nahi kar paya.",
            "aura": "“Sir, NXDOMAIN means the domain does not exist in the authoritative zone, while SERVFAIL indicates the nameserver encountered an internal failure or upstream timeout.”"
        },
        {
            "tag": "[EASY / GENERAL]", "color": "#16a34a",
            "q": "Q9. Tumhara code kaun-kaun se Record Types support karta hai?",
            "ans": "A (IPv4), AAAA (IPv6), MX (Mail Exchange server), NS (Nameserver delegation), CNAME (Canonical Name alias), aur TXT (Domain verification strings).",
            "aura": "“Sir, we support A, AAAA, MX, NS, CNAME, and TXT records, each parsed according to its specific RDATA schema.”"
        },
        {
            "tag": "[EDGE CASE]", "color": "#d97706",
            "q": "Q10. Agar UDP packet network me drop ho jaye toh tumhara code kya karega?",
            "ans": "Humne socket par 5.0 seconds ka timeout lagaya hai (`sock.settimeout(5.0)`). Agar packet drop ho jaye toh `socket.timeout` exception catch hota hai, error log hoti hai, aur code crash nahi hota.",
            "aura": "“Sir, socket timeout exception handling ensures that if an upstream datagram is dropped, the resolver fails gracefully without blocking the thread.”"
        },
    ]

    for item in viva_qa:
        card_content = (
            f"<font color='{item['color']}'><b>{item['tag']}</b></font><br/>"
            f"<b>{item['q']}</b><br/>"
            f"<b>Normal Explanation:</b> {item['ans']}<br/>"
            f"<font color='#1d4ed8'><b>⚡ Aura Answer (Bina soche ye boldo):</b> {item['aura']}</font>"
        )
        t_card = Table([[Paragraph(card_content, body_style)]], colWidths=[523])
        t_card.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ffffff')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_card)
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # =========================================================================
    # PART 5: LIVE DEMO PLAYBOOK
    # =========================================================================
    story.append(Paragraph("SECTION 5: LIVE DEMO PLAYBOOK (Screen par kya run karke dikhana hai)", h1_style))
    story.append(Paragraph("<i>Professor ke bolte hi yeh 3 commands run karke dikhana:</i>", body_style))

    demo_steps = [
        ("Demo 1: The Iterative Trace Flex",
         "python3 cli.py github.com A --trace",
         "Screen pe Root Server (192.33.4.12) -> .com TLD -> AWS Nameserver teen steps aayenge.<br/>"
         "<b>Kya bolna hai:</b> <i>'Sir dekhiye, yahan koi shortcut nahi liya. Step 1 me Root server ne referral diya, Step 2 me TLD server ne referral diya, aur Step 3 me Authoritative server ne final IP diya.'</i>"),

        ("Demo 2: The Cache Speedup Flex",
         "python3 cli.py github.com A",
         "Same command bina trace ke chalao. Output me likha aayega: <b>Time: 0.0ms | Source: Cache Hit ✓</b>.<br/>"
         "<b>Kya bolna hai:</b> <i>'Sir pehli baar me 380ms lage the, second time humare TTL-cache ne bina network call kiye 0.0ms me memory se return kar diya.'</i>"),

        ("Demo 3: Latency Benchmark vs System DNS",
         "python3 cli.py google.com --compare",
         "Side-by-side comparison table aayega showing Iterative vs Recursive vs Host OS DNS.<br/>"
         "<b>Kya bolna hai:</b> <i>'Yahan hum apne resolver ki performance host operating system ke getaddrinfo resolver se compare kar rahe hain.'</i>"),

        ("Demo 4: Web UI Dashboard",
         "python3 web_ui.py (Open http://localhost:8080)",
         "Sleek modern card-based dashboard khulega.<br/>"
         "<b>Kya bolna hai:</b> <i>'Sir, demonstration ke liye humne ek responsive web dashboard bhi banaya hai jisme hop timeline aur live cache inspection supported hai.'</i>"),
    ]

    for d_title, d_cmd, d_desc in demo_steps:
        d_text = (
            f"<b>{d_title}</b><br/>"
            f"<font color='#047857'><b>Command:</b> <code>{d_cmd}</code></font><br/>"
            f"{d_desc}"
        )
        t_demo = Table([[Paragraph(d_text, body_style)]], colWidths=[523])
        t_demo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#94a3b8')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_demo)
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 6))

    # =========================================================================
    # PART 6: EMERGENCY BAILOUT SCRIPT (Out of Syllabus Savior)
    # =========================================================================
    story.append(Paragraph("SECTION 6: EMERGENCY BAILOUT SCRIPT (Jab Examiner kuch ajeeb pooch le)", h1_style))
    bailout_text = (
        "Agar examiner koi high-level advanced topic pooch le (jaise DNSSEC, Anycast BGP routing, EDNS0, DoH):<br/>"
        "<b>Step 1: Ghabrana mat. Bilkul chup mat rehna.</b><br/>"
        "<b>Step 2: Yeh line bolo:</b><br/>"
        "<i>“Sir, that is related to advanced DNS extensions like DNSSEC cryptographic verification and EDNS0 buffer scaling. "
        "In our core scope, we strictly prioritized mastering RFC 1035 fundamental socket mechanics and binary serialization. "
        "However, as mentioned in Chapter 9 of our report under Future Scope, DNSSEC and DNS-over-HTTPS are our direct next milestones.”</i><br/>"
        "➔ <b>Result:</b> Examiner sochenga ki bache ko na sirf basics aate hain, balki aage ka roadmap bhi pata hai!"
    )
    t_bailout = Table([[Paragraph(bailout_text, body_style)]], colWidths=[523])
    t_bailout.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fff7ed')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#ea580c')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_bailout)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Presentation Guide PDF generated at: {OUTPUT_PDF}")

if __name__ == '__main__':
    build_guide()
