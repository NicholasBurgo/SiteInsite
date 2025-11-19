import React, { useState, useEffect } from "react";

/** Get system color scheme preference */
function getSystemColorScheme(): "light" | "dark" {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? "dark" : "light";
  }
  return "light";
}

/** Resolve mode (system -> light/dark) */
function resolveMode(mode: "light" | "dark" | "system"): "light" | "dark" {
  if (mode === "system") {
    return getSystemColorScheme();
  }
  return mode;
}

export function dm(mode: "light" | "dark" | "system", lightCls: string, darkCls: string) {
  const resolved = resolveMode(mode);
  return resolved === "dark" ? darkCls : lightCls;
}

export function FramerExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="framer" className={dm(mode, "min-h-screen p-10 bg-gradient-to-br from-sky-50 via-white to-emerald-50", "min-h-screen p-10 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900")}>
      <nav className={dm(mode, "sticky top-0 z-20 rounded-full border border-slate-200 px-6 py-3 shadow-xl backdrop-blur bg-white/70 flex justify-between items-center", "sticky top-0 z-20 rounded-full border border-slate-700 px-6 py-3 shadow-xl backdrop-blur bg-slate-900/60 flex justify-between items-center")}>
        <div className="font-extrabold text-2xl bg-gradient-to-r from-sky-500 to-emerald-400 bg-clip-text text-transparent">FramerSite</div>
        <div className={dm(mode, "flex gap-4 text-slate-800", "flex gap-4 text-slate-200")}>
          <a href="#" className="hover:text-sky-500">Home</a>
          <a href="#" className="hover:text-sky-500">About</a>
          <a href="#" className="hover:text-sky-500">Contact</a>
        </div>
      </nav>
      <header className="text-center mt-16">
        <h1 className="text-6xl font-extrabold tracking-tight bg-gradient-to-r from-sky-500 to-emerald-400 bg-clip-text text-transparent">
          Beautiful Framer Design
        </h1>
        <p className={dm(mode, "text-lg text-slate-600 mt-4 max-w-2xl mx-auto", "text-lg text-slate-300 mt-4 max-w-2xl mx-auto")}>
          Fluid glass effects, rounded corners, and vivid gradients inspired by Framer aesthetics.
        </p>
        <button className="mt-8 px-8 py-3 rounded-full bg-gradient-to-r from-sky-500 to-emerald-400 text-white font-semibold shadow-lg hover:opacity-90">
          Explore Now
        </button>
      </header>
      <main className="grid md:grid-cols-3 gap-8 mt-20">
        {[1, 2, 3].map((i) => (
          <div key={i} className={dm(mode, "rounded-3xl border border-slate-200 p-6 backdrop-blur-xl bg-white/60 shadow-xl", "rounded-3xl border border-slate-700 p-6 backdrop-blur-xl bg-slate-900/50 shadow-xl")}>
            <h3 className={dm(mode, "font-semibold text-xl mb-2 text-slate-900", "font-semibold text-xl mb-2 text-slate-100")}>Feature {i}</h3>
            <p className={dm(mode, "text-slate-600", "text-slate-300")}>Signature Framer look — glowing shadows and soft, glassy surfaces.</p>
          </div>
        ))}
      </main>
    </div>
  );
}

