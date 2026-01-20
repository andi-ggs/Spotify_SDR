import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { storage } from "../app/storage";
import { Music, Sparkles, SlidersHorizontal } from "lucide-react";

const PRESET_GENRES = [
  "pop",
  "rock",
  "hip-hop",
  "electronic",
  "jazz",
  "classical",
  "country",
  "r-n-b",
  "metal",
  "world-music",
];

function Chip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={[
        "px-3 py-2 rounded-full border text-sm transition",
        active
          ? "bg-emerald-500/20 text-emerald-200 border-emerald-400/30"
          : "bg-white/5 text-white/80 border-white/10 hover:bg-white/10",
      ].join(" ")}
      type="button"
    >
      {label}
    </button>
  );
}

function Slider({
  label,
  value,
  setValue,
  hint,
  min = 0,
  max = 1,
  step = 0.01,
  format = (v: number) => v.toFixed(2),
}: {
  label: string;
  value: number;
  setValue: (v: number) => void;
  hint?: string;
  min?: number;
  max?: number;
  step?: number;
  format?: (v: number) => string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium text-white/80">{label}</label>
        <span className="text-xs text-emerald-200">{format(value)}</span>
      </div>
      <input
        type="range"
        className="mt-3 w-full accent-emerald-400"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => setValue(Number(e.target.value))}
      />
      {hint ? <div className="text-xs text-white/55 mt-1">{hint}</div> : null}
    </div>
  );
}

