# ⚡ VPN MANAGER - ULTIMATE EDITION

An advanced Windows GUI application designed to manage WireGuard VPN tunnels, optimize ping latency for **Roblox**, and display real-time network traffic telemetry.

---

## 🌟 Key Features

* **Modern GUI Design:** Sleek Dark Mode interface built using `customtkinter`.
* **Custom App Branding:** Integrated custom application icon (`vpn_lock_global.ico`) for windows and taskbar display.
* **C++ Core Engine Integration:** Calls `vpn_core.dll` via Python's `ctypes` for high-precision latency checks, with a built-in Python fallback mechanism.
* **Automatic Server Discovery:** Automatically scans and retrieves WireGuard configuration files (`.conf`) placed inside `bin/vps/`.
* **Roblox & Cloudflare Ping Test:** Detects active Roblox application/web processes to measure accurate latency against Roblox servers (`128.116.119.3`) and Cloudflare DNS (`1.1.1.1`).
* **Real-time Traffic Telemetry:**
  * Displays live Download and Upload speeds in KB/s.
  * Interactive real-time network bandwidth graph.
  * Extracts transfer statistics directly via `wireguard.exe`.
* **Administrative Tunnel Control:** Integrates with PowerShell scripts running under Administrator privileges (`runas`) to start/stop WireGuard services.

---

## 📁 Repository Structure

```text
VPN-Manager/
├── bin/                  # Compiled binaries (.dll), config files, and UI assets
│   ├── assets/           # Application icons and graphic assets
│   │   └── vpn_lock_global.ico
│   ├── vpn_core.dll      # C++ latency engine library
│   └── vps/              # Directory for WireGuard configuration files (.conf)
├── build/                # Intermediate object files (.o) created during build
├── include/              # C/C++ header files
│   └── vpn_core.h        # Function definitions for the C++ core engine
├── src/                  # Application source code
│   ├── main.py           # Main Python GUI implementation
│   └── vpn_core.cpp      # C++ source code for high-performance latency measurement
├── scripts/              # System execution scripts
│   ├── setup_vps.sh      # VPS deployment script for Linux/WSL
│   └── toggle_vpn.ps1    # PowerShell script to handle WireGuard service toggles
├── Makefile              # Build automation script for compiling C++ components via WSL/Linux
└── README.md             # Project documentation
```

---

## 🛠️ System Requirements & Installation

### 1. Prerequisites

* Operating System: Windows 10 / 11
* Python Version: Python 3.8+
* WireGuard Client: Installed on Windows (`C:\Program Files\WireGuard\wireguard.exe`)

### 2. Install Python Dependencies

Install the required GUI library using pip:

```bash
pip install customtkinter
```

---

## 🚀 Usage Instructions

1. **Add Server Configurations & Assets:**
   * Place your WireGuard `.conf` configuration files inside the `bin/vps/` directory.
   * Ensure `vpn_lock_global.ico` is placed inside the `bin/assets/` directory.
2. **Building the C++ DLL (Optional):**
   * If you want to recompile `vpn_core.dll` from source (`src/vpn_core.cpp`), run:
     ```bash
     make
     ```
3. **Launch the Application:**
   * Open Terminal or Command Prompt as Administrator (required to modify Windows WireGuard services) and execute:
     ```bash
     python src/main.py
     ```
4. **Operations:**
   * **Select Server:** Choose your preferred WireGuard configuration from the drop-down menu.
   * **TEST PING:** Run latency diagnostics for Cloudflare and Roblox servers.
   * **CONNECT SERVER:** Click to activate the VPN tunnel and start live traffic monitoring.