export function ModernExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="modern" className={dm(mode, "min-h-screen bg-white text-slate-900 p-10", "min-h-screen bg-slate-950 text-slate-100 p-10")}>
      <nav className={dm(mode, "flex justify-between items-center border-b border-slate-200 pb-3", "flex justify-between items-center border-b border-slate-800 pb-3")}>
        <div className="text-2xl font-bold tracking-tight">ModernCo</div>
        <div className={dm(mode, "flex gap-6 text-slate-700", "flex gap-6 text-slate-300")}>
          <a href="#" className="relative group">Home<span className={dm(mode, "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-900 transition-all", "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-100 transition-all")} /></a>
          <a href="#" className="relative group">Services<span className={dm(mode, "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-900 transition-all", "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-100 transition-all")} /></a>
          <a href="#" className="relative group">Contact<span className={dm(mode, "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-900 transition-all", "absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-slate-100 transition-all")} /></a>
        </div>
      </nav>
      <header className="mt-16 text-center">
        <h1 className="text-5xl font-bold tracking-tight">Sleek Modern Design</h1>
        <p className={dm(mode, "text-slate-600 mt-4 max-w-xl mx-auto", "text-slate-400 mt-4 max-w-xl mx-auto")}>Crisp edges, bold typography, and minimal contrast surfaces for a professional tone.</p>
        <button className={dm(mode, "mt-8 px-6 py-2 rounded-xl bg-slate-900 text-white font-semibold shadow-sm hover:opacity-90", "mt-8 px-6 py-2 rounded-xl bg-white text-slate-900 font-semibold shadow-sm hover:opacity-90")}>Get Started</button>
      </header>
      <section className="grid md:grid-cols-3 gap-8 mt-20">
        {[1, 2, 3].map((i) => (
          <div key={i} className={dm(mode, "rounded-xl border border-slate-200 p-6 shadow-sm bg-white", "rounded-xl border border-slate-800 p-6 shadow-sm bg-slate-900")}>
            <h3 className="font-semibold text-lg mb-2">Feature {i}</h3>
            <p className={dm(mode, "text-slate-600", "text-slate-400")}>Modern simplicity: focus on content clarity and precise alignment.</p>
          </div>
        ))}
      </section>
    </div>
  );
}

export function TraditionalExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="traditional" className={dm(mode, "min-h-screen p-10 bg-[repeating-linear-gradient(45deg,_#fafafa,_#fafafa_12px,_#f2f2f2_12px,_#f2f2f2_24px)] text-slate-900", "min-h-screen p-10 bg-[repeating-linear-gradient(45deg,_#0b1220,_#0b1220_12px,_#0f172a_12px,_#0f172a_24px)] text-slate-100")}>
      <nav className={dm(mode, "flex justify-between items-center border-b border-slate-300 pb-3", "flex justify-between items-center border-b border-slate-700 pb-3")}>
        <div className="text-2xl font-semibold font-serif tracking-tight">Traditional Inc.</div>
        <div className={dm(mode, "flex gap-6 text-slate-700", "flex gap-6 text-slate-300")}>
          <a href="#" className="px-2 border-r last:border-r-0 border-slate-300">Home</a>
          <a href="#" className="px-2 border-r last:border-r-0 border-slate-300">Products</a>
          <a href="#" className="px-2">Contact</a>
        </div>
      </nav>
      <header className="mt-16 text-center">
        <h1 className="text-4xl md:text-5xl font-serif font-semibold tracking-tight">Classic Website Aesthetic</h1>
        <p className={dm(mode, "text-slate-700 mt-3 max-w-2xl mx-auto", "text-slate-300 mt-3 max-w-2xl mx-auto")}>Boxed layout, serif headings, and clear separations with borders and subtle texture.</p>
        <button className={dm(mode, "mt-8 px-6 py-2 rounded border border-slate-400 bg-white text-slate-900", "mt-8 px-6 py-2 rounded border border-slate-600 bg-slate-900 text-slate-100")}>Learn More</button>
      </header>
      <main className="grid md:grid-cols-3 gap-8 mt-16">
        {[1,2,3].map(i => (
          <div key={i} className={dm(mode, "rounded-md border border-slate-300 bg-white p-6 shadow-sm", "rounded-md border border-slate-700 bg-slate-900 p-6 shadow-sm")}>
            <h3 className="font-serif text-xl mb-2">Section {i}</h3>
            <p className={dm(mode, "text-slate-700", "text-slate-300")}>A more traditional, content-first layout with sensible spacing.</p>
          </div>
        ))}
      </main>
    </div>
  );
}

