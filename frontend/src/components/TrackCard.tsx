import { Sparkles, ThumbsDown, ThumbsUp } from "lucide-react";

type Props = {
  track: any;
  selected?: boolean;
  badge?: string;
  onSelect?: () => void;

  // change: onView takes duration_ms
  onView?: (durationMs: number) => void;
  onLike?: () => void;
  onDislike?: () => void;
};

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[11px] text-white/70">
      <span className="text-white/50">{label}:</span> <span className="text-white/80">{value}</span>
    </span>
  );
}

function listenLabel(ms: number) {
  if (ms >= 1_000_000) return "Full";
  return `${Math.round(ms / 1000)}s`;
}

export function TrackCard({ track, selected, badge, onSelect, onView, onLike, onDislike }: Props) {
  const fullMs =
    typeof track.duration_ms === "number" && track.duration_ms > 0
      ? Math.min(track.duration_ms, 240_000) // cap full at 4min for demo
      : 60_000;

  const options = [10_000, 30_000, fullMs];

  return (
    <div
      className={[
        "group rounded-3xl border p-4 transition shadow-[0_10px_30px_-20px_rgba(0,0,0,0.9)]",
        "bg-white/5 border-white/10 hover:bg-white/7 hover:border-white/15",
        selected ? "ring-2 ring-emerald-400/25 border-emerald-300/30 bg-emerald-500/10" : "",
      ].join(" ")}
      onClick={onSelect}
      role="button"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-semibold text-white break-words whitespace-normal">
            {track.track_name}
          </div>
          <div className="text-sm text-white/70 break-words whitespace-normal">
            {track.artists}
          </div>
          <div className="text-xs text-white/50 break-words whitespace-normal">
            {track.album_name} • {track.track_genre}
          </div>
        </div>

        {badge ? (
          <span className="text-xs px-2.5 py-1.5 rounded-full bg-emerald-500/15 border border-emerald-400/25 text-emerald-200 flex items-center gap-1">
            <Sparkles className="h-3.5 w-3.5" /> {badge}
          </span>
        ) : null}
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <StatPill label="Popularity" value={track.popularity != null ? String(track.popularity) : "-"} />
        {track.energy != null ? <StatPill label="Energy" value={Number(track.energy).toFixed(2)} /> : null}
        {track.danceability != null ? <StatPill label="Dance" value={Number(track.danceability).toFixed(2)} /> : null}
        {track.valence != null ? <StatPill label="Valence" value={Number(track.valence).toFixed(2)} /> : null}
        {track.acousticness != null ? <StatPill label="Acoustic" value={Number(track.acousticness).toFixed(2)} /> : null}
      </div>

      <div className="mt-4 flex flex-col gap-3">
        {/* Listen buttons */}
        <div className="flex items-center justify-between gap-2">
          <div className="text-[11px] text-white/50">
            Listen time (affects avg listening stats)
          </div>
          <div className="flex gap-2">
            {options.map((ms) => (
              <button
                key={ms}
                className="px-3 py-2 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 text-sm text-white/85"
                onClick={(e) => {
                  e.stopPropagation();
                  onView?.(ms);
                }}
                type="button"
                title={`Record view: ${listenLabel(ms)}`}
              >
                {listenLabel(ms)}
              </button>
            ))}
          </div>
        </div>

        {/* Like/Dislike */}
        <div className="flex items-center justify-between gap-2">
          <div className="text-[11px] text-white/50">
            {track.explicit ? "Explicit" : "Clean"} •{" "}
            {track.duration_ms ? `${Math.round(track.duration_ms / 1000)}s` : "-"}
          </div>

          <div className="flex items-center gap-2">
            <button
              className="px-3 py-2 rounded-2xl border border-emerald-400/25 bg-emerald-500/15 hover:bg-emerald-500/20 text-sm flex items-center gap-1"
              onClick={(e) => {
                e.stopPropagation();
                onLike?.();
              }}
              type="button"
              title="Like"
            >
              <ThumbsUp className="h-4 w-4 text-emerald-200" />{" "}
              <span className="text-emerald-100">Like</span>
            </button>

            <button
              className="px-3 py-2 rounded-2xl border border-red-300/20 bg-red-500/10 hover:bg-red-500/15 text-sm flex items-center gap-1"
              onClick={(e) => {
                e.stopPropagation();
                onDislike?.();
              }}
              type="button"
              title="Dislike"
            >
              <ThumbsDown className="h-4 w-4 text-red-200" />{" "}
              <span className="text-red-100">Dislike</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
