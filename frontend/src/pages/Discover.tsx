import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { storage } from "../app/storage";
import { TrackCard } from "../components/TrackCard";
import { Panel } from "../components/Panel";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";

export function Discover() {
  const nav = useNavigate();
  const userId = storage.getUserId();

  const [q, setQ] = useState("");
  const [page, setPage] = useState(0);
  const limit = 12;

  const [selectedTrack, setSelectedTrack] = useState<any | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    if (!userId) nav("/");
  }, [userId, nav]);

  const offset = page * limit;

  const tracksQuery = useQuery({
    queryKey: ["tracks", q, page],
    queryFn: () => api.listTracks(q || undefined, limit, offset),
    enabled: !!userId,
  });

  const items = tracksQuery.data?.items ?? [];

  const header = useMemo(() => {
    if (selectedTrack) return `Selected: ${selectedTrack.track_name}`;
    return "Discover tracks";
  }, [selectedTrack]);

  async function sendView(track: any, durationMs: number) {
    if (!userId) return;
    setStatus(null);
    try {
      await api.eventView({
        user_id: userId,
        track_id: track.track_id,
        duration_ms: durationMs,
        recomm_id: null,
      });
      setStatus(`View recorded (${track.track_name}, ${Math.round(durationMs / 1000)}s)`);
    } catch (e: any) {
      setStatus(e.message || String(e));
    }
  }

  async function sendRating(track: any, rating: 1 | -1) {
    if (!userId) return;
    setStatus(null);
    try {
      await api.eventRating({
        user_id: userId,
        track_id: track.track_id,
        rating,
        recomm_id: null,
      });
      setStatus(`${rating === 1 ? "Like" : "Dislike"} recorded (${track.track_name})`);
    } catch (e: any) {
      setStatus(e.message || String(e));
    }
  }

  return (
    <div className="mx-auto max-w-7xl px-6">
      <div className="min-h-[calc(100vh-72px)] py-10">
        <div className="text-xs uppercase tracking-wider text-white/60">Discover</div>
        <h1 className="text-3xl md:text-4xl font-extrabold mt-2 text-white">{header}</h1>
        <p className="text-white/70 mt-2 max-w-2xl">
          Browse the catalog, select tracks, and interact (view/like/dislike). This trains the hybrid recommender.
        </p>

        <div className="mt-7">
          <Panel
            title="Catalog"
            subtitle="Search by track, artist, or album. Paginated list."
            right={
              <div className="text-sm text-white/60">
                {tracksQuery.isLoading ? "Loading..." : `Page ${page + 1}`}
              </div>
            }
          >
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/50" />
                <input
                  value={q}
                  onChange={(e) => {
                    setQ(e.target.value);
                    setPage(0);
                  }}
                  placeholder="Search..."
                  className="w-full rounded-2xl border border-white/10 bg-black/20 px-11 py-3 outline-none focus:ring-2 focus:ring-emerald-400/30 text-white placeholder:text-white/40"
                />
              </div>
              <button
                onClick={() => {
                  setQ("");
                  setPage(0);
                }}
                className="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-3 text-white/80"
                type="button"
              >
                Clear
              </button>
            </div>

            {status ? (
              <div
                className={[
                  "mt-4 rounded-2xl border p-3 text-sm",
                  status.includes("recorded")
                    ? "border-emerald-400/25 bg-emerald-500/10 text-emerald-100"
                    : "border-red-300/20 bg-red-500/10 text-red-200",
                ].join(" ")}
              >
                {status}
              </div>
            ) : null}

            <div className="mt-5 grid md:grid-cols-2 gap-4">
              {items.map((t) => (
                <TrackCard
                  key={t.track_id}
                  track={t}
                  selected={selectedTrack?.track_id === t.track_id}
                  onSelect={() => {
                    setSelectedTrack(t);
                    storage.setLastTrackId(t.track_id);
                  }}
                  onView={(ms) => sendView(t, ms)}
                  onLike={() => sendRating(t, 1)}
                  onDislike={() => sendRating(t, -1)}
                />
              ))}
            </div>

            <div className="mt-6 flex items-center justify-between">
              <button
                className="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-2 text-white/80 flex items-center gap-2 disabled:opacity-40"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                type="button"
              >
                <ChevronLeft className="h-4 w-4" /> Prev
              </button>

              <div className="text-xs text-white/50">
                Tip: select a track here, then go to Recommendations → “Similar to selected”.
              </div>

              <button
                className="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-4 py-2 text-white/80 flex items-center gap-2 disabled:opacity-40"
                onClick={() => setPage((p) => p + 1)}
                disabled={items.length < limit}
                type="button"
              >
                Next <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
