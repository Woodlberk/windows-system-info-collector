# Windows System Info Collector

A simple Python script that collects basic Windows system information and saves it to a text file.

## How to Use
1. Ensure Python 3.x is installed on your Windows machine
2. Download `windows_system_info_collector.py`
3. Double-click the file OR run `python windows_system_info_collector.py` in Command Prompt
4. A timestamped report file (like `system_info_report_20260611_144804.txt`) will be created
5. Open the .txt file to view your system information

## or
1. dowload the Release and run the .bat file

## Example Output
```
WINDOWS SYSTEM INFORMATION
==========================

Timestamp: 2026-06-11 14:47:58

--- SYSTEM ---
OS:          Windows 11 (Professional)
Version:     11
Build:       10.0.26100
Architecture:64bit
Computer:    YOUR-PC-NAME

--- DISK ---
C:\ [NTFS] 853.3GB/929.4GB used (91.8%)

--- NETWORK ---
Interface:   YOUR-PC-NAME
IP:          192.168.0.5
Gateway:     192.168.0.1

--- SECURITY ---
TPM:         Present, v2.0, Ready
Hotfixes:    3 installed (KB5034441, KB5035849, KB5036892)

==========================
```
