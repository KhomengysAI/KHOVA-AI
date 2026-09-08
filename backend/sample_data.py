"""Lightweight sample project (demo of the full data flow, no expensive assets)."""
import uuid
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _opp(name, tc, prob, out, ind, niche, alt, ev, gap, concept, s):
    keys = ["pain", "worsening", "purchasing_power", "speed", "market_validation", "differentiation"]
    overall = round(sum(s[k] for k in keys) / len(keys), 1)
    return {
        "id": f"op_{uuid.uuid4().hex[:10]}",
        "name": name, "target_customer": tc, "problem": prob, "desired_outcome": out,
        "industry": ind, "niche": niche, "existing_alternatives": alt, "market_evidence": ev,
        "product_gap": gap, "product_concept": concept, "scores": s, "overall_score": overall, "saved": False,
    }


def build_sample_project(user):
    opps = [
        _opp(
            "Sistem Keuangan 30 Menit untuk Freelancer",
            "Freelancer & pekerja lepas di Indonesia",
            "Pendapatan tidak menentu membuat sulit menabung dan membayar pajak",
            "Punya sistem keuangan sederhana yang berjalan otomatis tiap bulan",
            "Keuangan Pribadi", "Freelancer",
            "Aplikasi budgeting umum, template gratis yang membingungkan",
            "Banyak diskusi komunitas freelancer tentang 'gaji tidak stabil' dan bingung sisihkan pajak",
            "Belum ada produk yang dibuat khusus untuk arus kas tidak teratur",
            "Ebook + spreadsheet sistem keuangan khusus penghasilan tidak tetap",
            {"pain": 9, "worsening": 8, "purchasing_power": 7, "speed": 8, "market_validation": 8, "differentiation": 8},
        ),
        _opp(
            "Kalkulator Tarif & Proyek untuk Kreator",
            "Desainer & kreator konten lepas",
            "Sering salah menentukan harga dan rugi di proyek",
            "Menentukan tarif yang menguntungkan dengan percaya diri",
            "Bisnis", "Pricing",
            "Perhitungan manual, tebak-tebakan",
            "Keluhan umum 'undercharging' di forum freelancer",
            "Tidak ada kalkulator lokal yang memasukkan pajak & biaya operasional",
            "Spreadsheet kalkulator tarif otomatis",
            {"pain": 8, "worsening": 6, "purchasing_power": 7, "speed": 9, "market_validation": 7, "differentiation": 7},
        ),
        _opp(
            "Panduan Dana Darurat Anti-Panik",
            "Pekerja muda usia 22-30",
            "Tidak punya dana darurat dan panik saat ada kebutuhan mendadak",
            "Membangun dana darurat 3-6 bulan secara bertahap",
            "Keuangan Pribadi", "Menabung",
            "Artikel blog gratis yang tidak actionable",
            "Tingginya pencarian 'cara buat dana darurat' setiap tahun",
            "Kurang panduan langkah demi langkah yang realistis untuk gaji kecil",
            "Ebook + tracker tabungan bertahap",
            {"pain": 7, "worsening": 7, "purchasing_power": 6, "speed": 7, "market_validation": 8, "differentiation": 6},
        ),
        _opp(
            "Template Invoice & Pencatatan Klien",
            "UMKM jasa & freelancer",
            "Repot membuat invoice dan melacak pembayaran klien",
            "Invoice profesional & pembayaran terlacak otomatis",
            "Bisnis", "Administrasi",
            "Aplikasi invoice berbayar bulanan",
            "Banyak yang mencari template invoice gratis/murah",
            "Solusi sekali beli tanpa langganan",
            "Spreadsheet invoice + dashboard pembayaran",
            {"pain": 6, "worsening": 5, "purchasing_power": 7, "speed": 8, "market_validation": 7, "differentiation": 6},
        ),
        _opp(
            "Perencana Pajak Tahunan Freelancer",
            "Freelancer dengan NPWP",
            "Bingung menghitung dan menyisihkan pajak penghasilan",
            "Siap lapor pajak tanpa stres di akhir tahun",
            "Keuangan Pribadi", "Pajak",
            "Konsultan pajak yang mahal",
            "Kebingungan pajak freelancer sering dibahas di media sosial",
            "Belum ada alat bantu sederhana untuk estimasi pajak bulanan",
            "Spreadsheet estimasi & penyisihan pajak",
            {"pain": 8, "worsening": 7, "purchasing_power": 6, "speed": 7, "market_validation": 7, "differentiation": 7},
        ),
    ]
    selected = opps[0]

    research = {
        "status": "complete",
        "summary": "Pasar produk keuangan digital untuk freelancer Indonesia sedang tumbuh. Banyak yang mengeluh soal penghasilan tidak stabil, kebingungan pajak, dan sulit menabung. Produk yang ada terlalu umum dan tidak dibuat untuk arus kas tidak teratur.",
        "findings": [
            {"text": "Freelancer kesulitan menabung karena penghasilan fluktuatif", "label": "RESEARCH-BACKED", "relevance": "Inti masalah yang bisa diselesaikan produk"},
            {"text": "Banyak pencarian tentang cara menghitung pajak freelancer", "label": "RESEARCH-BACKED", "relevance": "Peluang produk khusus pajak"},
            {"text": "Template budgeting umum dianggap membingungkan", "label": "HYPOTHESIS", "relevance": "Peluang membuat versi yang lebih sederhana"},
            {"text": "Audiens bersedia membayar untuk solusi sekali beli tanpa langganan", "label": "ASSUMPTION", "relevance": "Model harga potensial"},
        ],
        "pain_points": ["Penghasilan tidak menentu", "Bingung pajak", "Sulit menabung konsisten"],
        "what_people_buy": ["Template spreadsheet", "Ebook panduan keuangan", "Kalkulator tarif"],
        "gaps": ["Produk khusus arus kas tidak teratur", "Panduan pajak freelancer yang sederhana"],
        "sources": [
            {"title": "Diskusi komunitas freelancer (contoh sampel)", "url": "https://example.com/komunitas-freelancer"},
            {"title": "Artikel keuangan pribadi (contoh sampel)", "url": "https://example.com/keuangan-freelancer"},
        ],
        "raw_notes": "(Data riset ini adalah SAMPEL demonstrasi. Jalankan riset nyata pada proyek Anda sendiri.)",
        "generated_at": now_iso(),
    }

    positioning = {
        "target_customer": "Freelancer Indonesia dengan penghasilan tidak tetap",
        "problem": "Sulit mengelola uang karena pemasukan naik-turun",
        "desired_result": "Sistem keuangan otomatis yang berjalan hanya 30 menit/bulan",
        "unique_angle": "Dirancang khusus untuk arus kas tidak teratur, bukan gaji tetap",
        "positioning": "Sistem keuangan paling sederhana untuk freelancer bergaji tidak tetap",
        "product_promise": "Tenang soal uang meski penghasilan naik-turun",
        "mechanism": "Metode 'Amplop Digital' + penyisihan otomatis",
        "suggested_pricing": "Rp 99.000 - Rp 249.000",
        "why_choose": "Praktis, lokal, sekali beli",
        "alternatives": "Aplikasi budgeting, konsultan keuangan",
        "competitive_differentiation": "Fokus 100% pada penghasilan tidak tetap",
        "one_liner": "Saya membantu freelancer merasa tenang soal keuangan tanpa harus jago Excel.",
    }

    transformation = {
        "categories": [
            {"key": "emotional_state", "label": "Emotional State", "before": "Cemas setiap kali lihat saldo", "after": "Tenang karena tahu uang terkelola"},
            {"key": "core_fear", "label": "Core Fear", "before": "Takut tidak bisa bayar kebutuhan bulan depan", "after": "Yakin ada dana untuk kebutuhan & pajak"},
            {"key": "daily_experience", "label": "Daily Experience", "before": "Bingung uang habis ke mana", "after": "Tahu persis alur uang tiap bulan"},
            {"key": "identity", "label": "Identity", "before": "Merasa 'tidak jago uang'", "after": "Merasa sebagai profesional yang teratur"},
            {"key": "practical_situation", "label": "Practical Situation", "before": "Tidak ada tabungan & dana pajak", "after": "Punya dana darurat & pajak tersisih"},
            {"key": "desired_outcome", "label": "Desired Outcome", "before": "Keuangan berantakan", "after": "Sistem keuangan otomatis 30 menit/bulan"},
        ],
        "core_transformation": "Dari cemas dan berantakan menjadi tenang dengan sistem keuangan otomatis.",
        "core_promise": "Kelola uang freelancer hanya 30 menit sebulan.",
        "customer_win": "Punya dana darurat & pajak tersisih dalam 90 hari.",
        "palette": {"primary": "#0B6E6B", "secondary": "#111C2E", "accent": "#C07A2B", "background": "#FBFAF7", "text": "#0B1220"},
    }

    return {
        "id": f"prj_{uuid.uuid4().hex[:12]}",
        "user_id": user["user_id"] if user else None,
        "title": "Contoh: Sistem Keuangan Freelancer",
        "is_sample": True,
        "status": "draft",
        "current_step": "format",
        "ui_language": "id",
        "product_language": "id",
        "models_config": {},
        "discover": {
            "mode": "know",
            "idea": "Saya ingin membantu freelancer mengatur keuangan mereka",
            "expertise": "Perencanaan keuangan pribadi",
            "audience": "Freelancer dan pekerja lepas",
            "problem": "Penghasilan tidak menentu sehingga sulit menabung",
            "industry": "Keuangan pribadi",
        },
        "research": research,
        "opportunities": opps,
        "selected_opportunity_id": selected["id"],
        "positioning": positioning,
        "transformation": transformation,
        "format": None,
        "ebook": None,
        "spreadsheet": None,
        "website": None,
        "qa": [],
        "branding": None,
        "assets": [],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
