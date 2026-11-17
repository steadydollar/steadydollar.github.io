# SteadyDollar daily Short: runbook

Goal: every Short sells ONE product, the **Paycheck Budget Planner ($7)**, https://payhip.com/b/LEfx4
(each video ends on the product card "Link in description"; the description's 2nd line is the link).

Files (all in this folder):
- `specs.json`  queue of Shorts. Upload them in order.
- `make_short.py <slug>`  renders `video/shorts/<slug>.mp4` (fonts bundled, needs ffmpeg + Pillow).
- `uploads.json`  log: {slug, video_id, date_pt, status, units}. status: public | quota | failed.

## Daily run (00:07 America/Los_Angeles = 09:07 Belgrade, right after YouTube quota reset)

1. **Quota guard.** `today` = current date in America/Los_Angeles (YouTube quota day).
   - If uploads.json has any entry with date_pt == today: STOP (max 1 upload per day).
   - GET youtube/v3/playlistItems?part=contentDetails&playlistId=UUzBz4aCkBDVE_GiWUKW0eLw&maxResults=5 (1 unit).
     If a video was published in the last 20 h: log it and STOP (stops duplicates).
2. **Pick** the first spec in specs.json whose slug has no `public` entry in uploads.json.
   If none left: write 3 new specs (same keys, paycheck-planning topics only: bills, paydays, biweekly,
   rent, groceries per paycheck, raises, refunds, seasonal; numbers must add up; max 6 rows; hook max 3
   short lines) and append them. Render with make_short.py, check one frame visually, commit + push.
3. **Upload** (NEVER the Composio YOUTUBE_UPLOAD_VIDEO tool, it corrupts files):
   a) COMPOSIO_PROXY_EXECUTE youtube POST https://www.googleapis.com/upload/youtube/v3/videos
      query uploadType=resumable, part=snippet,status; header X-Upload-Content-Type: video/mp4; body:
      snippet {title: spec.title + " #Shorts", categoryId "27", tags: spec.tags + ["Shorts","paycheck budget"],
      description: see template}, status {privacyStatus "public", selfDeclaredMadeForKids false}.
      Take the `location` header.
   b) In the Composio workbench download
      https://raw.githubusercontent.com/steadydollar/steadydollar.github.io/main/video/shorts/<slug>.mp4
      and requests.put(location, data=bytes, headers={"Content-Type":"video/mp4"}). channelId must be
      UCzBz4aCkBDVE_GiWUKW0eLw.
   c) A few minutes later GET videos?part=status,processingDetails&id=<id>. Log status public / failed.
4. **On 403/429 quotaExceeded or uploadLimitExceeded**: log {status:"quota", date_pt: today}, do NOT retry
   today. Tell Boris only when the last 3 entries are all quota/failed.
5. Commit uploads.json with message "[skip ci] log short <slug>" and push.

Description template:
```
<spec.caption>
👉 Paycheck Budget Planner ($7, Excel + Google Sheets): https://payhip.com/b/LEfx4

Free guide: https://steadydollar.github.io/how-to-budget-paycheck-to-paycheck/
Example numbers only, not financial advice.
#Shorts #<tag1> #<tag2> #<tag3> #<tag4> #<tag5>
```

Quota math: videos.insert ~1,600 units + ~3 units of checks, out of 10,000/day. The Composio Google
project is shared with other users, so the real per-day upload limit can be lower (429 on 2026-11-10);
that's why it is one attempt per day, no retries.
