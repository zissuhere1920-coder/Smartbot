# 🤖 Smart Telegram Bot

## Features
- ✅ Auto "I love u professor 💓 🎀" every 5 hours
- ✅ DM Commands: /send, /timer, /groups, /timerlist, /cancel
- ✅ Manual group add/remove: /addgroup, /removegroup
- ✅ Flask web server for health checks

## Deploy on Render
1. Fork this repo
2. Create Web Service on Render
3. Add environment variable: `BOT_TOKEN`
4. Deploy!

## Commands
| Command | Description |
|---------|-------------|
| /send msg | Send to all groups |
| /timer 5h msg | Set timer |
| /addgroup 123 | Add group manually |
| /removegroup 123 | Remove group |
| /groups | List active groups |
| /timerlist | Active timers |
| /cancel | Cancel all timers |

## Files
- `app.py` - Flask wrapper for Render
- `bot.py` - Main bot code
- `requirements.txt` - Python dependencies