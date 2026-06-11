import platform
import socket
import os
import sys
import datetime
import subprocess
import ipaddress
try:
    import winreg
except ImportError:
    winreg = None
try:
    import ctypes
except ImportError:
    ctypes = None

def get_os_info():
    try:
        os_name = platform.system()
        os_release = platform.release()
        os_version = platform.version()
        if hasattr(platform, 'win32_edition'):
            os_edition = platform.win32_edition()
        else:
            os_edition = "N/A"
        architecture = platform.architecture()[0]
        full_name = f"{os_name} {os_release} ({os_edition})"
        return {'name': os_name, 'release': os_release, 'version': os_version, 'edition': os_edition, 'architecture': architecture, 'full_name': full_name}
    except:
        return {'error': 'Failed to get OS info'}

def get_hostname():
    try:
        return socket.gethostname()
    except:
        return 'Unknown'

def get_drive_list():
    if not ctypes:
        return []
    try:
        drives = []
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetLogicalDriveStringsW(1024, buf)
        for drive in buf.value.split('\x00'):
            if drive:
                drives.append(drive)
        return drives
    except:
        return []

def get_disk_info(drive_letter):
    if not ctypes:
        return {'error': 'no ctypes'}
    try:
        drive = drive_letter.strip()
        if not drive.endswith('\\'):
            drive = drive + '\\'
        free_bytes = ctypes.c_ulonglong(0)
        total_bytes = ctypes.c_ulonglong(0)
        if ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(drive), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes)):
            total = total_bytes.value
            free = free_bytes.value
            used = total - free
            percent_used = (used / total * 100) if total > 0 else 0
            fs_name_buf = ctypes.create_unicode_buffer(256)
            ret = ctypes.windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(drive), None, 0, None, None, None, fs_name_buf, 256)
            if ret:
                fs_name = fs_name_buf.value
            else:
                fs_name = 'Unknown'
            return {'drive': drive[:-1], 'filesystem': fs_name, 'total_bytes': total, 'used_bytes': used, 'free_bytes': free, 'percent_used': round(percent_used, 1)}
        else:
            return {'error': 'GetDiskFreeSpaceExW failed'}
    except:
        return {'error': 'disk info error'}

def format_bytes(bytes_value):
    if bytes_value == 0:
        return "0B"
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while bytes_value >= 1024 and i < len(size_names) - 1:
        bytes_value /= 1024.0
        i += 1
    if i == 0:
        return f"{int(bytes_value)}{size_names[i]}"
    else:
        return f"{bytes_value:.1f}{size_names[i]}"

def get_network_info():
    try:
        hostname = socket.gethostname()
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip_address = s.getsockname()[0]
        except:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return {'hostname': hostname, 'ip_address': ip_address}
    except:
        return {'error': 'network info failed'}

def get_tpm_info():
    tpm_info = {'present': False, 'version': 'N/A', 'manufacturer': 'N/A', 'status': 'Unknown'}
    try:
        if winreg:
            try:
                key_path = r"SYSTEM\CurrentControlSet\Services\TPM"
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
                tpm_info['present'] = True
                try:
                    version, _ = winreg.QueryValueEx(key, "Version")
                    tpm_info['version'] = str(version)
                except:
                    pass
                try:
                    manufacturer, _ = winreg.QueryValueEx(key, "Manufacturer")
                    tpm_info['manufacturer'] = str(manufacturer)
                except:
                    pass
            except:
                pass
        if tpm_info['present'] and subprocess:
            try:
                cmd = ['powershell', '-command', 'Get-WmiObject -Namespace "root\\CIMv2\\Security\\MicrosoftTpm" -Class Win32_Tpm | Select-Object SpecVersion, ManufacturerVersion, IsEnabled_InitialValue, IsActivated_InitialValue']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            if key == 'SpecVersion':
                                tpm_info['version'] = value
                            elif key == 'ManufacturerVersion':
                                tpm_info['manufacturer'] = value
                            elif key in ['IsEnabled_InitialValue', 'IsActivated_InitialValue']:
                                if value.lower() == 'true':
                                    tpm_info['status'] = 'Ready'
                                else:
                                    tpm_info['status'] = 'Not Ready'
            except:
                pass
        if tpm_info['present'] and tpm_info['status'] == 'Unknown':
            tpm_info['status'] = 'Present'
    except:
        tpm_info['error'] = 'TPM info error'
    return tpm_info

