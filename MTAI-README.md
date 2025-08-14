1. JSON 参数文件格式
假设前端会在共享文件夹 D:\MTAI_vmshare\input\params.json 写入以下内容：
{
    "input_pcap": "1.pcap",
    "delay": "10ms",
    "loss": "10%",
    "reorder": "10%"
}
input_pcap：前端给的原始 PCAP 文件名，位于 input 文件夹下
delay / loss / reorder：延迟、丢包率、乱序率。

2. Windows 主控脚本（auto_run.py）
这个脚本会：
读取 JSON 参数。
调用 modifypcap_final.py 修改 PCAP。
通过 SSH（用密钥）到 Kali2 启动抓包脚本。
通过 SSH（用密钥）到 Kali1 启动发包脚本。
全部完成后结束。
保存为 D:\MTAI_vmshare\auto_run.py：

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

3. SSH 免密钥登录配置
为了让 Windows 脚本无密码自动执行：

3.1 在 Windows 生成密钥
在 PowerShell 运行：
ssh-keygen -t rsa -b 4096
一路回车，默认生成到 C:\Users\<你的Windows用户名>\.ssh\id_rsa

3.2 复制公钥到 Kali1、Kali2
scp C:\Users\<你的Windows用户名>\.ssh\id_rsa.pub kali@61.139.2.134:/home/kali/.ssh/authorized_keys
scp C:\Users\<你的Windows用户名>\.ssh\id_rsa.pub kali@61.139.2.133:/home/kali/.ssh/authorized_keys
（如果 .ssh 目录不存在，在 Kali 里先 mkdir -p ~/.ssh && chmod 700 ~/.ssh）

4. 目录结构示例
D:\MTAI_vmshare
│
├─ auto_run.py
├─ modifypcap_final.py
├─ kali1_final.sh
├─ kali2_final.sh
├─ input
│   ├─ 1.pcap
│   └─ params.json
└─ output
    └─ （最终 server_final.pcap 会出现在这里）

5. README（执行步骤）
1.在 Windows 配置 SSH 免密钥登录（参考上面第3节）。

2.确保两个 Kali 虚拟机的共享目录 /mnt/hgfs/MTAI_vmshare 已挂载，并与 Windows 的 D:\MTAI_vmshare 对应。

3.确保两个虚拟机上 tcpreplay、tcpdump、tc、python3、scapy 已安装。

4.前端将 1.pcap 和 params.json 放到 D:\MTAI_vmshare\input。

5.在 Windows 打开 PowerShell，运行：
python D:\MTAI_vmshare\auto_run.py

6.等待运行结束，最终的 server_final.pcap 会出现在 D:\MTAI_vmshare\output。




对的，SSH 免密钥配置完成后，你在 Windows 物理机上就可以直接 SSH 登录 Kali，而不需要输入密码。
我给你分步骤讲一下怎么做和验证。

1. 在 Windows 物理机生成密钥对
打开 PowerShell（用管理员权限更好），输入：
ssh-keygen -t rsa -b 4096
一路按回车（Enter），使用默认路径：
C:\Users\<你的Windows用户名>\.ssh\id_rsa
C:\Users\<你的Windows用户名>\.ssh\id_rsa.pub
这个 id_rsa.pub 是公钥，id_rsa 是私钥（一定不能泄露）。

2. 把公钥复制到 Kali 虚拟机
2.1 Kali 虚拟机上确保 .ssh 目录存在
在 Kali 里运行：
mkdir -p ~/.ssh
chmod 700 ~/.ssh

2.2 从 Windows 复制公钥到 Kali
在 Windows PowerShell 中运行（替换用户名、IP）：
scp C:\Users\<你的Windows用户名>\.ssh\id_rsa.pub kali@61.139.2.134:/home/kali/

然后在 Kali 里执行：
cat ~/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
rm ~/id_rsa.pub
（对 Kali1 和 Kali2 都执行一次，IP 换成各自的）

3. 测试免密钥登录
在 Windows PowerShell 中直接运行：
ssh kali@61.139.2.134

如果一切正确，这一步不会要求输入密码，会直接登录到 Kali1。
同样：
ssh kali@61.139.2.133
直接登录 Kali2。