<p align="center">
  <img src="assets/alice-mark.svg" width="120" height="120" alt="Alice Music Bot logo">
</p>

<h1 align="center">Alice Music Bot</h1>

<p align="center">
  <strong>Telegram music. No music API key needed.</strong><br>
  Alice 2.0 · Free to use · Self-hosted
</p>

<p align="center">
  <img src="assets/alice-waveform.gif" width="240" height="36" alt="Animated music waveform">
</p>

<p align="center">
  <a href="https://alicemusic.online/getting-started.html">Get started</a> ·
  <a href="https://alicemusic.online/deployment.html">Deploy</a> ·
  <a href="https://t.me/thanosprosss">Support</a>
</p>

**Your group. Your music. No paid music API.**

**Alice 2.0** is a free, self-hosted **Telegram music bot** for group voice chats. Search for songs, share supported music links, or play Telegram audio with queue controls and custom player cards. Built in Python with Pyrofork and Py-TgCalls, Alice handles music lookup inside the bot—there is no separate music API server to deploy or music API key to buy.

> **100% free to use. No music API key needed.**  
> Alice charges no bot subscription or music API fee. Hosting, internet and database costs depend on your setup. Telegram credentials are still required.

Current release: **2.1.0** · Alice 2.x series.

[Get started](https://alicemusic.online/getting-started.html) · [Deploy Alice](https://alicemusic.online/deployment.html) · [Command guide](https://alicemusic.online/commands.html)

## What can Alice do?

Song search and playback from supported song links.  
Telegram audio files and voice messages.  
Queue management, shuffle, repeat and admin playback controls.  
Song artwork and player cards with a charcoal and gold design.  
Private owner tools for statistics, broadcasts and database management.  

## Documentation

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

### Everyday commands

- **Play:** `/play song name` — play a song or add it to the queue.
- **Search:** `/search song name` — choose a matching song.
- **Queue:** `/queue` — view upcoming tracks.
- **Playback:** `/pause` and `/resume`.
- **Skip or stop:** `/skip` and `/stop`.
- **Queue modes:** `/shuffle` and `/repeat`.

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

## Developer

### Rishabh Anand

**Creator & Lead Developer · Founder of Thanos Pro**

I build Telegram bots and automation tools in Python. Alice and [CipherElite ↗](https://github.com/rishabhops/CipherElite) are my projects under Thanos Pro.

- GitHub: [@rishabhops](https://github.com/rishabhops)
- Telegram: [@thanosceo](https://t.me/thanosceo)
- Instagram: [@xrishabhanand](https://www.instagram.com/xrishabhanand/)
- LinkedIn: [Rishabh Anand](https://www.linkedin.com/in/xrishabhanand/)

## Co-developers

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

## Support & community

**Talk to us. Stay in the loop.**

**[Join the conversation ↗](https://t.me/thanosprosss)**  
Questions, bug reports and feedback — our Telegram support group.

**[Follow Thanos Pro ↗](https://t.me/THANOS_PRO)**  
Project news and release updates.

**[Message me ↗](https://t.me/thanosceo)**  
Get in touch directly on Telegram.

If you enjoy using Alice, leave a star on the repository or share it with your friends. Bug reports and contributions are welcome too.

## Credits

Thanks to the projects that make Alice possible:

**Telegram & voice**  
[Pyrofork ↗](https://github.com/Mayuri-Chan/pyrofork) · [Py-TgCalls ↗](https://github.com/pytgcalls/pytgcalls) · [NTgCalls ↗](https://github.com/pytgcalls/ntgcalls)

**Audio, storage & artwork**  
[FFmpeg ↗](https://ffmpeg.org/) · [MongoDB ↗](https://www.mongodb.com/) · [Pillow ↗](https://python-pillow.github.io/)

---

**Alice Music Bot · Thanos Pro**  
Rishabh Anand · Chetan Anand · Shreyas Lande