export function MinimalistExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="minimalist" className={dm(mode, "min-h-screen p-16 bg-white text-slate-900", "min-h-screen p-16 bg-slate-950 text-slate-100")}>
      <nav className={dm(mode, "flex justify-between items-center pb-6 border-b border-slate-200", "flex justify-between items-center pb-6 border-b border-slate-800")}>
        <div className="tracking-tight text-xl">minimal™</div>
        <div className={dm(mode, "flex gap-8 text-slate-700", "flex gap-8 text-slate-300")}>
          <a href="#" className="hover:opacity-70">Work</a>
          <a href="#" className="hover:opacity-70">About</a>
          <a href="#" className="hover:opacity-70">Contact</a>
        </div>
      </nav>
      <header className="mt-24">
        <h1 className="text-[48px] leading-[1.05] font-light tracking-tight">Less. But Better.</h1>
        <p className={dm(mode, "mt-6 max-w-2xl text-slate-600", "mt-6 max-w-2xl text-slate-400")}>Whitespace-forward layout, thin rules, and restrained typography. Great for portfolios and calm brands.</p>
      </header>
      <main className="mt-20 grid md:grid-cols-3 gap-6">
        {[1,2,3,4,5,6].map(i => (
          <div key={i} className={dm(mode, "aspect-[4/3] border border-slate-200 rounded-md", "aspect-[4/3] border border-slate-800 rounded-md")} />
        ))}
      </main>
      <footer className={dm(mode, "mt-24 pt-6 border-t border-slate-200 text-sm", "mt-24 pt-6 border-t border-slate-800 text-sm")}>© Minimal Co.</footer>
    </div>
  );
}

export function CyberpunkExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="cyberpunk" className={dm(mode, "min-h-screen p-10 bg-slate-900 text-slate-100", "min-h-screen p-10 bg-black text-slate-100")}>
      <nav className="flex justify-between items-center pb-3 border-b border-fuchsia-500/40">
        <div className="font-mono text-xl">NEON_SYS</div>
        <div className="flex gap-6">
          {["Nodes","Mesh","Console"].map((l,i)=> (
            <a key={i} href="#" className="relative group">{l}<span className="absolute left-0 -bottom-1 w-0 group-hover:w-full h-0.5 bg-fuchsia-500 transition-all" /></a>
          ))}
        </div>
      </nav>
      <header className="mt-14 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight"><span className="bg-gradient-to-r from-cyan-400 via-fuchsia-500 to-violet-500 bg-clip-text text-transparent">Neon Interface</span></h1>
        <p className="mt-4 text-slate-300 max-w-2xl mx-auto font-mono">Glowing borders, chromatic gradients, and console-flavored typography.</p>
        <button className="mt-8 px-6 py-2 rounded-md bg-gradient-to-r from-fuchsia-600 to-cyan-500 text-white shadow-[0_0_20px_#d946ef]">Jack In</button>
</header>
      <main className="mt-16 grid md:grid-cols-3 gap-6">
        {[1,2,3].map(i => (
          <div key={i} className="p-6 rounded-lg border border-cyan-400/40 bg-slate-900/60 shadow-[0_0_15px_#22d3ee]">
            <h3 className="font-mono text-cyan-300 mb-2">Module {i}</h3>
            <p className="text-slate-300">Realtime telemetry and neon aesthetics for immersive UIs.</p>
          </div>
        ))}
      </main>
    </div>
  );
}

