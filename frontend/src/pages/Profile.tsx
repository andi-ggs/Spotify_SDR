import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { storage } from "../app/storage";
import { Panel } from "../components/Panel";
import { RefreshCw } from "lucide-react";

function badgeForInteraction(i: any) {
  if (i.event_type === "view") return "Viewed";
  if (i.event_type === "rating" && i.rating === 1) return "Liked";
  if (i.event_type === "rating" && i.rating === -1) return "Disliked";
  return i.event_type;
}

function MiniStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="text-xs text-white/50">{label}</div>
      <div className="text-xl font-extrabold text-white">{value}</div>
    </div>
  );
}

function TasteGrid({ u }: { u: any }) {
  const items: Array<[string, any]> = [
    ["Energy", u.taste_energy],
    ["Danceability", u.taste_danceability],
    ["Acousticness", u.taste_acousticness],
    ["Instrumental", u.taste_instrumentalness],
    ["Valence", u.taste_valence],
    ["Speechiness", u.taste_speechiness],
    ["Liveness", u.taste_liveness],
    ["Tempo", u.taste_tempo],
  ];

  const hasAny = items.some(([, v]) => v != null);

  return (
    <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
      <div className="font-semibold text-white">Learned taste profile (from likes)</div>
      <div className="text-sm text-white/60 mt-1">
        Weighted by listening ratio (longer listens influence the profile more).
      </div>

      {!hasAny ? (
        <div className="text-sm text-white/60 mt-3">
          No taste profile yet. Like a few tracks and record some listening time.
        </div>
      ) : (
        <div className="mt-4 grid grid-cols-2 gap-3">
          {items.map(([label, v]) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-3">
              <div className="text-xs text-white/50">{label}</div>
              <div className="font-semibold text-white/90">
                {v == null ? "-" : typeof v === "number" ? v.toFixed(2) : String(v)}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function Profile() {
  const nav = useNavigate();
  const userId = storage.getUserId();

  useEffect(() => {
    if (!userId) nav("/");
  }, [userId, nav]);

  const userQuery = useQuery({
    queryKey: ["user", userId],
    queryFn: () => api.getUser(userId as string),
    enabled: !!userId,
  });

  const interactionsQuery = useQuery({
    queryKey: ["interactions", userId],
    queryFn: () => api.getUserInteractions(userId as string),
    enabled: !!userId,
  });

  const interactions = interactionsQuery.data?.interactions || [];

  const likes = interactions.filter((x: any) => x.event_type === "rating" && x.rating === 1).length;
  const dislikes = interactions.filter((x: any) => x.event_type === "rating" && x.rating === -1).length;
  const views = interactions.filter((x: any) => x.event_type === "view").length;

  const avgListenSec = userQuery.data?.avg_listen_seconds ?? null;
  const avgListenRatio = userQuery.data?.avg_listen_ratio ?? null;

  return (
    <div className="mx-auto max-w-7xl px-6">
      <div className="min-h-[calc(100vh-72px)] py-10">
        <div className="text-xs uppercase tracking-wider text-white/60">Profile</div>
        <h1 className="text-3xl md:text-4xl font-extrabold mt-2 text-white">User model</h1>
        <p className="text-white/70 mt-2 max-w-3xl">
          Explicit preferences + implicit feedback (listening time + likes/dislikes). This is your rubric page.
        </p>

        <div className="mt-7 grid lg:grid-cols-2 gap-6">
          <Panel
            title="Explicit preferences"
            right={
              <button
                className="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-3 py-2 text-sm text-white/85 flex items-center gap-2"
                onClick={() => userQuery.refetch()}
                type="button"
              >
                <RefreshCw className="h-4 w-4" /> Refresh
              </button>
            }
          >
            <div className="rounded-2xl border border-white/10 bg-black/15 p-4">
              {userQuery.isLoading ? (
                <div className="text-sm text-white/60">Loading...</div>
              ) : userQuery.data ? (
                <div className="space-y-2 text-sm text-white/75">
                  <div>
                    <span className="text-white/50">User ID:</span>{" "}
                    <b className="text-white/85">{userQuery.data.user_id}</b>
                  </div>
                  <div>
                    <span className="text-white/50">Mood:</span>{" "}
                    <b className="text-white/85">{userQuery.data.mood ?? "-"}</b>
                  </div>
                  <div>
                    <span className="text-white/50">Preferred genres:</span>{" "}
                    <b className="text-white/85">
                      {(userQuery.data.preferred_genres || []).length
                        ? (userQuery.data.preferred_genres || []).join(", ")
                        : "-"}
                    </b>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Energy</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_energy ?? "-"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Danceability</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_danceability ?? "-"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Acousticness</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_acousticness ?? "-"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Valence</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_valence ?? "-"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Instrumental</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_instrumentalness ?? "-"}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div className="text-xs text-white/50">Tempo</div>
                      <div className="font-semibold text-white/90">
                        {userQuery.data.preferred_tempo ?? "-"}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-white/60">No user data.</div>
              )}
            </div>

            {userQuery.data ? <div className="mt-4"><TasteGrid u={userQuery.data} /></div> : null}
          </Panel>

          <Panel
            title="Implicit feedback"
            subtitle="Views track listening time and likes/dislikes."
            right={
              <button
                className="rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 px-3 py-2 text-sm text-white/85 flex items-center gap-2"
                onClick={() => interactionsQuery.refetch()}
                type="button"
              >
                <RefreshCw className="h-4 w-4" /> Refresh
              </button>
            }
          >
            <div className="grid grid-cols-3 gap-3">
              <MiniStat label="Views" value={String(views)} />
              <div className="rounded-2xl border border-emerald-400/25 bg-emerald-500/10 p-3">
                <div className="text-xs text-emerald-100/70">Likes</div>
                <div className="text-xl font-extrabold text-emerald-100">{likes}</div>
              </div>
              <div className="rounded-2xl border border-red-300/20 bg-red-500/10 p-3">
                <div className="text-xs text-red-100/70">Dislikes</div>
                <div className="text-xl font-extrabold text-red-100">{dislikes}</div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3">
              <MiniStat
                label="Avg listen (sec)"
                value={avgListenSec == null ? "-" : Number(avgListenSec).toFixed(1)}
              />
              <MiniStat
                label="Avg listen ratio"
                value={avgListenRatio == null ? "-" : Number(avgListenRatio).toFixed(2)}
              />
            </div>

            <div className="mt-5 space-y-2">
              {interactionsQuery.isLoading ? (
                <div className="text-sm text-white/60">Loading interactions...</div>
              ) : interactions.length ? (
                interactions.slice(0, 20).map((i: any) => (
                  <div
                    key={i.id}
                    className="rounded-2xl border border-white/10 bg-white/5 p-3 flex items-start justify-between gap-3"
                  >
                    <div className="min-w-0">
                      <div className="font-medium truncate text-white/90">{i.track.track_name}</div>
                      <div className="text-xs text-white/55 truncate">{i.track.artists}</div>
                      <div className="text-xs text-white/40 mt-1 truncate">
                        {i.created_at}
                        {i.event_type === "view" && i.duration_ms != null
                          ? ` • listened ${Math.round(i.duration_ms / 1000)}s`
                          : ""}
                      </div>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full border border-white/10 bg-black/15 text-white/70">
                      {badgeForInteraction(i)}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-sm text-white/60">
                  No interactions yet. Go to Discover and record listening time + likes/dislikes.
                </div>
              )}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}
