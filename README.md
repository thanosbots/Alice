<img src="assets/alice-mark.svg" align="right" width="110" alt="Alice music bot — lavender headphones monogram">

# Alice Music Bot — Telegram Music Bot Without a Music API Key

<img src="assets/alice-waveform.gif" width="200" height="30" alt="Animated lavender and lime audio waveform">

<p>
  <strong>ALICE 2.0 · FREE TO USE · NO MUSIC API KEY NEEDED</strong>
</p>

<img src="assets/icons/chat.svg" width="16" height="16" align="center" alt=""> [Support ↗](https://t.me/thanosprosss) &nbsp; / &nbsp; <img src="assets/icons/announcement.svg" width="16" height="16" align="center" alt=""> [Updates ↗](https://t.me/THANOS_PRO) &nbsp; / &nbsp; <img src="assets/icons/code.svg" width="16" height="16" align="center" alt=""> [Developer ↓](#developer)

## <img src="assets/icons/telegram.svg" width="20" height="20" align="center" alt=""> Try Alice now

**Already hosted. Ready for your group.**

Use our deployed bot **[@alice2music_bot](https://t.me/alice2music_bot)** on Telegram—no server setup or personal API credentials needed to try it.

**[Open Alice on Telegram ↗](https://t.me/alice2music_bot)** · **[Add Alice to your group ↗](https://t.me/alice2music_bot?startgroup=true)**

Open the bot and tap **Start**, then add it to your group and follow its setup instructions. Once the group voice chat and required permissions are ready, use `/play song name` to start listening. Want your own instance? Follow the deployment guide below.

**Your group. Your music. No paid music API.**

**Alice 2.0** is a free, self-hosted **Telegram music bot** for group voice chats. Search for songs, share supported music links, or play Telegram audio with queue controls and custom player cards. Built in Python with Pyrofork and Py-TgCalls, Alice handles music lookup inside the bot—there is no separate music API server to deploy or music API key to buy.

> **100% free to use. No music API key needed.**  
> Alice charges no bot subscription or music API fee. Hosting, internet and database costs depend on your setup. Telegram credentials are required only when hosting your own instance.

Current code release: **2.1.0**, part of the Alice 2.x series.

[Get started](https://alicemusic.online/getting-started.html) · [Deploy Alice](https://alicemusic.online/deployment.html) · [Command guide](https://alicemusic.online/commands.html)

## What can Alice do?

<img src="assets/icons/search.svg" width="16" height="16" align="center" alt=""> Song search and playback from supported song links.  
<img src="assets/icons/audio.svg" width="16" height="16" align="center" alt=""> Telegram audio files and voice messages.  
<img src="assets/icons/queue.svg" width="16" height="16" align="center" alt=""> Queue management, shuffle, repeat and admin playback controls.  
<img src="assets/icons/artwork.svg" width="16" height="16" align="center" alt=""> Song artwork and player cards with a charcoal and gold design.  
<img src="assets/icons/shield.svg" width="16" height="16" align="center" alt=""> Private owner tools for statistics, broadcasts and database management.  

<br clear="both">

## <img src="assets/icons/book.svg" width="20" height="20" align="center" alt=""> Documentation

Commands, deployment, configuration and troubleshooting are in the **[Alice documentation ↗](https://alicemusic.online)**.

For help, join the [Telegram support group ↗](https://t.me/thanosprosss).

## Run your own Telegram music bot

You need Python 3, FFmpeg/FFprobe, a MongoDB connection, a Telegram bot token, and Telegram API credentials with an assistant account session. The setup script prepares the Python 3.11 environment and installs the bot dependencies.

```sh
git clone https://github.com/thanosbots/Alice.git
cd Alice
bash setup.sh
```

Fill in the generated `Config.env` using [Config.env.example](Config.env.example), then start Alice:

```sh
bash start.sh
```

Add the bot and assistant account to your group, grant the permissions described in the [getting started guide](https://alicemusic.online/getting-started.html), and open a voice chat.

| Command | What it does |
| :--- | :--- |
| `/play song name` | Find a song and play it or add it to the queue |
| `/search song name` | Choose from matching songs |
| `/queue` | View upcoming tracks |
| `/pause`, `/resume` | Control playback |
| `/skip`, `/stop` | Move to the next track or end playback |
| `/shuffle`, `/repeat` | Change how the queue plays |

You can also reply to a Telegram audio file or voice message with `/play`. Playback and queue edits are restricted to group admins or the configured bot owner.

## Frequently asked questions

### Does Alice work without an API?

**No music API key is needed.** Alice does not need a paid music API subscription or a separately hosted music API server. It still makes online requests to a music provider and uses Telegram's API, so it is not API-free or offline.

### Is Alice free?

Alice is free to use, with no bot subscription or music API fee. Your hosting provider, database provider or internet service may charge for their services.

### Which credentials do I need?

Your Telegram `API_ID`, `API_HASH`, `BOT_TOKEN`, assistant `STRING_SESSION`, and MongoDB `MONGO_URL`. Keep these in your local `Config.env`; never commit them to GitHub.

### Where can I deploy Alice?

Use a [Linux VPS](https://alicemusic.online/deploy-vps.html), [local Linux machine](https://alicemusic.online/deploy-linux.html), or [macOS](https://alicemusic.online/deploy-macos.html). Follow the deployment guide for your platform.

<a id="developer"></a>

## <img src="assets/icons/code.svg" width="20" height="20" align="center" alt=""> Developer

### Rishabh Anand

**Creator & Lead Developer · Founder of Thanos Pro**

I build Telegram bots and automation tools in Python. Alice and [CipherElite ↗](https://github.com/rishabhops/CipherElite) are my projects under Thanos Pro.

<p>
  <a href="https://github.com/rishabhops"><img src="assets/icons/github.svg" width="16" height="16" align="center" alt=""> <strong>GitHub ↗</strong></a>
  &nbsp;&nbsp; / &nbsp;&nbsp;
  <a href="https://t.me/thanosceo"><img src="assets/icons/telegram.svg" width="16" height="16" align="center" alt=""> <strong>Telegram ↗</strong></a>
  &nbsp;&nbsp; / &nbsp;&nbsp;
  <a href="https://www.instagram.com/xrishabhanand/"><img src="assets/icons/instagram.svg" width="16" height="16" align="center" alt=""> <strong>Instagram ↗</strong></a>
  &nbsp;&nbsp; / &nbsp;&nbsp;
  <a href="https://www.linkedin.com/in/xrishabhanand/"><img src="assets/icons/linkedin.svg" width="16" height="16" align="center" alt=""> <strong>LinkedIn ↗</strong></a>
</p>

<sub>@rishabhops on GitHub · @thanosceo on Telegram · @xrishabhanand on Instagram & LinkedIn</sub>

## <img src="assets/icons/people.svg" width="20" height="20" align="center" alt=""> Co-developers

### Chetan Anand

Co-developer · Alice Music Bot

- Telegram: [@Xketan](https://t.me/Xketan)
- Instagram: [@xchetan45](https://www.instagram.com/xchetan45/)
- GitHub: [chetananand28](https://github.com/chetananand28)
- LinkedIn: [Chetan Anand](https://www.linkedin.com/in/chetan-anand-66b04a33a)

### Shreyas Lande

Co-developer · Alice Music Bot

- Instagram: [@\_shrey999](https://www.instagram.com/_shrey999/)
- GitHub: [shreyaslande](https://github.com/shreyaslande)
- LinkedIn: [Shreyas Lande](https://www.linkedin.com/in/shreyas-lande-83a19b304)

## <img src="assets/icons/chat.svg" width="20" height="20" align="center" alt=""> Support & community

**Talk to us. Stay in the loop.**

<img src="assets/icons/chat.svg" width="16" height="16" align="center" alt=""> **[Join the conversation ↗](https://t.me/thanosprosss)**  
Questions, bug reports and feedback — our Telegram support group.

<img src="assets/icons/announcement.svg" width="16" height="16" align="center" alt=""> **[Follow Thanos Pro ↗](https://t.me/THANOS_PRO)**  
Project news and release updates.

<img src="assets/icons/mail.svg" width="16" height="16" align="center" alt=""> **[Message me ↗](https://t.me/thanosceo)**  
Get in touch directly on Telegram.

If you enjoy using Alice, leave a star on the repository or share it with your friends. Bug reports and contributions are welcome too.

## <img src="assets/icons/heart.svg" width="20" height="20" align="center" alt=""> Credits

Thanks to the projects that make Alice possible:

<img src="assets/icons/wave.svg" width="16" height="16" align="center" alt=""> **Telegram & voice**  
[Pyrofork ↗](https://github.com/Mayuri-Chan/pyrofork) &nbsp; · &nbsp; [Py-TgCalls ↗](https://github.com/pytgcalls/pytgcalls) &nbsp; · &nbsp; [NTgCalls ↗](https://github.com/pytgcalls/ntgcalls)

<img src="assets/icons/artwork.svg" width="16" height="16" align="center" alt=""> **Audio, storage & artwork**  
[FFmpeg ↗](https://ffmpeg.org/) &nbsp; · &nbsp; [MongoDB ↗](https://www.mongodb.com/) &nbsp; · &nbsp; [Pillow ↗](https://python-pillow.github.io/)

---

**Alice Music Bot · Thanos Pro**  
Rishabh Anand · Chetan Anand · Shreyas Lande
