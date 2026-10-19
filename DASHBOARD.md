# Web dashboard setup

The dashboard runs **inside the bot**. Whenever `python main.py` is running, the website is running too, on port 8080 of that computer. To make it public at `https://dash.defeataboss.com`, you connect your domain to that port with a free **Cloudflare Tunnel**. You don't need port forwarding or a separate web host.

Anyone with **Manage Server** in a server can log in with Discord and change that server's settings. Owner-only parts (antinuke admins, fake permissions) stay owner-only, and every change is listed under **Dashboard activity** on the overview page.

---

## 1. Discord Developer Portal

1. https://discord.com/developers/applications → your bot's application → **OAuth2**.
2. Copy the **Client ID**.
3. Under **Client Secret**, click **Reset Secret** and copy it. Treat it like your bot token and never share it.
4. Under **Redirects**, click **Add Redirect** and enter exactly:
   ```
   https://dash.defeataboss.com/callback
   ```
   To test on your own PC first, also add `http://localhost:8080/callback`.
5. **Save Changes**.

## 2. Add the settings to `.env`

Open `.env` in Notepad (`notepad .env`) and add these lines below your token:

```
DISCORD_CLIENT_ID=paste-client-id-here
DISCORD_CLIENT_SECRET=paste-client-secret-here
DASHBOARD_URL=https://dash.defeataboss.com
DASHBOARD_PORT=8080
```

Restart the bot. The window should show `Dashboard running on http://127.0.0.1:8080`.

**Quick local test (optional):** set `DASHBOARD_URL=http://localhost:8080`, restart, and open http://localhost:8080 in your browser. Change it back to the https address afterwards.

## 3. Put it on your domain with Cloudflare Tunnel (free)

Your domain's DNS needs to be managed by Cloudflare. If `defeataboss.com` isn't on Cloudflare yet:

1. Create a free account at https://dash.cloudflare.com.
2. Click **Add a domain** and enter `defeataboss.com`.
3. Cloudflare gives you two nameservers. Set those at the company where you bought the domain, and wait for Cloudflare to show the domain as **Active** (usually under an hour).

Then create the tunnel:

1. Cloudflare dashboard → **Zero Trust** → **Networks** → **Tunnels** → **Create a tunnel** → **Cloudflared**, and name it `pulse-dashboard`.
2. Pick **Windows**. Cloudflare shows an install command that starts with `cloudflared.exe service install …`.
   - Download and install cloudflared from the link on that page.
   - Open **Command Prompt as Administrator** (Start → type `cmd` → right-click → *Run as administrator*).
   - Paste and run the command.

   The tunnel now starts automatically with Windows.
3. Click **Next** and add a **Public Hostname**:
   - Subdomain: `dash`
   - Domain: `defeataboss.com`
   - Type: `HTTP`
   - URL: `localhost:8080`
4. **Save tunnel**.

Open **https://dash.defeataboss.com**, click **Log in with Discord**, and pick your server.

In Discord, `,dashboard` posts the link.

---

## Things to know

- **The site is only up while the bot is running.** If your PC sleeps or the bot window closes, the dashboard goes offline with it. For 24/7 uptime, run the bot and cloudflared on an always-on machine or a small VPS, using the same steps.
- **Turning it off:** add `DASHBOARD_ENABLED=false` to `.env`.
- **Port already in use:** change `DASHBOARD_PORT` (e.g. `8090`) and use the same port in the tunnel's URL.
- **"Discord login failed":** the redirect in step 1 must match `DASHBOARD_URL` + `/callback` exactly, and the client secret must be the latest one you reset.
- **Login sessions** last 7 days. Logging out ends the session immediately.
- **Security:**
  - The dashboard only listens on your own computer (`127.0.0.1`), so it can only be reached through your tunnel.
  - Every request is checked against the person's live permissions in Discord.
  - Changes are only accepted from your own site.
