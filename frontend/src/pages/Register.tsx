import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { storage } from "../app/storage";
import { Music, UserPlus } from "lucide-react";

export function Register() {
  const nav = useNavigate();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const res = await api.register(userId.trim(), password);
      storage.setUserId(res.user_id);
      storage.setToken(res.access_token);
      nav("/"); // onboarding
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-screen text-white relative overflow-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950">
      {/* glow */}
      <div className="pointer-events-none fixed inset-0 opacity-40">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-emerald-500 blur-[120px]" />
        <div className="absolute top-40 -right-40 h-96 w-96 rounded-full bg-sky-500 blur-[140px]" />
      </div>

      {/* Center a bit lower */}
      <div className="relative min-h-screen flex items-start justify-center pt-24 px-6">
        <div className="w-full max-w-lg">
          {/* Cute title */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2">
              <Music className="h-4 w-4 text-emerald-200" />
              <span className="text-sm text-white/80">Spotify Recommender System</span>
            </div>
            <div className="mt-3 text-white/70 text-sm">
              Create an account to start your personalized music journey!
            </div>
          </div>

          <div className="rounded-[32px] border border-white/10 bg-white/5 backdrop-blur p-8 shadow-[0_20px_60px_-30px_rgba(0,0,0,0.9)]">
            <div className="flex items-center gap-3">
              <div className="h-11 w-11 rounded-2xl bg-white/5 border border-white/10 grid place-items-center">
                <UserPlus className="h-5 w-5 text-emerald-200" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-white/60">Authentication</div>
                <div className="text-2xl font-extrabold">Create account</div>
              </div>
            </div>

            <form className="mt-6 space-y-4" onSubmit={submit}>
              <div>
                <label className="text-sm font-medium text-white/80">Username</label>
                <input
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-400/30"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="username"
                  autoComplete="username"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-white/80">Password</label>
                <input
                  type="password"
                  className="mt-2 w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-400/30"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="****"
                  autoComplete="new-password"
                />
              </div>

              {err ? (
                <div className="rounded-2xl border border-red-300/20 bg-red-500/10 text-red-200 p-4 text-sm">
                  {err}
                </div>
              ) : null}

              <button
                disabled={busy || !userId.trim() || password.length < 4}
                className="w-full rounded-2xl bg-emerald-400 text-emerald-950 py-3.5 font-semibold hover:brightness-110 disabled:opacity-50 flex items-center justify-center gap-2"
                type="submit"
              >
                <UserPlus className="h-4 w-4" />
                {busy ? "Creating..." : "Register"}
              </button>

              <div className="text-sm text-white/60 text-center">
                Already have an account?{" "}
                <Link className="text-emerald-200 hover:text-emerald-100" to="/login">
                  Login
                </Link>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
