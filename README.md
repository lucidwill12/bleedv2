# Pulse — a bleed-style Discord bot

A self-hosted multipurpose bot that follows bleed's commands and syntax: `,` prefix, ✅ ⚠️ ❌ replies, 👍 on moderation actions, `--flags`, and `{embed}$v{...}` embed scripting with `{user.mention}`-style variables.

**27 modules · ~390 commands.** Type `,help` in Discord to browse them all, or `,help <command>` for usage and required permissions.

---

## Updating from the first version

1. Stop the bot (**Ctrl + C** in its window).
2. Copy your **`.env`** file and the **`data`** folder out of the old `bot` folder. They hold your token and saved settings.
3. Delete the old `bot` folder, unzip the new one in its place, and put `.env` and `data` back inside it.
4. In the `bot` folder run `python -m pip install -r requirements.txt`, then `python main.py`.

## First-time setup

1. https://discord.com/developers/applications → your app → **Bot**:
   - **Reset Token** and copy it.
   - Turn on all three **Privileged Gateway Intents**.
2. Install Python 3.10+ from python.org, ticking **"Add python.exe to PATH"**.
3. In this folder:
   ```
   copy .env.example .env
   notepad .env              (paste your token, set BOT_NAME)
   python -m pip install -r requirements.txt
   python main.py
   ```
4. Invite it: OAuth2 → URL Generator → scope **bot** → permission **Administrator** → open the link.
5. **Server Settings → Roles**: drag the bot's role to the **top**.

The bot only runs while that window is open. For 24/7 uptime, run it on a VPS or always-on PC.

---

## Recommended first commands

| What | Command |
|---|---|
| Jail system + case log channel | `,setup` |
| Mute roles | `,setupmute` |
| Where mod actions are logged | `,settings modlog #mod-logs` |
| Mark staff roles | `,bind staff @Moderators` |
| Antinuke | `,antinuke ban on --threshold 3 --do stripstaff` (repeat for `kick`, `role`, `channel`, `emoji`, `webhook`, `botadd`, `vanity`) |
| Antiraid | `,antiraid massjoin on --threshold 7 --do kick --lock true` |
| Welcome message | `,welcome add #welcome {embed}$v{description: Welcome {user.mention} to **{guild.name}**!}$v{color: #2b2d31}` |
| Join-to-create voice | `,voicemaster setup` |
| Levels | `,levels unlock` |
| Starboard | `,starboard set #starboard` then `,starboard unlock` |
| Logging | `,log add #logs` |
| Tickets | `,tickets panel add support #tickets buttons` → `,tickets options add support Support 🎫` → `,tickets resend support` |

## Modules

| Category | Highlights |
|---|---|
| **Moderation** | ban, tempban, softban, hardban, unbanall, kick, timeout, jail, mute/imute/rmute, warn/warnings, purge (+ 17 filters), lock/lockdown, hide/reveal, nuke, slowmode, role (+ create/color/icon/all/restore), nick/forcenickname, history/case/reason, drag/moveall, `,invoke` custom responses & DMs |
| **Antinuke** | ban, kick, role, channel, emoji, webhook, botadd and vanity protection with `--threshold`, `--do`, `--command`; whitelist, admins, monitored permissions; reverts damage |
| **Antiraid** | massjoin, no-avatar, account-age filters; raid state; `,recentban`, `,raid` |
| **Honeypot** · **Fake Permissions** | trap channels; give roles bot-only permissions |
| **Tickets** | panels (buttons/dropdown), options, forms (modals), claim, close, reopen, transcripts, trainees, blacklist, stats |
| **Roles** | booster roles, button roles, reaction roles, vanity (status) roles, autorole |
| **Messages** | welcome/goodbye/boost, autoresponders (+flags, roles, exclusive), auto messages (timers), bump reminder, reaction triggers, command aliases |
| **Embeds** · **Webhooks** | `,createembed`, `,embed edit/copy`; webhook create/send/edit |
| **Starboard** · **Clownboard** · **Levels** · **Giveaways** · **Counters** · **Logging** · **VoiceMaster** | as in bleed |
| **Utility** | snipe/editsnipe/reactionsnipe, afk, avatar/banner, userinfo/serverinfo, steal emoji, poll, and more |

## Web dashboard
The bot includes a website where server admins log in with Discord and change every module's settings, with live embed previews. Setup, including putting it on your own domain, is in **DASHBOARD.md**. `,dashboard` in Discord posts the link.

## Embed scripting

```
{embed}$v{title: Hi {user.name}}$v{description: Welcome!}$v{color: #ff6464}$v{thumbnail: {user.avatar}}$v{field: Members && {guild.count} && inline}$v{footer: {guild.name}}$v{button: link && Website && https://example.com}$v{message: {user.mention}}
```
Keys: `message, title, description, color, url, image, thumbnail, timestamp, author (name && icon && url), field (name && value && inline), footer (text && icon), button (type && label && url/emoji && disabled)`.
Run `,embed variables` for the variable list, and `,embed copy <message link>` to turn any message into a script.

## Not included
These bleed features need outside accounts, API keys or audio servers: Spotify, Last.fm, Fortnite, social notifications (Twitch/YouTube/etc.), music.

## Files
- `.env`: your token and settings. **Never share it.**
- `data/bot.db`: all saved server settings. Back it up.
