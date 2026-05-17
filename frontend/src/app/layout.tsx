import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: '句式 · JuShi — 中文网络句式档案',
  description: '搜索、发现和追溯中文网络 JuShi：那些替换槽位后仍让人想起原始名场面的句式。',
  keywords: '句式,JuShi,中文梗,神评,名场面,句式搜索',
  openGraph: {
    title: '句式 · JuShi',
    description: '中文网络 JuShi 档案',
    type: 'website',
  },
};

function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="relative w-9 h-9 rounded-lg bg-indigo-500 flex items-center justify-center shadow-glow-sm group-hover:shadow-glow transition-shadow duration-300">
            <span className="text-white text-lg font-bold" style={{ fontFamily: "'Noto Serif SC', serif", lineHeight: 1 }}>
              句
            </span>
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-sm font-bold tracking-widest text-[var(--color-text)]" style={{ fontFamily: "'Noto Serif SC', serif" }}>
              句式
            </span>
            <span className="text-[10px] text-[var(--color-text-muted)] tracking-widest uppercase">
              JuShi
            </span>
          </div>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          <NavLink href="/" label="搜索" icon="⌕" />
          <NavLink href="/browse" label="发现" icon="◉" />
          <NavLink href="/museum" label="博物馆" icon="◈" />
        </nav>

        {/* Theme toggle placeholder — decorative for static build */}
        <div className="w-9 h-9 rounded-full border border-[var(--color-border)] flex items-center justify-center text-[var(--color-text-muted)] text-sm cursor-default">
          <span>☾</span>
        </div>
      </div>
    </header>
  );
}

function NavLink({ href, label, icon }: { href: string; label: string; icon: string }) {
  return (
    <Link
      href={href}
      className="group relative flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] hover:bg-[var(--color-border)] transition-all duration-200"
    >
      <span className="text-indigo-400 text-xs opacity-70 group-hover:opacity-100 transition-opacity">{icon}</span>
      <span className="font-medium">{label}</span>
    </Link>
  );
}

function Footer() {
  return (
    <footer className="mt-24 border-t border-[var(--color-border)] py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded bg-indigo-500/20 flex items-center justify-center">
              <span className="text-indigo-400 text-sm" style={{ fontFamily: "'Noto Serif SC', serif" }}>句</span>
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--color-text)]">JuShi 句式档案</p>
              <p className="text-xs text-[var(--color-text-muted)]">收录会被反复借用的中文网络句式</p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-xs text-[var(--color-text-muted)]">
            <Link href="/" className="hover:text-indigo-400 transition-colors">搜索</Link>
            <Link href="/browse" className="hover:text-indigo-400 transition-colors">发现</Link>
            <Link href="/museum" className="hover:text-indigo-400 transition-colors">博物馆</Link>
          </div>

          <p className="text-xs text-[var(--color-text-muted)]">
            © 2026 句式 · 收集被反复借用的网络记忆
          </p>
        </div>

        <div className="mt-8 flex items-center justify-center gap-2 text-xs text-[var(--color-text-muted)]/50">
          <span>「只有</span>
          <span className="text-indigo-400/60 italic">语言</span>
          <span>才是</span>
          <span className="text-vermillion-400/60 italic">时代</span>
          <span>的化石」</span>
        </div>
      </div>
    </footer>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Noto+Serif+SC:wght@400;600;700&family=Noto+Sans+Mono&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        <Header />
        <main className="min-h-[calc(100vh-56px)]">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
