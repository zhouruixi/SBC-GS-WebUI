#!/usr/bin/python3

# pip install flask configobj paramiko scp
from flask import (
    Flask,
    Response,
    g,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_file,
    send_from_directory,
    render_template_string,
)
from flask_babel import Babel
from configobj import ConfigObj
from ruamel.yaml import YAML
import os
import subprocess
import paramiko
from scp import SCPClient
import time
from datetime import datetime
from pathlib import Path
import shutil
import threading
import base64
from glob import glob
from filemanager import bp as filemanager_bp
from plotter import bp as plotter_bp


config_info_file = "settings_webui.yaml"
# os.makedirs(MANAGER_FOLDER, exist_ok=True)
script_dir = Path(__file__).resolve().parent
yaml = YAML()
yaml.width = 4096


# load_yaml_config
def load_yaml_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        yaml_dict = yaml.load(file)
    return yaml_dict


# save_yaml_config
def save_yaml_config(config: dict, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        yaml.dump(
            config,
            file,
        )


# load_ini_config
def load_ini_config(file_path: str) -> ConfigObj:
    config = ConfigObj(file_path, encoding="utf-8")
    return config


# save_ini_config
def save_ini_config(config: ConfigObj, file_path: str) -> None:
    config.filename = file_path
    config.write()


# load_config
def load_config(config_info: dict, side: str, filename: str) -> dict:
    file_path = config_info[f"{side}_config"][filename]["path"]
    file_format = config_info[f"{side}_config"][filename]["format"]
    if file_format == "ini":
        return load_ini_config(file_path)
    elif file_format == "yaml":
        return load_yaml_config(file_path)
    else:
        raise ValueError("Unsupported file type. Use 'ini' 'yaml' or 'shell'.")


# diff dict and get new dict value
def get_new_dict_value(old: dict, new: dict) -> dict:
    new_kv = {k: new[k] for k in old if k in new and old[k] != new[k]}
    return new_kv


# file_to_base64
def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        # 读取文件内容
        file_content = file.read()
        # 对文件内容进行 Base64 编码
        encoded_content = base64.b64encode(file_content)
        # 返回编码后的内容，转换为字符串格式
        return encoded_content.decode("utf-8")


# base64_to_file
def base64_to_file(base64_string, output_file_path):
    # 将 Base64 编码的字符串解码为字节
    file_data = base64.b64decode(base64_string)

    # 将解码后的字节写入文件
    with open(output_file_path, "wb") as file:
        file.write(file_data)


class SSHClient:
    def __init__(self, host_conf):
        """
        初始化 SSH 客户端
        Args:
            host_conf (dict): 包含连接信息的字典，必须包含以下键:
                - hostname: 主机地址
                - username: 用户名
                - password: 密码
                - port: 端口号
        """
        self.hostname = host_conf["hostname"]
        self.username = host_conf["username"]
        self.password = host_conf["password"]
        self.port = host_conf["port"]
        self.client = None
        self.last_activity_time = None
        self.close_timer = None
        self.max_retries = 3
        self.retry_delay = 1  # 重试延迟秒数

    def _is_connection_active(self):
        """
        检查 SSH 连接是否处于活动状态
        Returns:
            bool: 连接是否活动
        """
        return (
            self.client is not None
            and self.client.get_transport() is not None
            and self.client.get_transport().is_active()
        )

    def connect(self):
        """
        建立 SSH 连接，如果已经存在活动连接则不会重新连接
        Raises:
            paramiko.ssh_exception.NoValidConnectionsError: 无法连接到目标主机
            paramiko.AuthenticationException: 认证失败
            paramiko.SSHException: SSH 连接失败
            Exception: 其他连接错误
        """
        if self._is_connection_active():
            print(f"Already connected to {self.hostname}. No need to reconnect.")
            return

        # 如果连接不活跃，先确保关闭旧连接
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None

        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        retry_count = 0
        last_exception = None

        while retry_count < self.max_retries:
            try:
                self.client.connect(
                    self.hostname,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    timeout=2,
                )
                self.last_activity_time = time.time()
                print(f"Connected to {self.hostname}")
                return
            except paramiko.ssh_exception.NoValidConnectionsError as e:
                print(
                    f"无法连接到目标主机 {self.hostname}, 尝试重连... (重试 {retry_count + 1}/{self.max_retries})"
                )
                last_exception = e
            except paramiko.AuthenticationException as e:
                print(
                    f"Authentication failed when connecting to {self.hostname}. Please check your username/password."
                )
                raise
            except paramiko.SSHException as e:
                print(f"SSH connection failed to {self.hostname}. SSH error: {str(e)}")
                last_exception = e
            except Exception as e:
                print(f"Failed to connect to {self.hostname}. Error: {str(e)}")
                last_exception = e

            retry_count += 1
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)

        if last_exception:
            raise last_exception

    def execute_command(self, command):
        """
        执行 SSH 命令
        Args:
            command (str): 要执行的命令
        Returns:
            str: 命令执行的输出
        Raises:
            ValueError: SSH 连接未建立
            Exception: 命令执行错误
        """
        if not self._is_connection_active():
            print("SSH connection is not active. Reconnecting...")
            self.connect()

        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")

        if error:
            raise Exception(f"Error executing command: {error}")

        self.last_activity_time = time.time()
        self._reset_close_timer()

        # print(output)
        return output

    def download_file(self, remote_path, local_path):
        """
        从远程服务器下载文件
        Args:
            remote_path (str): 远程文件路径
            local_path (str): 本地保存路径
        Raises:
            ValueError: 本地目录不存在
            Exception: 下载失败
        """
        if not self._is_connection_active():
            print("SSH connection is not active. Reconnecting...")
            self.connect()

        if not os.path.isdir(os.path.dirname(local_path)):
            raise ValueError(
                f"Local path directory does not exist: {os.path.dirname(local_path)}"
            )

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                with SCPClient(self.client.get_transport()) as scp:
                    print(f"Download from {remote_path} to {local_path}...")
                    scp.get(remote_path, local_path)
                    print(f"Download {remote_path} sucess.")
                    break
            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    print(
                        f"Download {remote_path} failed, attempting retry {retry_count}/{self.max_retries}..."
                    )
                    time.sleep(self.retry_delay)
                    self.connect()  # 重新连接
                else:
                    print(f"Failed to download {remote_path} after {self.max_retries} attempts.")
                    raise

        self.last_activity_time = time.time()
        self._reset_close_timer()

    def upload_file(self, local_path, remote_path):
        """
        上传文件到远程服务器
        Args:
            local_path (str): 本地文件路径
            remote_path (str): 远程保存路径
        Raises:
            FileNotFoundError: 本地文件不存在
            Exception: 上传失败
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local file does not exist: {local_path}")

        if not self._is_connection_active():
            print("SSH connection is not active. Reconnecting...")
            self.connect()

        retry_count = 0
        while retry_count < self.max_retries:
            try:
                with SCPClient(self.client.get_transport()) as scp:
                    scp.put(local_path, remote_path)
                    print(f"File uploaded from {local_path} to {remote_path}.")
                    break
            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    print(
                        f"Upload failed, attempting retry {retry_count}/{self.max_retries}..."
                    )
                    time.sleep(self.retry_delay)
                    self.connect()  # 重新连接
                else:
                    print(f"Failed to upload file after {self.max_retries} attempts.")
                    raise

        self.last_activity_time = time.time()
        self._reset_close_timer()

    def _reset_close_timer(self):
        """重置自动关闭连接的定时器"""
        if self.close_timer:
            self.close_timer.cancel()

        self.close_timer = threading.Timer(1000, self.close)  # 5分钟后自动关闭
        self.close_timer.start()

    def close(self):
        """关闭 SSH 连接"""
        if self.client:
            try:
                self.client.close()
                print("SSH connection closed.")
            except Exception as e:
                print(f"Error closing SSH connection: {str(e)}")
            finally:
                self.client = None
                if self.close_timer:
                    self.close_timer.cancel()


def format_size(size):
    """将字节大小转换为 KB、MB、GB"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


