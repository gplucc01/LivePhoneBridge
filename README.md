# AbleMind Bridge

The Python Control Surface script that connects [AbleMind](https://ablemind.live) to Ableton Live.

AbleMind is an iOS app that lets you control Ableton Live with natural language. This bridge is the piece that runs inside Ableton and makes that possible — it listens for commands over your local network and translates them into real actions in your session.

The bridge is free and open source. The iOS app is available on the [App Store](https://ablemind.live).

## What It Does

The bridge exposes a JSON-RPC interface over TCP that the AbleMind iOS app connects to. When you type a prompt in the app, the AI translates your request into commands and sends them to this bridge, which executes them inside Ableton Live.

**Supported commands include:**

- **Transport** — Get/set tempo, play, stop, record, undo, redo
- **Tracks** — Create MIDI and audio tracks, set name, volume, pan, mute, solo, arm, routing
- **Clips** — Create, delete, duplicate, loop, quantize, fire, and stop clips in session view
- **Arrangement** — List, read, create, and edit clips in arrangement view
- **MIDI Notes** — Write notes into clips with pitch, velocity, duration, and timing
- **Devices** — Load any stock instrument or effect by name with fuzzy search across all browser categories
- **Parameters** — Read and write device parameters with automatic min/max clamping
- **Samples** — Search your sample library, load samples as audio clips or into Simpler, load samples into Drum Rack pads
- **Scenes** — Fire, create, duplicate, and rename scenes

## Requirements

- **Ableton Live 10 or later** (any edition — Intro, Standard, or Suite)
- **macOS or Windows**
- **AbleMind iOS app** installed on an iPhone on the same Wi-Fi network

## Installation

### Step 1: Find your MIDI Remote Scripts folder

**macOS:**
```
/Users/[YourName]/Library/Preferences/Ableton/Live x.x.x/User Remote Scripts/
```

If the `User Remote Scripts` folder doesn't exist, create it.

To find the Library folder: open Finder, click **Go** in the menu bar, hold **Option**, and click **Library**.

**Windows:**
```
C:\Users\[YourName]\AppData\Roaming\Ableton\Live x.x.x\Preferences\User Remote Scripts\
```

If the `User Remote Scripts` folder doesn't exist, create it.

### Step 2: Copy the bridge files

Download the latest release from the [Releases](../../releases) page.

Unzip and copy the entire `LivePhoneBridge` folder into your `User Remote Scripts` directory. The folder structure should look like:

```
User Remote Scripts/
  LivePhoneBridge/
    __init__.py
    server.py
    api.py
```

### Step 3: Enable in Ableton

1. Open Ableton Live
2. Go to **Preferences** → **Link, Tempo & MIDI** (or **MIDI** in older versions)
3. Under **Control Surface**, select **LivePhoneBridge** from the dropdown
4. You should see a log message: `LivePhoneBridge READY! Connect iOS app to [your IP]:8765`

### Step 4: Connect from AbleMind

1. Open the AbleMind app on your iPhone
2. Make sure your iPhone and computer are on the same Wi-Fi network
3. Enter your computer's IP address (shown in the Ableton log message)
4. Default port is **8765**
5. Tap **Connect**

## Finding Your IP Address

**macOS:** System Settings → Network → Wi-Fi → Details → IP Address

**Windows:** Settings → Network & Internet → Wi-Fi → Properties → IPv4 Address

Or open a terminal and run:
- macOS: `ipconfig getifaddr en0`
- Windows: `ipconfig` (look for IPv4 Address under Wi-Fi)

## Troubleshooting

**LivePhoneBridge doesn't appear in the Control Surface dropdown**

Make sure the folder is named exactly `LivePhoneBridge` and contains `__init__.py`. Restart Ableton after copying the files.

**"Connection refused" in the iOS app**

Check that Ableton is running and the bridge is enabled in Preferences. Verify you're using the correct IP address and that both devices are on the same Wi-Fi network. Some routers isolate devices on guest networks — use your main network.

**Connection drops or times out**

The bridge listens on TCP port 8765. Make sure no firewall is blocking this port. On macOS, you may see a system prompt asking to allow incoming connections — click Allow.

**Commands succeed but nothing happens in Ableton**

Make sure the Ableton window is in the foreground when loading devices or samples. Some browser-based operations require Ableton to have focus.

## Updating

To update the bridge, download the latest release and replace the files in your `LivePhoneBridge` folder. Restart Ableton to load the new version.

## How It Works

The bridge is a standard Ableton Live Control Surface script written in Python. When Ableton starts with the bridge enabled, it opens a TCP server on port 8765. The iOS app connects and sends JSON-RPC messages. Each message specifies a method (like `create_midi_track` or `add_notes`) and parameters. The bridge translates these into Ableton Live API calls and returns the results.

All communication happens over your local network. Nothing is sent to the internet by the bridge.

## License

MIT License. See [LICENSE](LICENSE) for details.

## Links

- **Website:** [ablemind.live](https://ablemind.live)
- **iOS App:** [App Store](https://ablemind.live)
- **Privacy Policy:** [ablemind.live/privacy](https://ablemind.live/privacy)
- **Terms of Service:** [ablemind.live/terms](https://ablemind.live/terms)
- **Support:** admin@beachdevllc.com

---

Built by [BeachDev LLC](https://ablemind.live)