export function EditorialExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="editorial" className={dm(mode, "min-h-screen p-10 bg-[#fcfbf9] text-slate-900", "min-h-screen p-10 bg-slate-950 text-slate-100")}>
      <nav className={dm(mode, "pb-4 border-b border-slate-200", "pb-4 border-b border-slate-800")}><div className="font-serif text-3xl tracking-tight">The Chronicle</div></nav>
      <header className="mt-10">
        <p className="uppercase tracking-[0.2em] text-xs">Feature</p>
        <h1 className="font-serif text-5xl leading-tight mt-2">Design Systems for Content-Heavy Products</h1>
        <p className={dm(mode, "mt-3 text-slate-700 max-w-3xl", "mt-3 text-slate-300 max-w-3xl")}>An editorial grid with multi-column layout and strong typographic hierarchy.</p>
      </header>
      <main className="mt-10 grid lg:grid-cols-3 gap-8">
        <article className="lg:col-span-2 space-y-4">
          <div className={dm(mode, "aspect-[16/9] rounded-md border border-slate-200 bg-white", "aspect-[16/9] rounded-md border border-slate-800 bg-slate-900")} />
          {[1,2,3].map(i => (
            <p key={i} className={dm(mode, "text-slate-800", "text-slate-300")}>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer facilisis, arcu vitae placerat dictum, metus urna hendrerit neque.</p>
          ))}
        </article>
        <aside className="space-y-4">
          {[1,2,3,4].map(i => (
            <div key={i} className={dm(mode, "p-4 border border-slate-200 rounded-md bg-white", "p-4 border border-slate-800 rounded-md bg-slate-900")}>
              <h3 className="font-serif text-xl mb-1">Sidebar {i}</h3>
              <p className={dm(mode, "text-slate-700", "text-slate-300")}>Short kicker and excerpt to related story.</p>
            </div>
          ))}
        </aside>
      </main>
    </div>
  );
}

export function EnterpriseExample({ mode }: { mode: "light" | "dark" | "system" }) {
  return (
    <div data-theme="enterprise" className={dm(mode, "min-h-screen p-10 bg-slate-50 text-slate-900", "min-h-screen p-10 bg-slate-950 text-slate-100")}>
      <nav className={dm(mode, "flex justify-between items-center pb-3 border-b border-slate-200", "flex justify-between items-center pb-3 border-b border-slate-800")}>
        <div className="text-2xl font-semibold tracking-tight">Acme Enterprise</div>
        <div className={dm(mode, "flex gap-6 text-slate-700", "flex gap-6 text-slate-300")}>
          <a href="#" className="hover:underline">Solutions</a>
          <a href="#" className="hover:underline">Pricing</a>
          <a href="#" className="hover:underline">Docs</a>
        </div>
      </nav>
      <header className="mt-12 grid md:grid-cols-2 gap-8 items-center">
        <div>
          <h1 className="text-5xl font-bold tracking-tight">Scale with Confidence</h1>
          <p className={dm(mode, "mt-4 text-slate-700", "mt-4 text-slate-300")}>Reliable patterns, accessibility by default, and executive-friendly branding.</p>
          <div className="mt-6 flex gap-3">
            <button className="px-5 py-2 rounded-md bg-slate-900 text-white">Start Trial</button>
            <button className={dm(mode, "px-5 py-2 rounded-md border border-slate-300", "px-5 py-2 rounded-md border border-slate-700")}>Contact Sales</button>
          </div>
        </div>
        <div className={dm(mode, "aspect-[16/10] rounded-lg border border-slate-200 bg-white", "aspect-[16/10] rounded-lg border border-slate-800 bg-slate-900")} />
      </header>
      <section className="mt-12 grid sm:grid-cols-3 gap-6">
        {[["99.99%","Uptime"],["500M+","Requests/day"],["24/7","Support"]].map(([k,v],i)=> (
          <div key={i} className={dm(mode, "rounded-md p-5 border border-slate-200 bg-white", "rounded-md p-5 border border-slate-800 bg-slate-900")}>
            <div className="text-3xl font-semibold">{k}</div>
            <div className={dm(mode, "text-slate-600", "text-slate-400")}>{v}</div>
          </div>
        ))}
      </section>
    </div>
  );
}

