# NetworkIt — Phase 1 backend

A real backend for the NetworkIt prototype, built on Supabase (Postgres + Auth + Storage + Realtime) with a static frontend deployable to Vercel.

The original file (`networkit-platform_4.html`) faked its entire backend with `localStorage` — plaintext passwords, privacy toggles enforced only by hiding fields in the renderer (the data was already in the browser regardless), fake online status, and an admin panel with zero authorization. None of that ships here. See **"What changed and why"** below for specifics.

## What's in this folder

```
supabase/
  migrations/0001_init.sql      → full schema, RLS policies, masking functions
  functions/delete-account/     → Edge Function for hard account deletion
web/
  index.html                    → the original UI, rewired to call Supabase
  app.js                        → all frontend logic (replaces the old DB.g/DB.s shim)
  config.example.js             → copy to config.js and fill in your project keys
```

## Scope: Phase 1 vs Phase 2

**Built now:** email/password auth (+ optional Google OAuth), 8-step registration, profile CRUD with avatar upload, discover/search with filters, saved/bookmarked profiles, 1:1 real-time messaging with seen receipts, profile reporting (write-only), account settings (name/username/password/email/delete).

**Deliberately deferred — not wired to anything, nav items hidden:**
- **Admin panel** (ban/remove users, review reports). Needs real role-based authorization and service-role Edge Functions for destructive actions; the original had zero authorization on this (any logged-in user could call the ban function from devtools).
- **Notifications** (message alerts, profile-view alerts, "smart" weekly digest/reminder checks). Needs its own event pipeline (likely Postgres triggers → a notifications table + realtime, or a scheduled Edge Function for digests).
- **Real online/presence status.** The original faked this with a per-browser `localStorage` timestamp, which never reflected any other user's actual state. Supabase Presence would do this correctly; not built here.
- **Profile-view tracking, profile-completeness widget, "People like you" suggestions.** Worth knowing: these were already dead code in the original — defined but never called from anywhere reachable in the UI — so nothing was lost by not porting them.
- **Phone verification.** The registration form and FAQ both implied phone numbers are verified. They aren't — the original just stored the number, and this build does the same (kept private, never exposed, but not verified). Real verification means an SMS OTP provider (Twilio Verify, etc.). Either build that or fix the FAQ copy — right now it's a claim the product doesn't back up.

## Setup

### 1. Create a Supabase project
[supabase.com/dashboard](https://supabase.com/dashboard) → New project. Note your project URL and **anon/public** API key (Project Settings → API) — never the `service_role` key, that one stays server-side only.

### 2. Run the migration
Easiest path: paste the contents of `supabase/migrations/0001_init.sql` into the Supabase Dashboard's SQL Editor and run it.
Or, with the Supabase CLI: `supabase link --project-ref YOUR_REF && supabase db push`.

### 3. Auth settings
Dashboard → Authentication → Providers → Email. For Phase 1's zero-friction registration flow (matching the original prototype's UX), turn **off** "Confirm email". If you'd rather have real email verification, leave it on — registration will then tell the user to check their email instead of logging them in immediately (`rFinish()` in `app.js` already handles both cases).

If you want the "Continue with Google" button to work: Authentication → Providers → Google, and follow Supabase's OAuth setup guide.

### 4. Deploy the delete-account Edge Function
```
supabase functions deploy delete-account
```
This is the only place the `service_role` key is used, and it never leaves Supabase's servers — the function reads it from its own environment (`SUPABASE_SERVICE_ROLE_KEY`, set automatically by Supabase for Edge Functions).

### 5. Configure the frontend
```
cp web/config.example.js web/config.js
```
Fill in your project URL + anon key. `config.js` is the only file with project-specific values — don't commit it if `SUPABASE_ANON_KEY` bothers you being in git history (it's safe to expose publicly, RLS is what actually protects data, but some teams prefer to keep it out of version control anyway).

### 6. Run locally
Any static file server works, e.g.:
```
cd web && python3 -m http.server 8080
```
Then open `http://localhost:8080`.

### 7. Deploy
Push the `web/` folder to Vercel (or Netlify, or any static host) as-is — no build step. In Vercel: New Project → point it at this repo → set the root directory to `web/`.

## What changed and why (beyond "added a backend")

- **Passwords**: were stored in plaintext and compared with `===`. Now handled entirely by Supabase Auth (bcrypt-hashed, never touches your database in plaintext).
- **Privacy toggles** (hide location/university/socials/join date, appear-in-search): were enforced by the *client* choosing not to render fields it already had. Now enforced by Postgres — other users' rows aren't even selectable directly (RLS restricts `profiles` to `auth.uid() = id`); the only way to read someone else's data is through `SECURITY DEFINER` functions that null out hidden fields *before* the response leaves the database.
- **Phone number**: was "never shown publicly" by convention only (client code just didn't render it, but the field was sitting in the same object as everything else). Now it's structurally impossible for another user's client to receive it — it's not present in any of the masked functions.
- **Password reset**: the original told you outright whether an email address had an account ("Reset link sent" vs "No account found") — classic account-enumeration leak. Fixed to always show the same message regardless.
- **Admin actions** (`admBan`, `admDel`, etc.): had no authorization at all — any logged-in user's browser console could call them. Removed from Phase 1 rather than ship them insecurely; rebuild properly in Phase 2 with real role checks.
- **Discover status filter**: the dropdown offered options ("High School Student", "Gap Year", etc.) that no registration path could ever actually produce (registration only ever sets `Student` or `Professional`), so filtering by them silently returned zero results. Fixed to match reality.
- **Messaging "seen" ticks / typing feel**: was simulated with `setInterval(...,3000)` polling against the *same browser's* localStorage — it never actually talked to another user's client. Now backed by Postgres row updates + Supabase Realtime, so it reflects what actually happened.
- **Avatars**: were base64-encoded and stuffed into `localStorage`, which caps out around 5–10MB per origin — a few photos would have broken the app. Now uploaded to Supabase Storage, referenced by URL.
- **Account deletion**: previously just filtered the fake in-memory array. Real deletion requires the `service_role` key (to delete the actual auth account), which is why it's now a dedicated Edge Function rather than something the browser can do directly.

## A note on the file itself

The original 3,000-line file had accumulated real drift — duplicate implementations of the same feature under different names, some wired into the UI and some fully dead (e.g. `saveAccSettings` vs. the actually-used `saveStAcc`; a profile-completeness/onboarding-checklist system that was fully built but never called). This rewrite used the HTML markup's actual `onclick`/`oninput` attributes as the source of truth for which function names had to exist, not the JS file's internal consistency — so the dead paths were dropped rather than ported forward.
