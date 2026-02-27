// app/(marketing)/page.tsx
"use client";

import React, { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

type Mode = "bus" | "rail" | "tram" | "road";

type JourneyQuery = {
  from: string;
  to: string;
  date: string; // YYYY-MM-DD
  time: string; // HH:MM
  modes: Mode[];
};

type StoredJourney = JourneyQuery & {
  id: string;
  label?: string;
  createdAt: number;
};

const RECENTS_KEY = "rtp_recent_journeys_v1";
const SAVED_KEY = "rtp_saved_journeys_v1";

function nowLocalISODate(): string {
  const d = new Date();
  const yyyy = d.getFullYear();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

function nowLocalISOTime(): string {
  const d = new Date();
  const hh = String(d.getHours()).padStart(2, "0");
  const min = String(d.getMinutes()).padStart(2, "0");
  return `${hh}:${min}`;
}

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function toId(q: JourneyQuery): string {
  // Deterministic enough for lists; also used to dedupe.
  return `${q.from}__${q.to}__${q.date}__${q.time}__${q.modes.sort().join(",")}`.toLowerCase();
}

function buildResultsUrl(q: JourneyQuery): string {
  const params = new URLSearchParams();
  params.set("from", q.from.trim());
  params.set("to", q.to.trim());
  params.set("date", q.date);
  params.set("time", q.time);
  params.set("modes", q.modes.join(","));
  return `/results?${params.toString()}`;
}

function formatModes(modes: Mode[]): string {
  if (!modes.length) return "Any";
  return modes
    .map((m) => (m === "rail" ? "Rail" : m.charAt(0).toUpperCase() + m.slice(1)))
    .join(" · ");
}

function formatWhen(date: string, time: string): string {
  // Keep it simple and local-friendly without heavy i18n libs.
  return `${date} at ${time}`;
}

function Icon({
  name,
  className = "",
}: {
  name: "search" | "pin" | "clock" | "star" | "map" | "shield" | "spark";
  className?: string;
}) {
  const base = `inline-block align-middle ${className}`;
  switch (name) {
    case "search":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M11 19a8 8 0 1 1 0-16 8 8 0 0 1 0 16Z"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path d="M21 21l-4.3-4.3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      );
    case "pin":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 21s7-4.6 7-11a7 7 0 1 0-14 0c0 6.4 7 11 7 11Z"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path d="M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z" stroke="currentColor" strokeWidth="2" />
        </svg>
      );
    case "clock":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z" stroke="currentColor" strokeWidth="2" />
          <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
        </svg>
      );
    case "star":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 17.3 6.2 20.7l1.6-6.6L2.6 9.7l6.8-.6L12 2.9l2.6 6.2 6.8.6-5.2 4.4 1.6 6.6L12 17.3Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
        </svg>
      );
    case "map":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M9 18 3 20V6l6-2 6 2 6-2v14l-6 2-6-2Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M9 4v14" stroke="currentColor" strokeWidth="2" />
          <path d="M15 6v14" stroke="currentColor" strokeWidth="2" />
        </svg>
      );
    case "shield":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 22s8-3 8-10V5l-8-3-8 3v7c0 7 8 10 8 10Z"
            stroke="currentColor"
            strokeWidth="2"
          />
        </svg>
      );
    case "spark":
      return (
        <svg className={base} width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M12 2l1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M20 14l.9 3.1L24 18l-3.1.9L20 22l-.9-3.1L16 18l3.1-.9L20 14Z" stroke="currentColor" strokeWidth="2" />
        </svg>
      );
    default:
      return null;
  }
}

function Badge({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-full border border-neutral-200 bg-white px-2.5 py-1 text-xs font-medium text-neutral-700 shadow-sm">
      {children}
    </span>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-2xl border border-neutral-200 bg-white shadow-sm">{children}</div>;
}

function CardHeader({ title, subtitle, icon }: { title: string; subtitle?: string; icon?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 border-b border-neutral-200 px-5 py-4">
      <div className="mt-0.5 text-neutral-700">{icon}</div>
      <div className="min-w-0">
        <div className="text-sm font-semibold text-neutral-900">{title}</div>
        {subtitle ? <div className="mt-0.5 text-xs text-neutral-600">{subtitle}</div> : null}
      </div>
    </div>
  );
}

function CardBody({ children }: { children: React.ReactNode }) {
  return <div className="px-5 py-4">{children}</div>;
}

function PrimaryButton({
  children,
  onClick,
  type = "button",
  disabled,
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold",
        "bg-neutral-900 text-white shadow-sm",
        "hover:bg-neutral-800 disabled:cursor-not-allowed disabled:opacity-60",
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function SecondaryButton({
  children,
  onClick,
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold",
        "border border-neutral-200 bg-white text-neutral-900 shadow-sm",
        "hover:bg-neutral-50",
        className,
      ].join(" ")}
    >
      {children}
    </button>
  );
}

function Input({
  label,
  icon,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  icon?: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center gap-2 text-xs font-semibold text-neutral-800">
        {icon ? <span className="text-neutral-600">{icon}</span> : null}
        {label}
      </span>
      <input
        {...props}
        className={[
          "w-full rounded-xl border border-neutral-200 bg-white px-3 py-2 text-sm text-neutral-900 shadow-sm",
          "placeholder:text-neutral-400",
          "focus:outline-none focus:ring-2 focus:ring-neutral-300",
        ].join(" ")}
      />
    </label>
  );
}

function TogglePill({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        "rounded-full px-3 py-1.5 text-xs font-semibold shadow-sm",
        active ? "bg-neutral-900 text-white" : "border border-neutral-200 bg-white text-neutral-800 hover:bg-neutral-50",
      ].join(" ")}
      aria-pressed={active}
    >
      {children}
    </button>
  );
}