export function Onboarding() {
  const nav = useNavigate();

  const userId = storage.getUserId();
  const token = storage.getToken();

  useEffect(() => {
    if (!token || !userId) nav("/login");
  }, [token, userId, nav]);

  const [genres, setGenres] = useState<string[]>(["world-music"]);
  const [mood, setMood] = useState("happy");

  const [energy, setEnergy] = useState(0.65);
  const [dance, setDance] = useState(0.55);

  const [acoustic, setAcoustic] = useState(0.4);
  const [instrumental, setInstrumental] = useState(0.2);
  const [valence, setValence] = useState(0.55);
  const [speechiness, setSpeechiness] = useState(0.15);
  const [liveness, setLiveness] = useState(0.2);
  const [tempo, setTempo] = useState(120);

  const [extraGenre, setExtraGenre] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const genreChips = useMemo(() => Array.from(new Set(genres)), [genres]);

  async function submit() {
    if (!userId) return;

    setErr(null);
    setBusy(true);
    try {
      await api.setPrefs(userId, {
        preferred_genres: genreChips,
        mood,
        preferred_energy: energy,
        preferred_danceability: dance,
        preferred_acousticness: acoustic,
        preferred_instrumentalness: instrumental,
        preferred_valence: valence,
        preferred_speechiness: speechiness,
        preferred_liveness: liveness,
        preferred_tempo: tempo,
      });

      nav("/discover");
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-6">
      <div className="min-h-[calc(100vh-72px)] py-10 flex items-center">
        <div className="w-full grid lg:grid-cols-2 gap-8">
          {/* LEFT */}
          <div className="rounded-[28px] border border-white/10 bg-white/5 backdrop-blur p-7 shadow-[0_20px_60px_-30px_rgba(0,0,0,0.8)]">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs uppercase tracking-wider text-white/60">Onboarding</div>
                <h1 className="text-3xl md:text-4xl font-extrabold mt-2">Create your taste profile</h1>
                <p className="text-white/70 mt-2 max-w-xl">
                  Signed in as <span className="text-white/90 font-semibold">{userId ?? "-"}</span>. Set preferences to
                  start.
                </p>
              </div>

              <div className="hidden md:flex items-center gap-2 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 px-3 py-2">
                <Sparkles className="h-4 w-4 text-emerald-200" />
                <span className="text-sm text-emerald-100">Hybrid SR</span>
              </div>
            </div>

            <div className="mt-7 grid gap-6">
              <div>
                <label className="text-sm font-medium text-white/80">Preferred genres</label>
                <div className="mt-3 flex flex-wrap gap-2">
                  {PRESET_GENRES.map((g) => {
                    const active = genres.includes(g);
                    return (
                      <Chip
                        key={g}
                        label={g}
                        active={active}
                        onClick={() => setGenres((prev) => (active ? prev.filter((x) => x !== g) : [...prev, g]))}
                      />
                    );
                  })}
                </div>

                <div className="mt-3 flex gap-2">
                  <input
                    className="flex-1 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-400/30"
                    value={extraGenre}
                    onChange={(e) => setExtraGenre(e.target.value)}
                    placeholder="Add custom genre…"
                  />
                  <button
                    className="rounded-2xl border border-white/10 px-5 py-3 bg-white/5 hover:bg-white/10"
                    onClick={() => {
                      const g = extraGenre.trim();
                      if (!g) return;
                      setGenres((prev) => (prev.includes(g) ? prev : [...prev, g]));
                      setExtraGenre("");
                    }}
                    type="button"
                  >
                    Add
                  </button>
                </div>

                <div className="mt-2 text-xs text-white/60">
                  Selected: <span className="text-white/80">{genreChips.length ? genreChips.join(", ") : "none"}</span>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-5">
                <div>
                  <label className="text-sm font-medium text-white/80">Mood</label>
                  <select
                    className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3"
                    value={mood}
                    onChange={(e) => setMood(e.target.value)}
                  >
                    <option value="happy">happy</option>
                    <option value="sad">sad</option>
                    <option value="chill">chill</option>
                    <option value="energetic">energetic</option>
                    <option value="focus">focus</option>
                  </select>
                </div>

                <div className="md:col-span-2 grid sm:grid-cols-2 gap-4">
                  <Slider label="Energy" value={energy} setValue={setEnergy} hint="0 = calm, 1 = intense" />
                  <Slider label="Danceability" value={dance} setValue={setDance} hint="0 = low, 1 = high" />
                </div>
              </div>

              <div className="rounded-[24px] border border-white/10 bg-white/5 p-5">
                <div className="flex items-center gap-2">
                  <SlidersHorizontal className="h-4 w-4 text-emerald-200" />
                  <div className="font-semibold">Advanced audio preferences</div>
                </div>

                <div className="mt-4 grid md:grid-cols-2 gap-4">
                  <Slider label="Acousticness" value={acoustic} setValue={setAcoustic} />
                  <Slider label="Instrumentalness" value={instrumental} setValue={setInstrumental} />
                  <Slider label="Valence" value={valence} setValue={setValence} hint="0 = sad, 1 = happy" />
                  <Slider label="Speechiness" value={speechiness} setValue={setSpeechiness} />
                  <Slider label="Liveness" value={liveness} setValue={setLiveness} />
                  <Slider
                    label="Tempo"
                    value={tempo}
                    setValue={setTempo}
                    min={60}
                    max={200}
                    step={1}
                    format={(v) => `${Math.round(v)} BPM`}
                  />
                </div>
              </div>

              {err ? (
                <div className="rounded-2xl border border-red-300/20 bg-red-500/10 text-red-200 p-4 text-sm">
                  {err}
                </div>
              ) : null}

              <button
                disabled={busy}
                onClick={submit}
                className="rounded-2xl bg-emerald-400 text-emerald-950 py-3.5 font-semibold hover:brightness-110 disabled:opacity-50"
              >
                {busy ? "Saving..." : "Continue to Discover"}
              </button>
            </div>
          </div>

          {/* RIGHT */}
          <div className="rounded-[28px] border border-white/10 bg-gradient-to-br from-emerald-500/10 to-sky-500/10 backdrop-blur p-7 shadow-[0_20px_60px_-30px_rgba(0,0,0,0.8)]">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-2xl bg-white/5 border border-white/10 grid place-items-center">
                <Music className="h-5 w-5 text-emerald-200" />
              </div>
              <div>
                <div className="text-sm text-white/60">What’s new</div>
                <div className="text-xl font-bold">Audio-aware + listening-time aware</div>
              </div>
            </div>

            <div className="mt-6 grid gap-4">
              <div className="rounded-2xl border border-white/10 bg-black/15 p-5">
                <div className="font-semibold">Knowledge-based</div>
                <div className="text-sm text-white/70 mt-2">
                  Uses explicit preferences: genres, mood and audio features.
                </div>
              </div>

              <div className="rounded-2xl border border-white/10 bg-black/15 p-5">
                <div className="font-semibold">Hybrid personalization</div>
                <div className="text-sm text-white/70 mt-2">
                  Listening time + likes/dislikes build a learned taste profile (Profile page).
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
