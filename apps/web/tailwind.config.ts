import type { Config } from "tailwindcss";
export default {darkMode:"class",content:["./app/**/*.{ts,tsx}","./components/**/*.{ts,tsx}"],theme:{extend:{colors:{ink:"hsl(var(--ink))",muted:"hsl(var(--muted))",panel:"hsl(var(--panel))",line:"hsl(var(--line))",brand:"hsl(var(--brand))",accent:"hsl(var(--accent))"},boxShadow:{soft:"0 12px 40px rgba(15,23,42,.08)"}}},plugins:[]} satisfies Config;

