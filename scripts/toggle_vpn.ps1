param (
    [string]$TunnelName = "VPS-Manager-SG-FREE-4"
)

# Xóa khoảng trắng thừa trong tên server
$TunnelName = $TunnelName.Trim()

# 1. Định vị đường dẫn file wireguard.exe trên Windows
$wgExe = "$env:ProgramFiles\WireGuard\wireguard.exe"
if (-not (Test-Path $wgExe)) {
    $wgExe = "${env:ProgramFiles(x86)}\WireGuard\wireguard.exe"
}

# Kiểm tra nếu máy chưa cài WireGuard
if (-not (Test-Path $wgExe)) {
    [System.Windows.Forms.MessageBox]::Show("Không tìm thấy WireGuard trên máy tính! Vui lòng kiểm tra lại cài đặt WireGuard.", "Lỗi Hệ Thống")
    exit
}

# 2. Thư mục lưu cấu hình mặc định của WireGuard
$wgConfigDir = "$env:ProgramFiles\WireGuard\Data\Configurations"
$wgConfigPathDpapi = Join-Path $wgConfigDir "$TunnelName.conf.dpapi"
$wgConfigPathConf  = Join-Path $wgConfigDir "$TunnelName.conf"

# 3. Đường dẫn file .conf nguồn trong thư mục bin/vps của dự án
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Split-Path -Parent $ScriptDir
$vpsConfigPath = Join-Path $ProjectDir "bin\vps\$TunnelName.conf"

function Toggle-WireGuard {
    # Tên Windows Service chuẩn của WireGuard
    $serviceName = "WireGuardTunnel`$$TunnelName"
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

    # -------------------------------------------------------------
    # TRƯỜNG HỢP 1: VPN Đang chạy -> Ngắt kết nối (Uninstall Service)
    # -------------------------------------------------------------
    if ($service -and $service.Status -eq "Running") {
        Start-Process $wgExe -ArgumentList "/uninstalltunnelservice ""$TunnelName""" -Wait -WindowStyle Hidden
        return
    }

    # -------------------------------------------------------------
    # TRƯỜNG HỢP 2: VPN Chưa chạy -> Kích hoạt & Tự động kết nối
    # -------------------------------------------------------------
    $fileToInstall = $null

    # Ưu tiên 1: Lấy file nguồn từ folder bin/vps
    if (Test-Path $vpsConfigPath) {
        # Đảm bảo folder Configurations của WireGuard đã tồn tại
        if (-not (Test-Path $wgConfigDir)) {
            New-Item -ItemType Directory -Path $wgConfigDir -Force | Out-Null
        }
        
        # Copy file sang folder hệ thống để đảm bảo WireGuard nhận diện
        Copy-Item -Path $vpsConfigPath -Destination $wgConfigPathConf -Force
        Start-Sleep -Milliseconds 500
        
        $fileToInstall = $vpsConfigPath
    } 
    # Ưu tiên 2: Sử dụng file đã tồn tại sẵn trong WireGuard
    elseif (Test-Path $wgConfigPathConf) {
        $fileToInstall = $wgConfigPathConf
    } 
    elseif (Test-Path $wgConfigPathDpapi) {
        $fileToInstall = $wgConfigPathDpapi
    }

    # Thực thi cài đặt Service và Kích hoạt VPN
    if ($fileToInstall) {
        Start-Process $wgExe -ArgumentList "/installtunnelservice ""$fileToInstall""" -Wait -WindowStyle Hidden
    } else {
        [System.Windows.Forms.MessageBox]::Show("Không tìm thấy file cấu hình $TunnelName.conf trong thư mục bin/vps!", "Lỗi VPN Manager")
    }
}

Toggle-WireGuard