export default function HomePage() {
  const router = useRouter();

  const [query, setQuery] = useState<JourneyQuery>({
    from: "",
    to: "",
    date: nowLocalISODate(),
    time: nowLocalISOTime(),
    modes: ["bus", "rail"],
  });

  const [recents, setRecents] = useState<StoredJourney[]>([]);
  const [saved, setSaved] = useState<StoredJourney[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const r = safeParse<StoredJourney[]>(typeof window !== "undefined" ? localStorage.getItem(RECENTS_KEY) : null, []);
    const s = safeParse<StoredJourney[]>(typeof window !== "undefined" ? localStorage.getItem(SAVED_KEY) : null, []);
    setRecents(Array.isArray(r) ? r : []);
    setSaved(Array.isArray(s) ? s : []);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem(RECENTS_KEY, JSON.stringify(recents.slice(0, 10)));
  }, [recents]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem(SAVED_KEY, JSON.stringify(saved.slice(0, 20)));
  }, [saved]);

  const canSearch = useMemo(() => {
    return query.from.trim().length > 1 && query.to.trim().length > 1 && !!query.date && !!query.time && query.modes.length > 0;
  }, [query]);

  function toggleMode(mode: Mode) {
    setQuery((prev) => {
      const has = prev.modes.includes(mode);
      const nextModes = has ? prev.modes.filter((m) => m !== mode) : [...prev.modes, mode];
      return { ...prev, modes: nextModes };
    });
  }

  function pushRecent(q: JourneyQuery) {
    const item: StoredJourney = {
      ...q,
      id: toId(q),
      createdAt: Date.now(),
    };
    setRecents((prev) => {
      const withoutDupes = prev.filter((x) => x.id !== item.id);
      return [item, ...withoutDupes].slice(0, 10);
    });
  }

  function submitSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!canSearch) return;
    const cleaned: JourneyQuery = {
      ...query,
      from: query.from.trim(),
      to: query.to.trim(),
      modes: [...query.modes],
    };
    pushRecent(cleaned);
    router.push(buildResultsUrl(cleaned));
  }

  function runStored(j: StoredJourney) {
    const q: JourneyQuery = {
      from: j.from,
      to: j.to,
      date: j.date,
      time: j.time,
      modes: j.modes,
    };
    pushRecent(q);
    router.push(buildResultsUrl(q));
  }

  function saveCurrent() {
    if (!canSearch) return;
    setSaving(true);
    const cleaned: StoredJourney = {
      ...query,
      from: query.from.trim(),
      to: query.to.trim(),
      id: toId(query),
      createdAt: Date.now(),
      label: `${query.from.trim()} → ${query.to.trim()}`,
    };
    setSaved((prev) => {
      const withoutDupes = prev.filter((x) => x.id !== cleaned.id);
      return [cleaned, ...withoutDupes].slice(0, 20);
    });
    // small UI feedback without toasts
    setTimeout(() => setSaving(false), 400);
  }

  function removeSaved(id: string) {
    setSaved((prev) => prev.filter((x) => x.id !== id));
  }

  function clearRecents() {
    setRecents([]);
  }

  return (
    <div className="min-h-screen bg-neutral-50 text-neutral-900">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-neutral-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link href="/" className="flex items-center gap-2">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-neutral-900 text-white shadow-sm">
              <Icon name="map" />
            </div>
            <div className="leading-tight">
              <div className="text-sm font-extrabold tracking-tight">Regional Transport</div>
              <div className="text-xs text-neutral-600">Preston ↔ Lancaster region</div>
            </div>
          </Link>

          <nav className="flex items-center gap-2">
            <Link
              href="/live"
              className="rounded-xl px-3 py-2 text-sm font-semibold text-neutral-800 hover:bg-neutral-100"
            >
              Live map
            </Link>
            <Link
              href="/about"
              className="rounded-xl px-3 py-2 text-sm font-semibold text-neutral-800 hover:bg-neutral-100"
            >
              About
            </Link>
            <Link
              href="/help"
              className="rounded-xl px-3 py-2 text-sm font-semibold text-neutral-800 hover:bg-neutral-100"
            >
              Help
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <main className="mx-auto max-w-6xl px-4">
        <section className="grid gap-6 py-10 lg:grid-cols-12 lg:items-start">
          <div className="lg:col-span-7">
            <div className="inline-flex flex-wrap items-center gap-2">
              <Badge>
                <Icon name="spark" className="mr-1" />
                Multi-operator journeys
              </Badge>
              <Badge>
                <Icon name="clock" className="mr-1" />
                Live departures
              </Badge>
              <Badge>
                <Icon name="shield" className="mr-1" />
                Safer routing (hub-aware)
              </Badge>
            </div>

            <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-4xl">
              Plan reliably across bus, rail, and tram — in one place.
            </h1>

            <p className="mt-3 max-w-2xl text-base text-neutral-700">
              Search routes, see real-time running, and pick journeys that keep you connected — even when services slip.
            </p>

            <div className="mt-6 grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Icon name="search" /> Fast search
                </div>
                <div className="mt-1 text-sm text-neutral-600">Timetables + live feeds where available.</div>
              </div>
              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Icon name="map" /> Live map view
                </div>
                <div className="mt-1 text-sm text-neutral-600">Track vehicles and nearby stops.</div>
              </div>
              <div className="rounded-2xl border border-neutral-200 bg-white p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold">
                  <Icon name="star" /> Save favourites
                </div>
                <div className="mt-1 text-sm text-neutral-600">Pin common commutes for one-tap access.</div>
              </div>
            </div>
          </div>

          {/* Search card */}
          <div className="lg:col-span-5">
            <Card>
              <CardHeader
                title="Search a journey"
                subtitle="Choose a start, destination, time, and modes."
                icon={<Icon name="search" />}
              />
              <CardBody>
                <form onSubmit={submitSearch} className="grid gap-4">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input
                      label="From"
                      icon={<Icon name="pin" />}
                      placeholder="e.g. Lancaster University"
                      value={query.from}
                      onChange={(e) => setQuery((p) => ({ ...p, from: e.target.value }))}
                      autoComplete="off"
                      inputMode="text"
                    />
                    <Input
                      label="To"
                      icon={<Icon name="pin" />}
                      placeholder="e.g. Blackpool North"
                      value={query.to}
                      onChange={(e) => setQuery((p) => ({ ...p, to: e.target.value }))}
                      autoComplete="off"
                      inputMode="text"
                    />
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <Input
                      label="Date"
                      icon={<Icon name="clock" />}
                      type="date"
                      value={query.date}
                      onChange={(e) => setQuery((p) => ({ ...p, date: e.target.value }))}
                    />
                    <Input
                      label="Time"
                      icon={<Icon name="clock" />}
                      type="time"
                      value={query.time}
                      onChange={(e) => setQuery((p) => ({ ...p, time: e.target.value }))}
                    />
                  </div>

                  <div>
                    <div className="mb-1.5 text-xs font-semibold text-neutral-800">Modes</div>
                    <div className="flex flex-wrap gap-2">
                      <TogglePill active={query.modes.includes("bus")} onClick={() => toggleMode("bus")}>
                        Bus
                      </TogglePill>
                      <TogglePill active={query.modes.includes("rail")} onClick={() => toggleMode("rail")}>
                        Rail
                      </TogglePill>
                      <TogglePill active={query.modes.includes("tram")} onClick={() => toggleMode("tram")}>
                        Tram
                      </TogglePill>
                      <TogglePill active={query.modes.includes("road")} onClick={() => toggleMode("road")}>
                        Road
                      </TogglePill>
                    </div>
                    <div className="mt-2 text-xs text-neutral-600">
                      Selected: <span className="font-semibold text-neutral-800">{formatModes(query.modes)}</span>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2 pt-1">
                    <PrimaryButton type="submit" disabled={!canSearch} className="flex-1">
                      <Icon name="search" />
                      Search
                    </PrimaryButton>
                    <SecondaryButton onClick={saveCurrent} className="whitespace-nowrap" >
                      <Icon name="star" />
                      {saving ? "Saved" : "Save"}
                    </SecondaryButton>
                  </div>

                  <div className="text-xs text-neutral-600">
                    Tip: For live running, open the <Link className="font-semibold hover:underline" href="/live">Live map</Link>.
                  </div>
                </form>
              </CardBody>
            </Card>

            <div className="mt-4 rounded-2xl border border-neutral-200 bg-white p-4 text-sm text-neutral-700 shadow-sm">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 text-neutral-700">
                  <Icon name="shield" />
                </div>
                <div>
                  <div className="font-semibold">Reliability-first routing</div>
                  <div className="mt-1 text-neutral-600">
                    When possible, we prefer well-served hubs over risky remote connections — so you’re less likely to get stranded.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Recents + Saved */}
        <section className="grid gap-6 pb-12 lg:grid-cols-2">
          <Card>
            <CardHeader
              title="Recently searched"
              subtitle={recents.length ? "Tap any journey to search again." : "Your recent journeys will appear here."}
              icon={<Icon name="clock" />}
            />
            <CardBody>
              {recents.length ? (
                <div className="grid gap-2">
                  {recents.map((j) => (
                    <button
                      key={j.id}
                      type="button"
                      onClick={() => runStored(j)}
                      className="flex w-full items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-white px-3 py-3 text-left shadow-sm hover:bg-neutral-50"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-sm font-semibold text-neutral-900">
                          {j.from} <span className="text-neutral-400">→</span> {j.to}
                        </div>
                        <div className="mt-0.5 text-xs text-neutral-600">
                          {formatWhen(j.date, j.time)} · {formatModes(j.modes)}
                        </div>
                      </div>
                      <span className="shrink-0 rounded-xl bg-neutral-900 px-3 py-1.5 text-xs font-semibold text-white">
                        Search
                      </span>
                    </button>
                  ))}
                  <div className="pt-2">
                    <SecondaryButton onClick={clearRecents}>Clear recents</SecondaryButton>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-neutral-200 p-4 text-sm text-neutral-600">
                  No recent searches yet. Try searching a journey above.
                </div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title="Saved journeys"
              subtitle={saved.length ? "Keep your commutes one tap away." : "Save a journey from the search card."}
              icon={<Icon name="star" />}
            />
            <CardBody>
              {saved.length ? (
                <div className="grid gap-2">
                  {saved.map((j) => (
                    <div
                      key={j.id}
                      className="flex items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-white px-3 py-3 shadow-sm"
                    >
                      <button
                        type="button"
                        onClick={() => runStored(j)}
                        className="min-w-0 flex-1 text-left hover:opacity-90"
                      >
                        <div className="truncate text-sm font-semibold text-neutral-900">{j.label ?? `${j.from} → ${j.to}`}</div>
                        <div className="mt-0.5 text-xs text-neutral-600">
                          {formatWhen(j.date, j.time)} · {formatModes(j.modes)}
                        </div>
                      </button>
                      <div className="flex shrink-0 items-center gap-2">
                        <button
                          type="button"
                          onClick={() => runStored(j)}
                          className="rounded-xl bg-neutral-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-neutral-800"
                        >
                          Open
                        </button>
                        <button
                          type="button"
                          onClick={() => removeSaved(j.id)}
                          className="rounded-xl border border-neutral-200 bg-white px-3 py-1.5 text-xs font-semibold text-neutral-800 hover:bg-neutral-50"
                          aria-label={`Remove saved journey ${j.label ?? `${j.from} to ${j.to}`}`}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-neutral-200 p-4 text-sm text-neutral-600">
                  Nothing saved yet. Fill in a search and hit <span className="font-semibold">Save</span>.
                </div>
              )}
            </CardBody>
          </Card>
        </section>

        {/* CTA */}
        <section className="pb-16">
          <div className="rounded-3xl border border-neutral-200 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <div className="text-sm font-semibold text-neutral-700">Want the live view?</div>
                <div className="mt-1 text-2xl font-extrabold tracking-tight">See vehicles and departures on the map.</div>
                <div className="mt-2 max-w-2xl text-sm text-neutral-600">
                  Open the map to browse nearby stops, view next departures, and follow services in real time where available.
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link
                  href="/live"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-neutral-900 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-neutral-800"
                >
                  <Icon name="map" />
                  Open live map
                </Link>
                <Link
                  href="/results"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-neutral-200 bg-white px-4 py-2 text-sm font-semibold text-neutral-900 shadow-sm hover:bg-neutral-50"
                >
                  <Icon name="search" />
                  Browse results
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-200 bg-white">
        <div className="mx-auto max-w-6xl px-4 py-8">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="text-sm text-neutral-600">
              © {new Date().getFullYear()} Regional Transport — SCC.200 demo UI
            </div>
            <div className="flex flex-wrap gap-4 text-sm font-semibold text-neutral-800">
              <Link href="/accessibility" className="hover:underline">
                Accessibility
              </Link>
              <Link href="/privacy" className="hover:underline">
                Privacy
              </Link>
              <Link href="/status" className="hover:underline">
                Status
              </Link>
            </div>
          </div>
          <div className="mt-3 text-xs text-neutral-500">
            Data sources and feeds are provided for the SCC.200 project environment.
          </div>
        </div>
      </footer>
    </div>
  );
}