config_info = load_yaml_config(config_info_file)
app = Flask(__name__)
app.json.sort_keys = False  # 禁用 jsonify 自动排序
app.config['MANAGER_FOLDER'] = "/config"
ssh = SSHClient(config_info["drone_config"]["ssh"])
drone_firmware_type = config_info["drone_config"]["firmware_type"]
Videos_dir = load_config(config_info, "gs", "gs")["rec_dir"]
config_drone = {}
sysupgrade_stdout = None
babel = Babel(app)


@app.before_request
def before_request():
    g.plotter_settings = config_info["gs_config"]["plotter"]

def before_request():
    # 获取浏览器语言偏好
    g.locale = request.accept_languages.best_match(['en', 'zh', 'ru'])

# 如果配置中未指定天空端固件版本则自动获取
def get_drone_firmware_type():
    global drone_firmware_type
    if drone_firmware_type not in ['latest', 'legacy']:
        get_firmware_type_cmd = "[ -f /etc/wfb.conf ] && printf legacy || printf latest"
        try:
            ssh.connect()
            drone_firmware_type = ssh.execute_command(get_firmware_type_cmd)
        except Exception as e:
            print(f"Failed to get drone firmware version: {str(e)}")

# 注册蓝图
app.register_blueprint(filemanager_bp)
app.register_blueprint(plotter_bp)


