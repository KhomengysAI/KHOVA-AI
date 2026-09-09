import React, { createContext, useContext, useState, useCallback } from 'react';

const DICT = {
  id: {
    'nav.dashboard': 'Dashboard', 'nav.new': 'Produk Baru', 'nav.projects': 'Proyek', 'nav.settings': 'Pengaturan',
    'nav.signin': 'Masuk', 'nav.signout': 'Keluar', 'nav.start': 'Mulai buat produk',
    'landing.kicker': 'PABRIK PRODUK DIGITAL BERTENAGA AI',
    'landing.title': 'Ubah pengetahuan Anda menjadi produk digital yang layak jual',
    'landing.subtitle': 'Riset pasar nyata, temukan peluang menguntungkan, lalu biarkan AI membuat eBook, spreadsheet, atau website siap ekspor — dengan kualitas yang diperiksa.',
    'landing.problem': 'Membuat produk digital itu melelahkan: bingung mau jual apa, tidak tahu apakah ada yang beli, dan menghabiskan berminggu-minggu menulis. Khova AI mengurus semuanya dari ide hingga aset akhir.',
    'landing.cta': 'Mulai buat produk',
    'landing.cta2': 'Lihat cara kerjanya',
    'landing.proof1': 'Riset pasar nyata + sumber', 'landing.proof2': '~20 peluang tervalidasi', 'landing.proof3': 'PDF, XLSX & Website asli',
    'landing.how': 'Cara kerja: lini produksi 10 langkah',
    'landing.formats': 'Format produk yang didukung', 'landing.comingsoon': 'Segera hadir',
    'landing.quality': 'Kualitas produk adalah prioritas utama', 'landing.quality.desc': 'Setiap produk melewati QA otomatis: skor 1-10, deteksi masalah, dan saran perbaikan sebelum ekspor.',
    'landing.tryagain': 'Coba proyek contoh',
    'steps.discover': 'Temukan', 'steps.research': 'Riset', 'steps.opportunities': 'Peluang', 'steps.positioning': 'Positioning', 'steps.transformation': 'Transformasi', 'steps.format': 'Format', 'steps.create': 'Buat', 'steps.qa': 'QA', 'steps.branding': 'Branding', 'steps.export': 'Ekspor',
    'status.done': 'Selesai', 'status.current': 'Berjalan', 'status.locked': 'Terkunci', 'status.error': 'Perlu perhatian',
    'common.next': 'Lanjut', 'common.back': 'Kembali', 'common.generate': 'Buat', 'common.regenerate': 'Buat ulang', 'common.save': 'Simpan', 'common.saved': 'Tersimpan', 'common.download': 'Unduh', 'common.preview': 'Pratinjau', 'common.edit': 'Ubah', 'common.loading': 'Memproses...', 'common.continue': 'Lanjutkan', 'common.optional': 'opsional',
    'discover.q': 'Apa yang ingin Anda buat?',
    'discover.mode.know': 'Saya tahu apa yang ingin dibuat', 'discover.mode.explore': 'Saya belum tahu',
    'discover.warning': 'Konteks lebih banyak biasanya menghasilkan rekomendasi lebih baik. Anda tetap bisa lanjut dengan informasi minimal.',
    'discover.more': 'Tambah konteks (opsional)', 'discover.btn': 'Temukan Peluang',
    'research.title': 'Riset Pasar Waktu-Nyata', 'research.run': 'Jalankan Riset Pasar', 'research.sources': 'Sumber', 'research.findings': 'Temuan', 'research.summary': 'Ringkasan',
    'opp.title': 'Kantong Menguntungkan', 'opp.build': 'Bangun Peluang Ini', 'opp.overall': 'Skor Keseluruhan', 'opp.sort': 'Urutkan', 'opp.saved': 'Disimpan', 'opp.compare': 'Bandingkan',
    'pos.title': 'Positioning Produk', 'trans.title': 'Peta Transformasi Viseral', 'trans.before': 'Sebelum', 'trans.after': 'Sesudah', 'trans.palette': 'Palet warna produk',
    'format.title': 'Ingin diubah menjadi apa?',
    'create.title': 'Buat Produk', 'qa.title': 'Editor QA Konten', 'qa.apply': 'Terapkan Perbaikan', 'branding.title': 'Branding', 'export.title': 'Ekspor Produk Final',
    'auth.title': 'Masuk untuk membuat & menyimpan produk Anda', 'auth.google': 'Lanjut dengan Google', 'auth.desc': 'Simpan progres Anda dan ekspor aset digital nyata.',
    'dash.title': 'Dashboard', 'dash.welcome': 'Selamat datang', 'projects.title': 'Proyek Saya', 'projects.empty': 'Belum ada proyek. Mulai buat produk pertama Anda!',
    'settings.title': 'Pengaturan', 'settings.uilang': 'Bahasa Aplikasi', 'settings.productlang': 'Bahasa Produk', 'settings.models': 'Model AI per Agen',
    'settings.langcard': 'Bahasa / Language',
    'dash.hero.sub': 'Ceritakan idemu, atau biarkan Khova AI membantu menemukannya lewat riset pasar.',
    'dash.recent': 'Proyek Terbaru', 'dash.stats.total': 'Total Proyek', 'dash.stats.complete': 'Selesai', 'dash.stats.progress': 'Dalam proses',
    'dash.viewall': 'Lihat semua',
    'opp.viewdetails': 'Lihat detail', 'opp.close': 'Tutup',
    'opp.detail.target': 'Target Pelanggan', 'opp.detail.problem': 'Masalah', 'opp.detail.outcome': 'Mengapa Ini Penting',
    'opp.detail.evidence': 'Bukti / Riset Pasar', 'opp.detail.alternatives': 'Konteks Pasar & Alternatif',
    'opp.detail.gap': 'Peluang Diferensiasi', 'opp.detail.concept': 'Arah Produk Potensial', 'opp.detail.confidence': 'Status Keyakinan',
    'opp.confidence.researched': 'Berbasis riset pasar', 'opp.confidence.hypothesis': 'Hipotesis AI (riset terbatas)',
    'score.how': 'Cara kerja skor', 'score.how.desc': 'Setiap peluang diberi skor 1-10 pada 6 dimensi berikut, dirata-ratakan menjadi Skor Keseluruhan.',
    'score.desc.pain': 'Seberapa menyakitkan masalah ini dirasakan pelanggan saat ini.',
    'score.desc.worsening': 'Apakah masalah ini makin mendesak / memburuk dari waktu ke waktu.',
    'score.desc.purchasing_power': 'Apakah audiens punya kemampuan & kemauan membayar solusi.',
    'score.desc.speed': 'Seberapa cepat pelanggan bisa merasakan hasil dari solusi ini.',
    'score.desc.market_validation': 'Seberapa kuat bukti bahwa orang sudah membeli solusi serupa.',
    'score.desc.differentiation': 'Seberapa besar peluang untuk tampil berbeda secara berarti dari yang sudah ada.',
    'brand.palette.title': 'Palet Produk (Kanonis)', 'brand.palette.desc': 'Palet ini otomatis dipakai di cover, PDF, website, dan semua aset — ubah di sini akan diterapkan ke semuanya.',
    'brand.palette.edit': 'Ubah Palet',
    'toast.research.done': 'Riset pasar selesai. {n} temuan & {s} sumber ditemukan.',
    'toast.research.unavailable': 'Riset web tidak tersedia — temuan di bawah adalah hipotesis AI, bukan hasil riset.',
    'toast.opp.done': '{n} peluang produk ditemukan dan diberi skor. Bandingkan lalu pilih salah satu.',
    'toast.trans.done': 'Peta transformasi dibuat. Tinjau & sesuaikan palet produk jika perlu.',
    'toast.brand.done': 'Branding dibuat. Lanjut ke Ekspor untuk membuat aset final.',
    'toast.qa.done': 'QA selesai — skor keseluruhan {n}/10. Tinjau masalah di bawah.',
    'toast.qa.apply.done': 'Perbaikan diterapkan ke semua bab. Versi asli tersimpan di riwayat.',
    'toast.qa.apply.open': 'Buka eBook',
    'toast.export.pdf': 'PDF final dibuat. Klik Unduh PDF untuk menyimpannya.',
    'toast.export.xlsx': 'XLSX dibuat. Klik Unduh XLSX untuk menyimpannya.',
    'toast.export.site': 'Website dibuat. Buka untuk melihat hasilnya secara langsung.',
  },
  en: {
    'nav.dashboard': 'Dashboard', 'nav.new': 'New Product', 'nav.projects': 'Projects', 'nav.settings': 'Settings',
    'nav.signin': 'Sign in', 'nav.signout': 'Sign out', 'nav.start': 'Start a product',
    'landing.kicker': 'AI-POWERED DIGITAL PRODUCT FACTORY',
    'landing.title': 'Turn your knowledge into a sellable digital product',
    'landing.subtitle': 'Real market research, discover profitable opportunities, then let AI build an eBook, spreadsheet or website — export-ready and quality-checked.',
    'landing.problem': 'Building digital products is exhausting: you don\'t know what to sell, whether anyone will buy, and you spend weeks writing. Khova AI handles everything from idea to final asset.',
    'landing.cta': 'Start a product',
    'landing.cta2': 'See how it works',
    'landing.proof1': 'Real market research + sources', 'landing.proof2': '~20 validated opportunities', 'landing.proof3': 'Real PDF, XLSX & Website',
    'landing.how': 'How it works: a 10-step factory line',
    'landing.formats': 'Supported product formats', 'landing.comingsoon': 'Coming soon',
    'landing.quality': 'Product quality is the top priority', 'landing.quality.desc': 'Every product passes automated QA: 1-10 scores, issue detection, and improvement suggestions before export.',
    'landing.tryagain': 'Try a sample project',
    'steps.discover': 'Discover', 'steps.research': 'Research', 'steps.opportunities': 'Opportunities', 'steps.positioning': 'Positioning', 'steps.transformation': 'Transformation', 'steps.format': 'Format', 'steps.create': 'Create', 'steps.qa': 'QA', 'steps.branding': 'Branding', 'steps.export': 'Export',
    'status.done': 'Done', 'status.current': 'In progress', 'status.locked': 'Locked', 'status.error': 'Needs attention',
    'common.next': 'Next', 'common.back': 'Back', 'common.generate': 'Generate', 'common.regenerate': 'Regenerate', 'common.save': 'Save', 'common.saved': 'Saved', 'common.download': 'Download', 'common.preview': 'Preview', 'common.edit': 'Edit', 'common.loading': 'Working...', 'common.continue': 'Continue', 'common.optional': 'optional',
    'discover.q': 'What do you want to create?',
    'discover.mode.know': 'I know what I want to build', 'discover.mode.explore': "I don't know yet",
    'discover.warning': 'More context usually produces better recommendations. You can continue with minimal information.',
    'discover.more': 'Add more context (optional)', 'discover.btn': 'Discover Opportunities',
    'research.title': 'Real-Time Market Research', 'research.run': 'Run Market Research', 'research.sources': 'Sources', 'research.findings': 'Findings', 'research.summary': 'Summary',
    'opp.title': 'Profitable Pockets', 'opp.build': 'Build This Opportunity', 'opp.overall': 'Overall Score', 'opp.sort': 'Sort', 'opp.saved': 'Saved', 'opp.compare': 'Compare',
    'pos.title': 'Product Positioning', 'trans.title': 'Visceral Transformation Map', 'trans.before': 'Before', 'trans.after': 'After', 'trans.palette': 'Product color palette',
    'format.title': 'What do you want to turn this into?',
    'create.title': 'Create Product', 'qa.title': 'Content QA Editor', 'qa.apply': 'Apply Improvements', 'branding.title': 'Branding', 'export.title': 'Final Product Export',
    'auth.title': 'Sign in to create & save your product', 'auth.google': 'Continue with Google', 'auth.desc': 'Save your progress and export real digital assets.',
    'dash.title': 'Dashboard', 'dash.welcome': 'Welcome', 'projects.title': 'My Projects', 'projects.empty': 'No projects yet. Start your first product!',
    'settings.title': 'Settings', 'settings.uilang': 'App Language', 'settings.productlang': 'Product Language', 'settings.models': 'AI Model per Agent',
    'settings.langcard': 'Language',
    'dash.hero.sub': 'Describe your idea, or let Khova AI help discover one through market research.',
    'dash.recent': 'Recent Projects', 'dash.stats.total': 'Total Projects', 'dash.stats.complete': 'Complete', 'dash.stats.progress': 'In progress',
    'dash.viewall': 'View all',
    'opp.viewdetails': 'View details', 'opp.close': 'Close',
    'opp.detail.target': 'Target Customer', 'opp.detail.problem': 'Problem', 'opp.detail.outcome': 'Why This Matters',
    'opp.detail.evidence': 'Evidence / Market Research', 'opp.detail.alternatives': 'Market Context & Alternatives',
    'opp.detail.gap': 'Differentiation Opportunity', 'opp.detail.concept': 'Potential Product Direction', 'opp.detail.confidence': 'Confidence Status',
    'opp.confidence.researched': 'Backed by market research', 'opp.confidence.hypothesis': 'AI hypothesis (limited research)',
    'score.how': 'How scoring works', 'score.how.desc': 'Each opportunity is scored 1-10 on the 6 dimensions below, averaged into the Overall Score.',
    'score.desc.pain': 'How painful this problem currently feels to customers.',
    'score.desc.worsening': 'Whether this problem is becoming more urgent / worse over time.',
    'score.desc.purchasing_power': "Whether the audience has the ability & willingness to pay for a solution.",
    'score.desc.speed': 'How quickly a customer can feel results from this solution.',
    'score.desc.market_validation': 'How strong the evidence is that people already buy similar solutions.',
    'score.desc.differentiation': 'How much room there is to stand out meaningfully from existing options.',
    'brand.palette.title': 'Product Palette (Canonical)', 'brand.palette.desc': 'This palette is automatically used across the cover, PDF, website and all assets — edits here apply everywhere.',
    'brand.palette.edit': 'Edit Palette',
    'toast.research.done': 'Market research complete. {n} findings & {s} sources found.',
    'toast.research.unavailable': 'Web research unavailable — findings below are AI hypotheses, not research results.',
    'toast.opp.done': '{n} product opportunities found and scored. Compare, then select one.',
    'toast.trans.done': 'Transformation map created. Review it and adjust the product palette if needed.',
    'toast.brand.done': 'Branding created. Continue to Export to generate the final assets.',
    'toast.qa.done': 'QA complete — overall score {n}/10. Review the issues below.',
    'toast.qa.apply.done': 'Improvements applied to all chapters. Original versions saved in history.',
    'toast.qa.apply.open': 'Open eBook',
    'toast.export.pdf': 'Final PDF generated. Click Download PDF to save it.',
    'toast.export.xlsx': 'XLSX generated. Click Download XLSX to save it.',
    'toast.export.site': 'Website generated. Open it to see the live result.',
  },
};

const LangContext = createContext(null);

export const LanguageProvider = ({ children }) => {
  const [lang, setLangState] = useState(() => localStorage.getItem('khova_ui_lang') || 'id');
  const setLang = useCallback((l) => { localStorage.setItem('khova_ui_lang', l); setLangState(l); }, []);
  const t = useCallback((key, vars) => {
    let str = (DICT[lang] && DICT[lang][key]) || (DICT.en[key]) || key;
    if (vars) {
      Object.entries(vars).forEach(([k, v]) => { str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), v); });
    }
    return str;
  }, [lang]);
  return <LangContext.Provider value={{ lang, setLang, t }}>{children}</LangContext.Provider>;
};

export const useLang = () => {
  const ctx = useContext(LangContext);
  if (!ctx) return { lang: 'id', setLang: () => {}, t: (k) => k };
  return ctx;
};

export const LANGUAGE_OPTIONS = [
  { code: 'id', label: 'Bahasa Indonesia' },
  { code: 'en', label: 'English' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'pt', label: 'Português' },
  { code: 'ja', label: '日本語' },
];
