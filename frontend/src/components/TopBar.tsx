import { NavLink, useNavigate } from "react-router-dom";
import { storage } from "../app/storage";

function Tab({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        [
          "px-3 py-2 rounded-2xl text-sm border transition",
          isActive
            ? "bg-emerald-500/15 border-emerald-400/25 text-emerald-200"
            : "bg-white/5 border-white/10 text-white/75 hover:bg-white/10",
        ].join(" ")
      }
    >
      {label}
    </NavLink>
  );
}

export function TopBar() {
  const nav = useNavigate();
  const userId = storage.getUserId();
  const token = storage.getToken();

  const loggedIn = !!userId && !!token;

  function logout() {
    storage.clearAuth();
    nav("/login");
  }

  return (
    <div className="sticky top-0 z-10 border-b border-white/10 bg-black/30 backdrop-blur">
      <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-emerald-500/15 border border-emerald-400/30 grid place-items-center font-extrabold text-emerald-300">
            SR
          </div>
          <div>
            <div className="font-semibold leading-tight">Spotify Recommender</div>
          </div>
        </div>

        <div className="hidden md:flex items-center gap-2">
          <Tab to="/discover" label="Discover" />
          <Tab to="/recommendations" label="Recommendations" />
          <Tab to="/profile" label="Profile" />
        </div>

        <div className="text-sm flex items-center gap-2">
          {loggedIn ? (
            <>
              <span className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10">
                User: <b className="text-emerald-200">{userId}</b>
              </span>

              <button
                onClick={logout}
                className="px-3 py-1.5 rounded-full bg-red-500/10 border border-red-300/20 text-red-200 hover:bg-red-500/15 transition"
                type="button"
                title="Logout"
              >
                Logout
              </button>
            </>
          ) : (
            <span className="px-3 py-1.5 rounded-full bg-amber-500/10 border border-amber-300/20 text-amber-200">
              Not logged in
            </span>
          )}
        </div>
      </div>

      {/* mobile tabs */}
      <div className="md:hidden px-6 pb-4 flex gap-2">
        <Tab to="/discover" label="Discover" />
        <Tab to="/recommendations" label="Recs" />
        <Tab to="/profile" label="Profile" />
      </div>
    </div>
  );
}