@app.route("/")
def home():
    global config_info
    # 获取地面站外部IP
    server_host = request.headers.get("host")
    server_ip = server_host.split(":")[0]
    # 获取地面站配置文件列表
    gs_config_files_path = config_info["gs_config"]["gs_config_files"]
    for i in range(len(gs_config_files_path)):
        path = gs_config_files_path[i]
        if not path.startswith("/"):
            gs_config_files_path[i] = str(script_dir / path)
    # 获取启用的 GS 按钮
    gs_button_config = config_info["gs_config"]["button"]
    # 获取启用的 Drone 按钮
    drone_button_config = config_info["drone_config"]["button"]
    button_enabled = {}
    button_enabled["gs"] = gs_button_config
    button_enabled["drone"] = drone_button_config
    drone_quick_setting = config_info["drone_config"]["quick_setting"]
    return render_template(
        "index.html",
        server_ip=server_ip,
        gs_config_files_path=gs_config_files_path,
        button_enabled=button_enabled,
        drone_quick_setting=drone_quick_setting,
    )


@app.route("/load_gs_config/<filename>", methods=["GET"])
def load_gs_config(filename):
    # global config_gs
    # config_file_path = config_info["gs_config"][filename]["path"]
    # config_gs = load_ini_config(config_file_path)
    config_gs = load_config(config_info, "gs", filename)
    return jsonify(config_gs)


@app.route("/save_gs_config/<filename>", methods=["POST"])
def save_gs_config(filename):
    try:
        # global config_gs
        # 保存前先获取配置文件最新内容
        config_gs = load_config(config_info, "gs", filename)
        # 设置新的保存路径
        # config_file = config_info["gs_config"]["gs"]["path"] + ".new"
        # config_gs.filename = config_file
        # config_gs['br0_fixed_ip'] = '0.0.0.0/0'
        # config_gs.write()

        config_gs_old = dict(config_gs)
        config_gs_new = request.json
        update_content = get_new_dict_value(config_gs_old, config_gs_new)
        # print(f"【Updated】{update_content}")
        if not update_content:
            print("配置没有变化")
        else:
            update_command = "sed -i"
            # crudini --set gs.conf.bak DEFAULT "br0_fixed_ip" "'0.0.0.0/0'"
            for k, v in update_content.items():
                update_command += f''' -e "s/^{k}=.*/{k}='{v}'/g"'''
            update_command += (
                f" {config_info['gs_config'][filename]['path']} && echo success"
            )
            # print(update_command)
            # exec command
            update_command_result = subprocess.run(
                update_command, shell=True, capture_output=True, text=True
            )
            print(update_command_result)
            if update_command_result.returncode != 0:
                raise ValueError("sed替换文件时出错")  # 主动抛出异常
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/load_drone_config/<filename>", methods=["GET"])
def load_drone_config(filename):
    global config_drone
    config_drone[filename] = {}
    drone_files_dir = os.path.join(script_dir, "drone_files")
    os.makedirs(drone_files_dir, exist_ok=True)
    # 获取天空端固件版本
    get_drone_firmware_type()
    if drone_firmware_type not in ['latest', 'legacy']:
        return jsonify({"error": "Failed to get drone firmware version."}), 400
    if drone_firmware_type == "legacy" and filename == "wfb":
        try:
            ssh.connect()
            for file in ['wfb', 'datalink', 'telemetry']:
                config_file_remote = config_info["drone_config"][f"{file}_legacy"]["path"]
                config_file_local = f"drone_files/{os.path.basename(config_file_remote)}"
                ssh.download_file(config_file_remote, config_file_local)
                config = load_ini_config(config_file_local)
                config_drone[filename][file] = config.dict()
            return jsonify(config_drone[filename])
        except Exception as e:
            print(f"load configuration failed: {str(e)}")
            return jsonify({"error": "Failed to load configuration."}), 400
    else:
        try:
            ssh.connect()
            config_file_remote = config_info["drone_config"][filename]["path"]
            config_file_local = f"drone_files/{os.path.basename(config_file_remote)}"
            ssh.download_file(config_file_remote, config_file_local)
            config_drone[filename] = load_yaml_config(config_file_local)
            return jsonify(config_drone[filename])
        except Exception as e:
            print(f"load configuration failed: {str(e)}")
            return jsonify({"error": "Failed to load configuration."}), 400


