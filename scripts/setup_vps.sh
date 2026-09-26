#!/bin/bash
set -e

echo "=== CẬP NHẬT HỆ THỐNG ==="
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget wireguard openresolv net-tools

echo "=== CÀI ĐẶT CLOUDFLARE WARP CLI ==="
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/cli $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
sudo apt update && sudo apt install cloudflare-warp -y

echo "=== KẾT NỐI CLOUDFLARE WARP ==="
warp-cli registration new
warp-cli mode warp
warp-cli connect

echo "=== CÀI ĐẶT WIREGUARD SERVER ==="
wget https://raw.githubusercontent.com/NygrenH/wireguard-install/master/wireguard-install.sh -O wireguard-install.sh
chmod +x wireguard-install.sh
./wireguard-install.sh