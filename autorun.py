import json
import subprocess
import time
import os

# ========== 配置区 ==========
KALI1_USER = "kali"
KALI1_IP = "61.139.2.134"
KALI2_USER = "kali"
KALI2_IP = "61.139.2.133"
SSH_KEY_PATH = r"C:\Users\<你的Windows用户名>\.ssh\id_rsa"

SHARE_DIR_WIN = r"D:\MTAI_vmshare"
SHARE_DIR_VM = "/mnt/hgfs/MTAI_vmshare"
# ============================

# 1. 读取 JSON 参数
with open(os.path.join(SHARE_DIR_WIN, "input", "params.json"), "r", encoding="utf-8") as f:
    params = json.load(f)

input_pcap = params["input_pcap"]
delay = params["delay"]
loss = params["loss"]
reorder = params["reorder"]

modified_pcap = f"modified_{input_pcap}"

# 2. 运行 modifypcap_final.py 修改 pcap
print("[主控] 正在修改 PCAP 文件...")
subprocess.run([
    "python", os.path.join(SHARE_DIR_WIN, "modifypcap_final.py"),
    "--input", os.path.join(SHARE_DIR_VM, "input", input_pcap),
    "--output", os.path.join(SHARE_DIR_VM, "input", modified_pcap),
    "--new-client-ip", KALI1_IP,
    "--new-server-ip", KALI2_IP,
    "--src-mac", "00:0c:29:b8:68:f9",
    "--dst-mac", "00:0c:29:b7:d9:c7"
], check=True)

# 3. SSH 启动 Kali2 抓包
print("[主控] 启动 Kali2 抓包...")
subprocess.Popen([
    "ssh", "-i", SSH_KEY_PATH, f"{KALI2_USER}@{KALI2_IP}",
    f"bash {os.path.join(SHARE_DIR_VM, 'kali2_final.sh')} --delay '{delay}' --loss '{loss}' --reorder '{reorder}' --output-dir '{os.path.join(SHARE_DIR_VM, 'output')}' --server-ip '{KALI2_IP}' --client-ip '{KALI1_IP}'"
])

time.sleep(3)  # 给 Kali2 抓包一些启动时间

# 4. SSH 启动 Kali1 发包
print("[主控] 启动 Kali1 发包...")
subprocess.run([
    "ssh", "-i", SSH_KEY_PATH, f"{KALI1_USER}@{KALI1_IP}",
    f"bash {os.path.join(SHARE_DIR_VM, 'kali1_final.sh')} --delay '{delay}' --loss '{loss}' --reorder '{reorder}' --input-dir '{os.path.join(SHARE_DIR_VM, 'input')}' --modified-pcap '{modified_pcap}' --server-ip '{KALI2_IP}' --client-ip '{KALI1_IP}'"
], check=True)

print("[主控] 任务完成！请在 output 文件夹中查看 server_final.pcap")