@app.route("/save_drone_config/<filename>", methods=["POST"])
def save_drone_config(filename):
    if not config_drone[filename]:
        return jsonify({"success": False, "message": "请先获取配置"})
    config_drone_old = {}
    for file, content in config_drone[filename].items():
        for k, v in content.items():
            if v is True:
                v = "true"
            elif v is False:
                v = "false"
            # 待解决： 原始文件中的 1.0 小数会被转换为整数1
            config_drone_old[f"{file}.{k}"] = str(v)
    # print(f"【Old】{config_drone_old}")
    try:
        config_drone_new = request.json  # 获取前端传来的 JSON 数据
        if config_drone_new == {}:
            return jsonify({"success": False, "message": "请先加载配置！"})
        # 比较获取更新的设置及内容
        update_content = get_new_dict_value(config_drone_old, config_drone_new)
        # 初始化用于存储更新命令的变量
        update_command = ""
        update_content_legacy = {}
        # legacy固件wfb更新
        if drone_firmware_type == "legacy" and filename == "wfb":
            # 将表单转为二维字典
            for k, v in update_content.items():
                config_file, config_key = k.split('.', 1)
                if config_file not in update_content_legacy:
                    update_content_legacy[config_file] = {}
                update_content_legacy[config_file][config_key] = v
            # 遍历字典为每个文件生成一个更新命令
            for file, content in update_content_legacy.items():
                update_command_used = "sed -i"
                for option, vlaue in content.items():
                    update_command_used += f' -e "s/^{option}=.*/{option}={vlaue}/g"'
                file_path = config_info['drone_config'][f"{file}_legacy"]['path']
                update_command_used += f" {file_path} && "
                update_command += update_command_used
        else:
            if filename == "wfb":
                update_command_used = "wfb-cli"
            elif filename == "majestic":
                update_command_used = "cli"
            for k, v in update_content.items():
                update_command += f"{update_command_used} -s .{k} {v} && "
        update_command += "echo success"
        # print(update_command)

        ssh.connect()
        print("Executing remote command...")
        output = ssh.execute_command(update_command)
        print(f"Command Output: {output}")
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/exec_button_function", methods=["POST"])
def exec_button_function():
    # 获取前端发送的数据
    data = request.get_json()
    button_id = data.get("button_id")
    if button_id.startswith("gs_btn_"):
        # 地面站按钮
        function_name = button_id.removeprefix("gs_btn_")

        # 打印接收到的按钮ID
        # print(f"收到【地面站】按钮指令: {function_name}")
        button_command = config_info["gs_config"]["button"][function_name]["command"]
        print(f"Executing local command: {button_command}")
        button_command_result = subprocess.run(
            button_command, shell=True, capture_output=True, text=True
        )
        if button_command_result.returncode != 0:
            raise ValueError("执行按钮命令出错")  # 主动抛出异常
        else:
            # 返回按钮 ID
            return jsonify({"status": "success", "button_id": function_name})
    elif button_id.startswith("drone_btn_"):
        # 天空端按钮
        function_name = button_id.removeprefix("drone_btn_")
        # 打印接收到的按钮ID
        # print(f"收到【天空端】按钮指令: {function_name}")
        button_command = config_info["drone_config"]["button"][function_name]["command"]
        print(f"Executing drone command: {button_command}")
        try:
            ssh.connect()
            print(f"Executing remote command: {button_command}")
            output = ssh.execute_command(button_command)
            # print(f"Command Output: {output}")
            return jsonify({"success": True, "message": "命令已执行！"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
        # finally:
            # ssh.close()
    elif button_id.startswith("drone_setting_"):
        function_name = button_id.removeprefix("drone_setting_")
        target_value = data.get("target_value")
        function_info = config_info["drone_config"]["quick_setting"][function_name]
        if drone_firmware_type == "legacy" and "command_legacy" in function_info:
            command_template = function_info["command_legacy"]
        else:
            command_template = function_info["command"]
        button_command = command_template.format(target_value=target_value)
        try:
            ssh.connect()
            print(f"Executing drone command: {button_command}")
            ssh.execute_command(button_command)
            return jsonify({"success": True, "message": "命令已执行！"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})


# 下载配置文件
@app.route("/download_config/<path:filepath>")
def download_config(filepath):
    return send_file(f"/{filepath}", as_attachment=True)


@app.route("/edit/<path:filepath>", methods=["GET", "POST"])
def edit_file(filepath):
    filepath = os.path.join("/", filepath)
    global config_info

    if request.method == "GET":
        # 打开文件并读取内容
        try:
            with open(filepath, "r") as f:
                content = f.read()
            return jsonify({"content": content})
        except Exception as e:
            return jsonify({"error": f"无法读取文件: {str(e)}"}), 500

    elif request.method == "POST":
        # 获取编辑器内容并保存到文件
        content = request.json.get("content", "")
        try:
            with open(filepath, "w") as f:
                f.write(content)
            # 修改webui配置文件后重载配置
            if filepath == config_info_file:
                config_info = load_yaml_config(config_info_file)
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": f"保存文件失败: {str(e)}"}), 500


@app.route("/backup/<path:filepath>", methods=["POST"])
def backup_file(filepath):
    filepath = os.path.join("/", filepath)
    backup_filepath = f"{filepath}.bak"
    # 复制文件到新的备份文件路径
    shutil.copy(filepath, backup_filepath)
    return jsonify(
        {
            "status": "success",
            "message": f"File '{filepath}' backed up to {backup_filepath}.",
        }
    )


@app.route("/list_video_files")
def list_video_files():
    """返回文件列表（文件名 & 文件大小），不包括文件夹"""
    files = [
        {
            "name": f,
            "size": format_size(os.path.getsize(os.path.join(Videos_dir, f))),
        }
        for f in os.listdir(Videos_dir)
        if os.path.isfile(os.path.join(Videos_dir, f))
    ]
    # 按文件名排序
    files_sorted = sorted(files, key=lambda x: x["name"])
    return jsonify(files_sorted)


@app.route("/download_video/<filename>")
def download_video_file(filename):
    """提供文件下载"""
    return send_from_directory(Videos_dir, filename, as_attachment=True)


@app.route("/delete_video/<filename>", methods=["POST"])
def delete_video_file(filename):
    """删除指定文件"""
    file_path = os.path.join(Videos_dir, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "File not found"}), 404


@app.route("/load_wfb_key_config/", defaults={"current": None})
@app.route("/load_wfb_key_config/<current>", methods=["GET"])
def load_wfb_key_config(current):
    if current == "current":
        current_gs_key = file_to_base64("/etc/gs.key")
        get_drone_key_command = "base64 -w 0 /etc/drone.key"
        try:
            ssh.connect()
            current_drone_key = ssh.execute_command(get_drone_key_command)
        except Exception:
            current_drone_key = None
        return jsonify({"gs": current_gs_key, "drone": current_drone_key})
    else:
        wfb_key_config = config_info["wfb_key_pair"]
        return jsonify(wfb_key_config)


@app.route("/save_wfb_key_config/<keypair>", methods=["POST"])
def save_wfb_key_config(keypair):
    global config_info
    new_keypair_content = request.get_json()
    config_info["wfb_key_pair"][keypair] = new_keypair_content
    # 保存修改后的配置到文件
    save_yaml_config(config_info, config_info_file)
    return jsonify({"status": "success"})


@app.route("/apply_wfb_key/<side>", methods=["POST"])
def apply_wfb_key(side):
    def apply_wfb_key_drone(key_base64: str):
        update_drone_keycommand = f"echo '{key_base64}' | base64 -d > /etc/drone.key"
        ssh.connect()
        ssh.execute_command(update_drone_keycommand)

    try:
        keypair_content = request.get_json()
        if side == "name":
            base64_to_file(keypair_content["gs"], "/config/gs.key")
            apply_wfb_key_drone(keypair_content["drone"])
        elif side == "gs":
            base64_to_file(keypair_content["gs"], "/config/gs.key")
        elif side == "drone":
            apply_wfb_key_drone(keypair_content["drone"])
        else:
            print(f"无效的请求!")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": f"应用 key 失败: {str(e)}"}), 500


@app.route("/get_random_wfb_key", methods=["GET"])
def get_random_wfb_key():
    wfb_keygen_command = "cd /dev/shm && wfb_keygen"
    subprocess.run(wfb_keygen_command, shell=True)
    gs_key_path = "/dev/shm/gs.key"
    drone_key_path = "/dev/shm/drone.key"
    gs_key_base64 = file_to_base64(gs_key_path)
    drone_key_base64 = file_to_base64(drone_key_path)
    os.remove(gs_key_path)
    os.remove(drone_key_path)
    random_wfb_key = {"gs": gs_key_base64, "drone": drone_key_base64}
    return jsonify(random_wfb_key)


@app.route("/systeminfo/<side>")
def gs_systeminfo(side):
    if side == "gs":
        get_info_command = config_info["gs_config"]["systeminfo"]
        systeminfo = {}
        for info in get_info_command:
            command_result = subprocess.run(
                get_info_command[info], shell=True, capture_output=True, text=True
            )
            systeminfo[info] = command_result.stdout
        # print(systeminfo)
        return jsonify(systeminfo)
    elif side == "drone":
        get_info_command = config_info["drone_config"]["systeminfo"]
        try:
            ssh.connect()
            ssh.execute_command("echo success")
            systeminfo = {}
            for info in get_info_command:
                command_result = ssh.execute_command(get_info_command[info])
                systeminfo[info] = command_result
            # print(systeminfo)
            return jsonify(systeminfo)
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})



