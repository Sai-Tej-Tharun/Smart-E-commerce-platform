# frontend — React storefront (GlowVeda)

A Vite + React storefront for the Smart E-Commerce Platform, styled with the
GlowVeda organic-skincare design system. Talks to `fastapi_backend` for
auth, products, and cart.

## Pages
- `/` — home / featured products
- `/products`, `/products/:id` — catalog + product detail
- `/login`, `/register` — email/password + Auth0 social login (Google, Facebook)
- `/cart` — requires login
- `/admin/products` — requires the `admin` role; create/delete products

## Setup
```
cd frontend
npm install
cp .env.example .env      # edit if your backend isn't on 127.0.0.1:8000
npm run dev                # http://localhost:5173
```

Make sure `fastapi_backend` is running first (`uvicorn main:app --reload`)
and that its `.env` has `CORS_ORIGINS=http://localhost:5173` so the browser
is allowed to call it.

## Auth0 social login
Social buttons are disabled with a tooltip until you set
`VITE_AUTH0_DOMAIN` and `VITE_AUTH0_CLIENT_ID` in `.env` (see the Screenshot
Guide, Part C, for how to set up a free Auth0 tenant). Once set, "Continue
with Google/Facebook" opens Auth0's hosted login, then this app exchanges
the resulting ID token for its own JWT pair via `POST /auth/social`.
