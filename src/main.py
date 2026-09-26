import os
import sys
import glob
import ctypes
import time
import threading
import subprocess
from collections import deque
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CREATE_NO_WINDOW = 0x08000000

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join(BASE_DIR, "bin")
VPS_DIR = os.path.join(BIN_DIR, "vps")
DLL_PATH = os.path.join(BIN_DIR, "vpn_core.dll")
PS_SCRIPT = os.path.join(BASE_DIR, "scripts", "toggle_vpn.ps1")
WG_EXE = os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "WireGuard", "wireguard.exe")

HAS_DLL = False
vpn_core = None

if os.path.exists(DLL_PATH):
    try:
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(BIN_DIR)
        
        orig_cwd = os.getcwd()
        os.chdir(BIN_DIR)
        vpn_core = ctypes.CDLL(DLL_PATH)
        os.chdir(orig_cwd)

        vpn_core.CheckLatency.argtypes = [ctypes.c_char_p]
        vpn_core.CheckLatency.restype = ctypes.c_int
        HAS_DLL = True
    except Exception:
        HAS_DLL = False


class LoadingSpinner(ctk.CTkCanvas):
    def __init__(self, master, size=30, color="#00f0ff", bg_color="#121824", **kwargs):
        super().__init__(master, width=size, height=size, bg=bg_color, highlightthickness=0, **kwargs)
        self.size = size
        self.color = color
        self.angle = 0
        self.is_running = False

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._animate()

    def stop(self):
        self.is_running = False
        self.delete("all")

    def _animate(self):
        if not self.is_running:
            return
        self.delete("all")
        
        padding = 4
        extent = 120
        self.create_arc(
            padding, padding, self.size - padding, self.size - padding,
            start=self.angle, extent=extent, outline=self.color, width=3, style="arc"
        )
        
        self.angle = (self.angle + 12) % 360
        self.after(30, self._animate)


