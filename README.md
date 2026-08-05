# Karburetor

Karburetor is a Tor client for the KDE Plasma desktop. It is a port of
Carburetor to the KDE stack. The tractor CLI backend from Carburetor is kept
intact and wrapped in a PySide6 and Kirigami user interface with a Plasma
system tray integration. A bare `karburetor` command opens the graphical
interface, while the tractor subcommands remain available from the terminal.

## Features

The main page starts and stops the Tor onion routing connection and shows the
bootstrap progress until the state turns to Protected. The drawer exposes the
Set Proxy toggle, a new identity request, the Preferences page and the Logs
sheet. Pluggable transports such as obfs4, meek, snowflake, webtunnel and
conjure can be configured with bridges, hidden services can be published, and
every runtime log line is streamed into the Logs sheet. All of this is also
available from the Plasma tray icon, which reflects the connection state.

## Requirements

On Parch Linux (Arch based) install these packages:

```sh
sudo pacman -S uv python python-stem python-pycountry python-pysocks pyside6 kirigami kirigami-addons ki18n kconfig kstatusnotifieritem tor
```

Python 3.14 or newer is required. The GUI needs a real Plasma session for the
system tray integration, so running it from a bare window manager will hide
the tray icon.

## Installation

From inside the repository directory run:

```sh
uv sync
```

uv installs the Python dependencies into the local virtual environment. PySide6
and the KDE frameworks are intentionally taken from the distribution packages
instead, so the virtual environment and the system tree share a single
shiboken6 runtime. Mixing a virtual environment PySide6 with the system
KStatusNotifierItem loads two copies of shiboken6 and crashes on import.

## Running the GUI

```sh
uv run karburetor
```

The first run shows an introduction sheet. Press Start on the main page to
launch tor, and wait for the state to become Protected. When the Set Proxy
action is toggled in the drawer while the connection is running, the KDE
system proxy settings in kioslaverc are pointed at the local SOCKS listener.

## Running the CLI

The vendored tractor backend is still available from the command line:

```sh
uv run karburetor start --verbose
uv run karburetor stop
uv run karburetor newid
uv run karburetor restart
uv run karburetor set
uv run karburetor unset
uv run karburetor killtor
```

## Testing

### Verify the connection

Start the connection from the main page and wait for the Protected state.
Then confirm the circuit from a terminal:

```sh
curl --socks5-hostname 127.0.0.1:9052 https://check.torproject.org/
```

The check page reports that the connection is using Tor when the circuit
works. The SOCKS listener defaults to port 9052 and can be changed in the
Preferences page.

### Verify the system proxy

With the connection running, enable Set Proxy in the drawer. KDE then routes
traffic through the local Tor SOCKS listener, and the kioslaverc file under
`~/.config` is updated. Stopping the connection or disabling the toggle
restores the proxy to its previous state. Confirm the value in System Settings
under Network Proxy.

### Verify a new identity

While connected, press New Identity in the tray menu or in the drawer. The
circuit is rebuilt and the next request exits from a fresh node.

### Verify bridges

Open the drawer, then Preferences, and add a bridge for the transport you
need, for example obfs4. Choose that transport as the bridge type and reconnect
by pressing Stop and Start again. The active bridge is shown on the main page.

### Verify hidden services

In the Preferences page add a port mapping that points at a local service,
for example port 8080 to 127.0.0.1:8080. Enable hidden services, reconnect,
and read the generated onion address from the Logs sheet. The service is then
reachable over Tor.

### Verify the logs

The Logs sheet shows every bootstrap and runtime line that the backend prints.
It is opened from the drawer and stays live while the connection runs.

### Verify the tray

Close the window while connected. The Karburetor item stays in the Plasma tray
with an icon that reflects the state: neutral when stopped, acquiring while
connecting, and connected when the circuit is up. The tray menu starts and
stops the connection, requests a new identity, toggles the proxy and quits the
app. Left clicking the item brings the window back.

## Configuration files

The shared settings live in `~/.config/karburetorrc` in KConfig INI format and
are used by both the GUI and the backend, so they can be inspected and edited
with `kwriteconfig6`.

The transport executables, bridge entries and hidden service port mappings are
stored in `~/.config/tractor/config.ini`, which is copied from the packaged
default on first use.

The tor data directory, the control socket and the hidden service directory are
created under `~/.local/share/tractor`.

The KDE system proxy file `~/.config/kioslaverc` is only modified when the Set
Proxy toggle is enabled.

## Troubleshooting

If the connection fails with "Unable to connect to tor", confirm that tor is
installed and that no other tor process is holding the data directory. The app
launches its own tor process on demand.

If the tray icon is missing, run the app from a real Plasma session instead of
a bare Wayland or X11 compositor, because KStatusNotifierItem needs the
Plasma shell to host the item.

If interface text appears untranslated, the translation catalogs are not
shipped yet and the source strings are shown instead.

## Known limitations

The About sheet inside the About page is created by the Kirigami library and
can emit a one time layout warning on some displays. It is cosmetic and does
not affect the sheet.

Settings are not migrated from a GNOME Carburetor install, so a fresh
karburetorrc starts from defaults.
