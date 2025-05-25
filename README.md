# nexim
Nexim is an open source Discord bot designed to be able to play YouTube videos (hopefully lol). If you've found this commit/repo, you're seeing it very early on and nothing is really set in stone. Please treat with care :)

## Things to do
* [x] bot connect to given voice channel, and can play example audio in path of bot execution (must be called `audio.mp3`)
* [ ] ensuring efficient audio transcode before playback
* [ ] proper temp audio file storage (possibly in mem)
* [ ] breaking out bot objects to allow multi-server playback
* [ ] queueing system
* [ ] cli to interact with bot
* [ ] search function
* [ ] auto detection of correct vc/configuration of default vc
* [ ] lots of error handling
* [ ] idk allow the bots to give out cookies or something

## Setting up your development environment
1. Set up a virtual Python environment in this repo (`python3 -m pip venv .venv`)
2. Set up a Discord Bot (TODO: Write how to do this)
3. Make a .env file in the "nexim" folder, using .env.example as a base
4. Run main.py
5. Probably not profit, but it was fun I hope

## Disclaimer

This bot is being written to respond to many music bots losing their ability to play YouTube videos as music, given that Discord has removed their "verified" status if they did not comply. THIS BOT IS NOT DESIGNED FOR USE AS AN OFFICIAL BOT, as this may be against YouTube's Terms of Service. The bot is instead designed for individual users to utilize as they see fit.