class ModernVPNManager(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("PROTON VPN MANAGER - ULTIMATE EDITION")
        self.geometry("580x760")
        self.resizable(False, False)
        self.configure(fg_color="#090d16")

        self.COLOR_BG = "#090d16"
        self.COLOR_CARD = "#121824"
        self.COLOR_BORDER = "#1f293d"
        self.COLOR_CYAN = "#00f0ff"
        self.COLOR_GREEN = "#10b981"
        self.COLOR_RED = "#ef4444"
        self.COLOR_PURPLE = "#8b5cf6"
        self.COLOR_GRAY = "#64748b"
        self.COLOR_ORANGE = "#f59e0b"

        self.servers = self.scan_vps_servers()
        self.selected_server = ctk.StringVar(value=self.servers[0] if self.servers else "No .conf found")
        
        self.is_processing = False
        self.is_connected = False
        
        self.last_rx = 0
        self.last_tx = 0
        self.total_rx = 0
        self.total_tx = 0
        self.last_time = time.time()
        self.connect_start_time = 0
        self.stats_thread_active = False
        
        self.ping_token = 0

        self.speed_history_dl = deque([0]*20, maxlen=20)
        self.speed_history_ul = deque([0]*20, maxlen=20)

        self.setup_ui()
        self.async_check_vpn_status()

    def scan_vps_servers(self):
        if not os.path.exists(VPS_DIR):
            os.makedirs(VPS_DIR, exist_ok=True)
            return []
        conf_files = glob.glob(os.path.join(VPS_DIR, "*.conf"))
        servers = [os.path.splitext(os.path.basename(f))[0] for f in conf_files]
        return servers if servers else ["wg-US-FREE-27"]

    def setup_ui(self):
        # 1. HEADER BAR
        header_card = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=16, border_width=1, border_color=self.COLOR_BORDER)
        header_card.pack(fill="x", padx=20, pady=(20, 10))

        header_title = ctk.CTkLabel(
            header_card, text="⚡ PROTON VPN CORE", 
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), 
            text_color=self.COLOR_CYAN
        )
        header_title.pack(anchor="w", padx=20, pady=(12, 2))

        header_sub = ctk.CTkLabel(
            header_card, text="Tối ưu độ trễ Roblox & Bật/Tắt WireGuard tự động", 
            font=ctk.CTkFont(family="Segoe UI", size=12), 
            text_color=self.COLOR_GRAY
        )
        header_sub.pack(anchor="w", padx=20, pady=(0, 12))

        # 2. STATUS DISPLAY CARD
        self.status_card = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=16, border_width=1, border_color=self.COLOR_BORDER)
        self.status_card.pack(fill="x", padx=20, pady=10)

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=12)

        self.status_icon = ctk.CTkLabel(
            status_inner, text="●", 
            font=ctk.CTkFont(size=24), text_color=self.COLOR_RED
        )
        self.status_icon.pack(side="left", padx=(0, 10))

        self.status_label = ctk.CTkLabel(
            status_inner, text="DISCONNECTED", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"), 
            text_color="#ffffff"
        )
        self.status_label.pack(side="left")

        self.status_spinner = LoadingSpinner(status_inner, size=24, color=self.COLOR_CYAN, bg_color=self.COLOR_CARD)

        core_text = "C++ ENGINE ACTIVE" if HAS_DLL else "PYTHON FALLBACK"
        core_color = self.COLOR_GREEN if HAS_DLL else self.COLOR_ORANGE
        
        self.core_badge = ctk.CTkLabel(
            status_inner, text=core_text, 
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=core_color, fg_color="#0a0f1d", corner_radius=8, padx=10, pady=4
        )
        self.core_badge.pack(side="right")

        # 3. SERVER SELECTOR
        server_card = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=16, border_width=1, border_color=self.COLOR_BORDER)
        server_card.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            server_card, text="CHỌN SERVER TUNNEL", 
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), 
            text_color=self.COLOR_GRAY
        ).pack(anchor="w", padx=20, pady=(10, 4))

        self.cb_server = ctk.CTkOptionMenu(
            server_card, variable=self.selected_server, values=self.servers,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="#1a2336", button_color=self.COLOR_PURPLE, button_hover_color="#7c3aed",
            text_color="#ffffff", corner_radius=10, height=38,
            command=lambda choice: self.async_check_vpn_status()
        )
        self.cb_server.pack(fill="x", padx=20, pady=(0, 12))

        # 4. PING METRICS
        ping_container = ctk.CTkFrame(self, fg_color="transparent")
        ping_container.pack(fill="x", padx=20, pady=5)

        cf_card = ctk.CTkFrame(ping_container, fg_color=self.COLOR_CARD, corner_radius=16, border_width=1, border_color=self.COLOR_BORDER, width=260, height=80)
        cf_card.pack_propagate(False)
        cf_card.pack(side="left")

        ctk.CTkLabel(cf_card, text="PING CLOUDFLARE", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.COLOR_GRAY).pack(anchor="w", padx=15, pady=(8, 0))
        
        cf_row = ctk.CTkFrame(cf_card, fg_color="transparent")
        cf_row.pack(anchor="w", padx=15, pady=(2, 0), fill="x")
        self.spinner_cf = LoadingSpinner(cf_row, size=20, color=self.COLOR_CYAN, bg_color=self.COLOR_CARD)
        self.lbl_cf_ping = ctk.CTkLabel(cf_row, text="-- ms", font=ctk.CTkFont(size=18, weight="bold"), text_color=self.COLOR_CYAN)
        self.lbl_cf_ping.pack(side="left")

        rb_card = ctk.CTkFrame(ping_container, fg_color=self.COLOR_CARD, corner_radius=16, border_width=1, border_color=self.COLOR_BORDER, width=260, height=80)
        rb_card.pack_propagate(False)
        rb_card.pack(side="right")

        ctk.CTkLabel(rb_card, text="PING ROBLOX SERVER", font=ctk.CTkFont(size=10, weight="bold"), text_color=self.COLOR_GRAY).pack(anchor="w", padx=15, pady=(8, 0))
        
        rb_row = ctk.CTkFrame(rb_card, fg_color="transparent")
        rb_row.pack(anchor="w", padx=15, pady=(2, 0), fill="x")
        self.spinner_rb = LoadingSpinner(rb_row, size=20, color=self.COLOR_PURPLE, bg_color=self.COLOR_CARD)
        self.lbl_rb_ping = ctk.CTkLabel(rb_row, text="-- ms", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.COLOR_PURPLE)
        self.lbl_rb_ping.pack(side="left")

        # 5. PROTON VPN DASHBOARD PANEL
        self.proton_panel = ctk.CTkFrame(self, fg_color="#0e1320", corner_radius=16, border_width=1, border_color="#1b253b")
        
        p_top = ctk.CTkFrame(self.proton_panel, fg_color="transparent")
        p_top.pack(fill="x", padx=15, pady=(10, 5))
        
        self.lbl_prot_status = ctk.CTkLabel(
            p_top, text="🔒 Protected  •  0 sec", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), 
            text_color=self.COLOR_GREEN
        )
        self.lbl_prot_status.pack(side="left")

        speed_right = ctk.CTkFrame(p_top, fg_color="transparent")
        speed_right.pack(side="right")
        
        self.lbl_live_dl = ctk.CTkLabel(speed_right, text="↓ 0.0 KB/s", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.COLOR_GREEN)
        self.lbl_live_dl.pack(side="left", padx=(0, 8))
        
        self.lbl_live_ul = ctk.CTkLabel(speed_right, text="↑ 0.0 KB/s", font=ctk.CTkFont(size=12, weight="bold"), text_color="#f43f5e")
        self.lbl_live_ul.pack(side="left")

        # Bố cục 3 chỉ số thực tế: VPN IP | Protocol | Network Status
        p_grid = ctk.CTkFrame(self.proton_panel, fg_color="transparent")
        p_grid.pack(fill="x", padx=15, pady=5)

        col1 = ctk.CTkFrame(p_grid, fg_color="transparent")
        col1.pack(side="left", anchor="n", expand=True, fill="x")
        
        ctk.CTkLabel(col1, text="VPN IP", font=ctk.CTkFont(size=10), text_color=self.COLOR_GRAY).pack(anchor="w")
        self.lbl_vpn_ip = ctk.CTkLabel(col1, text="10.13.13.2", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ffffff")
        self.lbl_vpn_ip.pack(anchor="w")

        col2 = ctk.CTkFrame(p_grid, fg_color="transparent")
        col2.pack(side="left", anchor="n", expand=True, fill="x")

        ctk.CTkLabel(col2, text="Protocol", font=ctk.CTkFont(size=10), text_color=self.COLOR_GRAY).pack(anchor="w")
        ctk.CTkLabel(col2, text="WireGuard (UDP)", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ffffff").pack(anchor="w")

        col3 = ctk.CTkFrame(p_grid, fg_color="transparent")
        col3.pack(side="left", anchor="n", expand=True, fill="x")

        ctk.CTkLabel(col3, text="Network Status", font=ctk.CTkFont(size=10), text_color=self.COLOR_GRAY).pack(anchor="w")
        self.lbl_net_status = ctk.CTkLabel(col3, text="ONLINE", font=ctk.CTkFont(size=12, weight="bold"), text_color=self.COLOR_GREEN)
        self.lbl_net_status.pack(anchor="w")

        chart_frame = ctk.CTkFrame(self.proton_panel, fg_color="#0a0e18", corner_radius=10)
        chart_frame.pack(fill="x", padx=15, pady=(8, 12))

        ctk.CTkLabel(chart_frame, text="Current traffic (KB/s)", font=ctk.CTkFont(size=10), text_color=self.COLOR_GRAY).pack(anchor="w", padx=10, pady=(5, 0))

        self.canvas = ctk.CTkCanvas(chart_frame, height=55, bg="#0a0e18", highlightthickness=0)
        self.canvas.pack(fill="x", padx=5, pady=(0, 5))

        # 6. ACTION BUTTONS
        btn_container = ctk.CTkFrame(self, fg_color="transparent")
        btn_container.pack(fill="x", padx=20, pady=(15, 20))

        self.btn_toggle = ctk.CTkButton(
            btn_container, text="CONNECT SERVER", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=self.COLOR_GREEN, hover_color="#059669", height=48, corner_radius=12,
            command=self.on_click_toggle
        )
        self.btn_toggle.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.btn_ping = ctk.CTkButton(
            btn_container, text="TEST PING", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color="#1e293b", hover_color="#334155", text_color="#ffffff", height=48, corner_radius=12,
            command=self.update_ping
        )
        self.btn_ping.pack(side="right", fill="x", expand=True, padx=(10, 0))

    def update_btn_ui(self, mode):
        if mode == "CONNECTED":
            self.is_connected = True
            self.status_spinner.stop()
            self.status_spinner.pack_forget()
            self.status_icon.pack(side="left", padx=(0, 10))

            self.btn_toggle.configure(
                text="DISCONNECT SERVER", 
                fg_color=self.COLOR_RED, 
                hover_color="#dc2626", 
                state="normal"
            )
            self.proton_panel.pack(fill="x", padx=20, pady=10, before=self.btn_toggle.master)
            self.start_stats_thread()

        elif mode == "DISCONNECTED":
            self.is_connected = False
            self.status_spinner.stop()
            self.status_spinner.pack_forget()
            self.status_icon.pack(side="left", padx=(0, 10))

            self.btn_toggle.configure(
                text="CONNECT SERVER", 
                fg_color=self.COLOR_GREEN, 
                hover_color="#059669", 
                state="normal"
            )
            self.proton_panel.pack_forget()
            self.stop_stats_thread()

        elif mode == "LOADING":
            text = "CONNECTING..." if not self.is_connected else "DISCONNECTING..."
            self.status_icon.pack_forget()
            self.status_spinner.pack(side="left", padx=(0, 10))
            self.status_spinner.start()

            self.btn_toggle.configure(
                text=text, 
                fg_color=self.COLOR_GRAY, 
                hover_color=self.COLOR_GRAY, 
                state="disabled"
            )

    def async_check_vpn_status(self):
        threading.Thread(target=self._worker_check_vpn, daemon=True).start()

    def _worker_check_vpn(self):
        server_name = self.selected_server.get().strip()
        is_running = False

        if server_name and not server_name.startswith("No .conf"):
            try:
                cmd = f'sc query "WireGuardTunnel${server_name}"'
                output = subprocess.check_output(cmd, shell=True, creationflags=CREATE_NO_WINDOW).decode('utf-8', errors='ignore')
                if "RUNNING" in output:
                    is_running = True
            except Exception:
                pass

        self.after(0, lambda: self._apply_vpn_status(is_running, server_name))

    def _apply_vpn_status(self, is_running, server_name):
        if is_running:
            self.status_icon.configure(text_color=self.COLOR_GREEN)
            self.status_label.configure(text=f"CONNECTED ({server_name})", text_color=self.COLOR_GREEN)
            self.update_btn_ui("CONNECTED")
        else:
            self.status_icon.configure(text_color=self.COLOR_RED)
            self.status_label.configure(text="DISCONNECTED", text_color="#ffffff")
            self.update_btn_ui("DISCONNECTED")

    def start_stats_thread(self):
        if not self.stats_thread_active:
            self.stats_thread_active = True
            threading.Thread(target=self._update_network_stats_loop, daemon=True).start()

    def stop_stats_thread(self):
        self.stats_thread_active = False

    def _update_network_stats_loop(self):
        while self.stats_thread_active and self.is_connected:
            server_name = self.selected_server.get().strip()
            rx_bytes, tx_bytes = self.get_wireguard_transfer(server_name)

            now = time.time()
            dt = now - self.last_time
            if dt <= 0:
                dt = 1

            dl_kb = 0.0
            ul_kb = 0.0

            if self.last_rx > 0 and self.last_tx > 0 and rx_bytes >= self.last_rx:
                dl_kb = ((rx_bytes - self.last_rx) / dt) / 1024
                ul_kb = ((tx_bytes - self.last_tx) / dt) / 1024

            self.total_rx = rx_bytes
            self.total_tx = tx_bytes
            self.last_rx = rx_bytes
            self.last_tx = tx_bytes
            self.last_time = now

            self.speed_history_dl.append(dl_kb)
            self.speed_history_ul.append(ul_kb)

            uptime_sec = int(now - self.connect_start_time)

            self.after(0, lambda d=dl_kb, u=ul_kb, ut=uptime_sec: self._update_proton_ui(d, u, ut))
            time.sleep(1)

    def get_wireguard_transfer(self, server_name):
        try:
            cmd = f'"{WG_EXE}" show "{server_name}" transfer'
            output = subprocess.check_output(cmd, shell=True, creationflags=CREATE_NO_WINDOW).decode('utf-8', errors='ignore').strip()
            if output:
                parts = output.split()
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return 0, 0

    def _update_proton_ui(self, dl_kb, ul_kb, uptime_sec):
        if not self.is_connected:
            return

        self.lbl_prot_status.configure(text=f"🔒 Protected  •  {uptime_sec} sec")
        self.lbl_live_dl.configure(text=f"↓ {dl_kb:.1f} KB/s")
        self.lbl_live_ul.configure(text=f"↑ {ul_kb:.1f} KB/s")

        if self.is_connected:
            self.lbl_net_status.configure(text="ONLINE", text_color=self.COLOR_GREEN)
        else:
            self.lbl_net_status.configure(text="OFFLINE", text_color=self.COLOR_RED)

        self.draw_chart()

    def draw_chart(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()

        if w < 10 or h < 10:
            return

        self.canvas.create_line(0, h/2, w, h/2, fill="#131c2e", dash=(2, 4))
        max_val = max(max(self.speed_history_dl), max(self.speed_history_ul), 50.0)
        dx = w / 19

        points_dl = [(i * dx, h - (val / max_val) * (h - 10) - 2) for i, val in enumerate(self.speed_history_dl)]
        for i in range(len(points_dl) - 1):
            self.canvas.create_line(points_dl[i][0], points_dl[i][1], points_dl[i+1][0], points_dl[i+1][1], fill=self.COLOR_GREEN, width=2)

        points_ul = [(i * dx, h - (val / max_val) * (h - 10) - 2) for i, val in enumerate(self.speed_history_ul)]
        for i in range(len(points_ul) - 1):
            self.canvas.create_line(points_ul[i][0], points_ul[i][1], points_ul[i+1][0], points_ul[i+1][1], fill="#f43f5e", width=1, dash=(3, 2))

    def get_ping(self, host):
        if HAS_DLL and vpn_core is not None:
            try:
                res = vpn_core.CheckLatency(host.encode('utf-8'))
                if res > 0:
                    return res
            except Exception:
                pass
        
        try:
            output = subprocess.check_output(f"ping -n 1 -w 1000 {host}", shell=True, creationflags=CREATE_NO_WINDOW).decode('utf-8', errors='ignore')
            if "TTL=" in output or "ttl=" in output:
                return int(output.split("time=")[1].split("ms")[0].strip())
        except Exception:
            return -1
        return -1

    def is_roblox_active(self):
        try:
            cmd = 'tasklist /FI "STATUS eq RUNNING"'
            output = subprocess.check_output(cmd, creationflags=CREATE_NO_WINDOW).decode('utf-8', errors='ignore').lower()
            if "robloxplayerbeta.exe" in output:
                return True
            for b in ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe"]:
                if b in output:
                    return True
        except Exception:
            pass
        return False

    def update_ping(self):
        self.ping_token += 1
        current_token = self.ping_token

        self.lbl_cf_ping.pack_forget()
        self.spinner_cf.pack(side="left")
        self.spinner_cf.start()

        self.lbl_rb_ping.pack_forget()
        self.spinner_rb.pack(side="left")
        self.spinner_rb.start()

        self.btn_ping.configure(state="disabled")

        threading.Thread(target=self._worker_update_ping, args=(current_token,), daemon=True).start()

    def _worker_update_ping(self, token):
        cf_ping = self.get_ping("1.1.1.1")
        roblox_active = self.is_roblox_active()
        rb_ping = self.get_ping("128.116.119.3") if roblox_active else -2

        if token == self.ping_token:
            self.after(0, lambda: self._apply_ping_results(cf_ping, rb_ping, roblox_active))

    def _apply_ping_results(self, cf_ping, rb_ping, roblox_active):
        self.spinner_cf.stop()
        self.spinner_cf.pack_forget()
        self.lbl_cf_ping.pack(side="left")

        self.spinner_rb.stop()
        self.spinner_rb.pack_forget()
        self.lbl_rb_ping.pack(side="left")

        self.btn_ping.configure(state="normal")

        cf_str = f"{cf_ping} ms" if cf_ping != -1 else "Timeout"
        self.lbl_cf_ping.configure(text=cf_str, font=ctk.CTkFont(size=18, weight="bold"))

        if not roblox_active:
            self.lbl_rb_ping.configure(text="App/Web Not Open", text_color=self.COLOR_ORANGE, font=ctk.CTkFont(size=11, weight="bold"))
        else:
            rb_str = f"{rb_ping} ms" if rb_ping != -1 else "Timeout"
            self.lbl_rb_ping.configure(text=rb_str, text_color=self.COLOR_PURPLE, font=ctk.CTkFont(size=18, weight="bold"))

    def on_click_toggle(self):
        if self.is_processing:
            return
        
        server_name = self.selected_server.get().strip()
        if not server_name or server_name.startswith("No .conf"):
            return

        self.is_processing = True
        self.update_btn_ui("LOADING")

        threading.Thread(target=self._async_toggle_task, args=(server_name,), daemon=True).start()

    def _async_toggle_task(self, server_name):
        try:
            args = f'-WindowStyle Hidden -ExecutionPolicy Bypass -File "{PS_SCRIPT}" -TunnelName "{server_name}"'
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell.exe", args, None, 0)
            if ret > 32:
                time.sleep(3.5)
        except Exception:
            pass
        
        self.after(0, self._on_toggle_complete)

    def _on_toggle_complete(self):
        self.is_processing = False
        self.async_check_vpn_status()
        self.update_ping()


if __name__ == "__main__":
    app = ModernVPNManager()
    app.mainloop()