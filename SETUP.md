# Midnight Aurora profile: setup

## 1. Fill in your details
Open `profile.json` and replace every placeholder: username, name, roles, tagline, links, about, highlights, projects, skills, certifications.
Leave a link empty (`""`) and its badge disappears. Delete the `certifications` list and that section disappears.

- **Photo:** `"avatar": "auto"` embeds your current GitHub profile photo in the hero. You can also put an image next to `profile.json` (for example `avatar.jpg`) and set `"avatar": "avatar.jpg"`.
- **Colors:** change any value in `"theme"`. Every SVG, badge and stats card follows it.

## 2. Build
```powershell
python build.py
```
To check the result, open `preview.html` through a local server: `python -m http.server`, then go to http://localhost:8000/preview.html.

## 3. Publish
1. On GitHub, create a **public** repository named **exactly `LakshayBansal06`** (the "special profile repository").
2. Push this folder's contents to it:
```powershell
git init; git add .; git commit -m "Midnight Aurora profile"; git branch -M main
git remote add origin https://github.com/LakshayBansal06/LakshayBansal06.git
git push -u origin main
```
3. Go to **Settings → Actions → General → Workflow permissions** and choose **Read and write permissions**.
4. Go to **Actions → Contribution snake → Run workflow** once, so the snake appears right away. After that it redraws every day.

## 4. Polish the rest of the profile page
- **Name, bio, location, website** (Settings → Public profile). Suggested bio: your first role + "· building with" + your top 2 tools.
- **Pin your 6 best repos.** Give each a one-line description, topics and a homepage link.
- **Profile photo:** a clear, well-lit headshot on a plain or dark background works best with this theme.
- After you edit `profile.json` on GitHub, the *Rebuild profile* workflow regenerates every SVG for you.