@app.route("/wifi_acs/", defaults={"wnic": None})
@app.route("/wifi_acs/<wnic>")
def wifi_acs(wnic):
    if wnic is None:
        available_nics = {}
        wfb_nics = load_config(config_info, "gs", "wfb_default")["WFB_NICS"].split()
        for nic in wfb_nics:
            driver_path = os.path.realpath(f"/sys/class/net/{nic}/device/driver")
            driver_name = os.path.basename(driver_path)
            if driver_name in ["rtl88x2cu", "rtl88x2eu", "rtl8733bu"]:
                available_nics[nic] = driver_name
        return jsonify(available_nics)
    else:
        scan_command = f"iw {wnic} scan passive"
        subprocess.run(scan_command, shell=True)
        proc_path = glob(f"/proc/net/rtl*/{wnic}")[0]
        acs_result = {}
        for file in ["acs", "chan_info"]:
            with open(f"{proc_path}/{file}", "r") as f:
                acs_result[file] = f.read()
        return jsonify(acs_result)


# 上传和升级操作
@app.route("/upgrade/<operate>", methods=["GET", "POST"])
def upgrade_firmware(operate):
    # 设置上传文件夹
    firmware_dir = os.path.join(script_dir, 'firmware')
    os.makedirs(firmware_dir, exist_ok=True)
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {'tgz', 'tar.gz'}
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    def execute_sysupgrade_command(command):
        """ 执行 SSH 命令并将输出存入缓存 """
        global sysupgrade_stdout
        sysupgrade_stdout = []
        # 封装的SSHClient类无法工作
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**config_info["drone_config"]["ssh"])
        stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
        try:
            buffer = ""
            while True:
                while stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(1)
                    if not chunk:
                        break
                    decoded_char = chunk.replace(b'\r', b'\n').decode()
                    if decoded_char == '\n':
                        if buffer:
                            sysupgrade_stdout.append(buffer)
                            print(buffer)
                            buffer = ""
                    else:
                        buffer += decoded_char
                if stdout.channel.exit_status_ready():
                    trailing_data = stdout.channel.recv(4096)
                    while trailing_data:
                        buffer += trailing_data.replace(b'\r', b'\n').decode()
                        trailing_data = stdout.channel.recv(4096)
                    if buffer:
                        sysupgrade_stdout.append(buffer)
                        print(buffer)
                    break
                time.sleep(0.1)
        except Exception as e:
            print(str(e))

    if operate == 'list':
        # 列出固件
        firmwares = []
        for filename in os.listdir(firmware_dir):
            if allowed_file(filename):
                firmwares.append(filename)
        return jsonify({'firmwares': firmwares})
    elif operate == 'upload' and request.method == "POST":
        # 上传固件
        if 'firmware' in request.files:
            file = request.files['firmware']
            filename = file.filename
            file.save(os.path.join(firmware_dir, filename))
            return jsonify({'message': f'固件 {filename} 上传成功'}), 200
        else:
            return jsonify({'message': '没有选择固件'}), 400
    elif operate == 'delete' and request.method == "POST":
        firmware = request.form.get('firmware')
        if not firmware:
            return jsonify({'message': '没有指定固件文件'}), 400
        firmware_path = os.path.join(firmware_dir, firmware)
        if not os.path.exists(firmware_path):
            return jsonify({'message': '固件文件不存在'}), 400
        try:
            os.remove(firmware_path)
            return jsonify({'message': f'固件 {firmware} 删除成功'}), 200
        except Exception as e:
            return jsonify({'message': f'删除失败: {str(e)}'}), 500
    elif operate == 'send' and request.method == "POST":
        # 发送固件到Drone
        firmware = request.form.get('firmware')
        firmware_path = os.path.join(firmware_dir, firmware)
        try:
            ssh.connect()
            print("Kill majestic")
            ssh.execute_command('[ -n "$(pidof majestic)" ] && killall majestic')
            print(f"uploading {firmware}...")
            ssh.upload_file(firmware_path, f"/tmp/{firmware}")
            return jsonify({'message': '固件发送成功'}), 200
        except Exception as e:
            return jsonify({'message': f'固件发送失败: {str(e)}'}), 500
    elif operate == 'execute' and request.method == "POST":
        # 升级固件
        firmware = request.form.get('firmware')
        firmware_path = os.path.join(firmware_dir, firmware)
        try:
            firmware_gs_md5 = subprocess.run(f"md5sum {firmware_path} | cut -d \  -f 1", shell=True, capture_output=True, text=True).stdout
            firmware_drone_md5 = ssh.execute_command(f"[ -f /tmp/{firmware} ] && md5sum /tmp/{firmware} | cut -d \  -f 1 || echo FileNotFound")
            if firmware_gs_md5 == firmware_drone_md5:
                upgrade_command = f"gzip -d /tmp/{firmware} -c | tar xf - -C /tmp && soc=$(fw_printenv -n soc) && sysupgrade --kernel=/tmp/uImage.$soc --rootfs=/tmp/rootfs.squashfs.$soc -n"
                print(f"正在升级固件: {upgrade_command}")
                threading.Thread(target=execute_sysupgrade_command, args=(upgrade_command,)).start()  # 在新线程执行
                return jsonify({'message': '固件升级指令发送成功，请等待升级完成。'}), 200
            else:
                return jsonify({'message': '固件未上传或校验未通过，请重新上传firmware！'}), 200
        except Exception as e:
            return jsonify({'message': f'升级失败: {str(e)}'}), 500
    elif operate == 'progress' and request.method == "GET":
        def generate():
            previous_length = 0
            while True:
                if sysupgrade_stdout:
                    new_output = sysupgrade_stdout[previous_length:]  # 只获取新行
                    for line in new_output:
                        yield f"data: {line}\n\n"  # SSE 格式推送
                    previous_length = len(sysupgrade_stdout)  # 更新已发送的行数
                time.sleep(0.1)  # 限制推送频率，避免过载
        return Response(generate(), mimetype="text/event-stream")
    else:
        return jsonify({'message': '无效的操作'}), 400


# 根据客户端设置系统时间
@app.route('/sync-time', methods=['POST'])
def sync_time():
    data = request.get_json()
    if 'time' not in data or 'timezone' not in data:
        return jsonify({"error": "缺少参数"}), 400
    try:
        # 解析 ISO 8601 时间
        client_time = datetime.fromisoformat(data['time'].replace("Z", "+00:00"))
        formatted_time = client_time.strftime('%Y-%m-%d %H:%M:%S')
        # 获取时区信息
        timezone = data['timezone']
        # 设置时间
        subprocess.run(["date", "-u", "-s", formatted_time], check=True)
        # 设置时区
        subprocess.run(["timedatectl", "set-timezone", timezone], check=True)
        subprocess.run(["fake-hwclock", "save"], check=True)
        response = {"message": "服务器时间和时区已更新", "new_time": formatted_time, "new_timezone": timezone}
        print("同步成功:", response)
        return jsonify(response)
    except Exception as e:
        print("同步失败:", str(e))
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=True)