def get_hotfix_info():
    try:
        hotfixes = []
        cmd = ['wmic', 'qfe', 'get', 'HotFixID', '/format:csv']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2 and parts[0] and parts[0] != 'HotFixID':
                        hotfix_id = parts[0].strip()
                        if hotfix_id and hotfix_id != 'HotFixID':
                            hotfixes.append({'id': hotfix_id})
        limited_hotfixes = hotfixes[:5] if hotfixes else []
        return {'count': len(hotfixes), 'recent': limited_hotfixes, 'list': [hf['id'] for hf in limited_hotfixes] if limited_hotfixes else []}
    except:
        return {'error': 'hotfix info failed', 'count': 0, 'recent': [], 'list': []}

def generate_full_report():
    report_lines = []
    report_lines.append("WINDOWS SYSTEM INFORMATION")
    report_lines.append("==========================")
    report_lines.append("")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_lines.append(f"Timestamp: {timestamp}")
    report_lines.append("")
    report_lines.append("--- SYSTEM ---")
    os_info = get_os_info()
    if 'error' not in os_info:
        report_lines.append(f"OS:          {os_info['full_name']}")
        report_lines.append(f"Version:     {os_info['release']}")
        report_lines.append(f"Build:       {os_info['version']}")
        report_lines.append(f"Architecture:{os_info['architecture']}")
    else:
        report_lines.append(f"OS:          {os_info.get('error', 'Unknown')}")
    hostname = get_hostname()
    report_lines.append(f"Computer:    {hostname}")
    report_lines.append("")
    report_lines.append("--- DISK ---")
    drives = get_drive_list()
    if drives:
        for drive in drives:
            disk_info = get_disk_info(drive)
            if 'error' not in disk_info:
                total_str = format_bytes(disk_info['total_bytes'])
                used_str = format_bytes(disk_info['used_bytes'])
                free_str = format_bytes(disk_info['free_bytes'])
                percent = disk_info['percent_used']
                report_lines.append(f"{drive} [{disk_info['filesystem']}] {used_str}/{total_str} used ({percent}%)")
            else:
                report_lines.append(f"{drive} [{disk_info.get('error', 'Error')}]")
    else:
        report_lines.append("No drives found or unable to detect drives")
    report_lines.append("")
    report_lines.append("--- NETWORK ---")
    net_info = get_network_info()
    if 'error' not in net_info:
        report_lines.append(f"Interface:   {net_info.get('hostname', 'Unknown')}")
        report_lines.append(f"IP:          {net_info.get('ip_address', 'Unknown')}")
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for i, line in enumerate(lines):
                    if 'Default Gateway' in line and i+1 < len(lines):
                        gateway_line = lines[i+1].strip()
                        if gateway_line:
                            import re
                            ips = re.findall(r'\d+\.\d+\.\d+\.\d+', gateway_line)
                            if ips:
                                report_lines.append(f"Gateway:     {ips[0]}")
                            break
        except:
            pass
    else:
        report_lines.append(f"Error: {net_info.get('error', 'Unknown')}")
    report_lines.append("")
    report_lines.append("--- SECURITY ---")
    tpm_info = get_tpm_info()
    if 'error' not in tpm_info:
        tpm_status = tpm_info.get('status', 'Unknown')
        tpm_version = tpm_info.get('version', 'N/A')
        tpm_manufacturer = tpm_info.get('manufacturer', 'N/A')
        if tpm_info.get('present', False):
            report_lines.append(f"TPM:         {tpm_manufacturer} v{tpm_version} ({tpm_status})")
        else:
            report_lines.append("TPM:         Not detected")
    else:
        report_lines.append(f"TPM:         Error - {tpm_info.get('error', 'Unknown')}")
    hotfix_info = get_hotfix_info()
    if 'error' not in hotfix_info:
        count = hotfix_info.get('count', 0)
        recent_list = hotfix_info.get('list', [])
        if recent_list:
            hotfix_str = ', '.join(recent_list[:3])
            if len(recent_list) > 3:
                hotfix_str += f", ...(+{len(recent_list)-3} more)"
            report_lines.append(f"Hotfixes:    {count} installed ({hotfix_str})")
        else:
            report_lines.append(f"Hotfixes:    {count} installed")
    else:
        report_lines.append(f"Hotfixes:    Error - {hotfix_info.get('error', 'Unknown')}")
    report_lines.append("")
    report_lines.append("=" * 26)
    return "\n".join(report_lines)

def save_report(content):
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"system_info_report_{timestamp}.txt"
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    except:
        print("Error saving report")
        return None

def main():
    print("Windows System Information Collector")
    print("=" * 40)
    print("Collecting system information...")
    try:
        report_content = generate_full_report()
        saved_path = save_report(report_content)
        print("\n" + report_content)
        if saved_path:
            print(f"\nReport saved to: {saved_path}")
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except:
        print("\nAn unexpected error occurred")
        sys.exit(1)
    if len(sys.argv) == 1:
        try:
            input("\nPress Enter to exit...")
        except:
            pass

if __name__ == "__main__":
    main()