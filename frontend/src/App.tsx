import { GraduationCap, Moon, Sun } from "lucide-react";
import { lazy, Suspense } from "react";
import { NavLink, Route, Routes } from "react-router-dom";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/cn";
import Dashboard from "@/pages/Dashboard";
import ExamRunner from "@/pages/ExamRunner";
import Landing from "@/pages/Landing";
import TutorChat from "@/pages/TutorChat";
import { useThemeStore } from "@/stores/theme";

// Heavy (d3-force) — split into its own lazy chunk.
const ConceptMap = lazy(() => import("@/pages/ConceptMap"));

const NAV = [
  { to: "/tutor", label: "Tutor" },
  { to: "/exam", label: "Exam" },
  { to: "/map", label: "Concept Map" },
  { to: "/dashboard", label: "Dashboard" },
];

function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const toggle = useThemeStore((s) => s.toggle);
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
    >
      {theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
    </Button>
  );
}

function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center gap-4 px-4">
        <NavLink to="/" className="flex items-center gap-2 font-semibold">
          <GraduationCap className="size-6 text-primary" aria-hidden />
          <span>AI Exam Assistant</span>
        </NavLink>
        <nav className="ml-auto flex items-center gap-1" aria-label="Main">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted/60",
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

export default function App() {
  return (
    <div className="flex min-h-dvh flex-col">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
      >
        Skip to content
      </a>
      <Header />
      <main id="main" className="mx-auto w-full max-w-6xl flex-1 px-4 py-6">
        <Suspense fallback={<div className="p-8 text-center text-muted-foreground">Loading…</div>}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/tutor" element={<TutorChat />} />
            <Route path="/exam" element={<ExamRunner />} />
            <Route path="/map" element={<ConceptMap />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="*" element={<Landing />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="border-t border-border py-6 text-center text-sm text-muted-foreground">
        Open-source · MIT · Microsoft Agent Framework · Azure AI Foundry · GraphRAG
      </footer>
    </div>
  );
}
