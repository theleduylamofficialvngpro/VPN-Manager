# Roblox Custom VPN Manager

Dự án quản lý VPN riêng tối ưu Ping Roblox kết hợp giữa **VPS Private + Cloudflare WARP Outbound**.

## Hướng dẫn từng bước trong VS Code:

1. **Tạo thư mục dự án và copy code:**
   - Tạo folder `Roblox-VPN-Manager` trong VS Code.
   - Tạo các folder con: `include`, `src`, `scripts`, `bin`, `build`.
   - Copy mã nguồn tương ứng vào đúng tên file ở trên.

2. **Cấu hình VPS bằng WSL Terminal:**
   ```bash
   scp scripts/setup_vps.sh root@<IP_VPS>:/root/
   ssh root@<IP_VPS> "chmod +x setup_vps.sh && ./setup_vps.sh"