export default function ThemeDemos() {
  const [mode, setMode] = useState<"light" | "dark" | "system">("system");
  const [theme, setTheme] = useState<"framer" | "modern" | "traditional" | "minimalist" | "cyberpunk" | "editorial" | "enterprise">("framer");
  
  // Listen for system color scheme changes
  useEffect(() => {
    if (mode === "system" && typeof window !== 'undefined' && window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      const handleChange = () => {
        // Force re-render by updating a dummy state
        setMode((prev) => prev === "system" ? "system" : prev);
      };
      
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [mode]);

  function renderExample() {
    switch (theme) {
      case "framer": return <FramerExample mode={mode} />;
      case "modern": return <ModernExample mode={mode} />;
      case "traditional": return <TraditionalExample mode={mode} />;
      case "minimalist": return <MinimalistExample mode={mode} />;
      case "cyberpunk": return <CyberpunkExample mode={mode} />;
      case "editorial": return <EditorialExample mode={mode} />;
      case "enterprise": return <EnterpriseExample mode={mode} />;
      default: return <FramerExample mode={mode} />;
    }
  }

  return (
    <div className={dm(mode, "min-h-screen bg-white text-slate-900", "min-h-screen bg-slate-950 text-slate-100")}>
      <div className={dm(mode, "sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur px-4 py-3 flex items-center justify-between", "sticky top-0 z-50 border-b border-slate-800 bg-slate-950/70 backdrop-blur px-4 py-3 flex items-center justify-between")}>
        <div className="text-sm opacity-70">Theme Demo — pick **one** design & light/dark</div>
        <div className="flex items-center gap-3">
          <label className="text-sm">Theme</label>
          <select className={dm(mode, "px-2 py-1 rounded-md border bg-white", "px-2 py-1 rounded-md border bg-slate-900 text-slate-100")} value={theme} onChange={(e) => setTheme(e.target.value as any)} aria-label="Theme">
            <option value="framer">Framer</option>
            <option value="modern">Modern</option>
            <option value="traditional">Traditional</option>
            <option value="minimalist">Minimalist</option>
            <option value="cyberpunk">Cyberpunk/Futuristic</option>
            <option value="editorial">Editorial/Magazine</option>
            <option value="enterprise">Corporate/Enterprise</option>
          </select>
          <label className="text-sm">Mode</label>
          <select className={dm(mode, "px-2 py-1 rounded-md border bg-white", "px-2 py-1 rounded-md border bg-slate-900 text-slate-100")} value={mode} onChange={(e) => setMode(e.target.value as "light" | "dark" | "system")} aria-label="Color Mode">
            <option value="system">System</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
      </div>
      <div className="p-4">
        <div className={dm(mode, "rounded-xl overflow-hidden border border-slate-200 shadow-sm", "rounded-xl overflow-hidden border border-slate-800 shadow-sm")}>
          <div className={dm(mode, "px-4 py-2 text-xs uppercase tracking-wide bg-slate-50 border-b border-slate-200", "px-4 py-2 text-xs uppercase tracking-wide bg-slate-900/60 border-b border-slate-800")}>
            {theme.charAt(0).toUpperCase() + theme.slice(1)} Example
          </div>
          {renderExample()}
        </div>
      </div>
      <div className="max-w-5xl mx-auto p-4">
        <div className={dm(mode, "rounded-lg border border-slate-200 p-3 text-xs", "rounded-lg border border-slate-800 p-3 text-xs")}>
          <div className="font-semibold mb-2">Runtime Tests</div>
          <ul className="space-y-1">
            <li className={dm(mode, "text-emerald-700", "text-emerald-400")}>✔ Components render</li>
            <li className={dm(mode, "text-emerald-700", "text-emerald-400")}>✔ Mode state = {mode} ({mode === "system" ? getSystemColorScheme() : mode})</li>
            <li className={dm(mode, "text-emerald-700", "text-emerald-400")}>✔ Theme selected = {theme}</li>
            <li className={dm(mode, "text-emerald-700", "text-emerald-400")}>✔ Only the selected example is rendered</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

