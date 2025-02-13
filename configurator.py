#!/usr/bin/python3

# pip install flask configobj paramiko scp
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    send_from_directory,
    render_template_string,
)
from configobj import ConfigObj
import yaml
import os
import subprocess
import paramiko
from scp import SCPClient
import mimetypes
import time
from pathlib import Path
import shutil
import threading
import base64


# load_yaml_config
def load_yaml_config(file_path: str) -> dict:
    with open(file_path, "r") as file:
        yaml_dict = yaml.safe_load(file)
    return yaml_dict


# save_yaml_config
def save_yaml_config(config: dict, file_path: str) -> None:
    with open(file_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            config,
            file,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
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
    file_path = config_info[f"{side}_config_files"][filename]["path"]
    file_format = config_info[f"{side}_config_files"][filename]["format"]
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
                - host: 主机地址
                - username: 用户名
                - password: 密码
                - port: 端口号
        """
        self.host = host_conf["host"]
        self.username = host_conf["username"]
        self.password = host_conf["password"]
        self.port = host_conf["port"]
        self.client = None
        self.last_activity_time = None
        self.close_timer = None
        self.max_retries = 3
        self.retry_delay = 2  # 重试延迟秒数

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
            print(f"Already connected to {self.host}. No need to reconnect.")
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
                    self.host,
                    username=self.username,
                    password=self.password,
                    port=self.port,
                    timeout=5,
                )
                self.last_activity_time = time.time()
                print(f"Connected to {self.host}")
                return
            except paramiko.ssh_exception.NoValidConnectionsError as e:
                print(
                    f"无法连接到目标主机 {self.host}, 尝试重连... (重试 {retry_count + 1}/{self.max_retries})"
                )
                last_exception = e
            except paramiko.AuthenticationException as e:
                print(
                    f"Authentication failed when connecting to {self.host}. Please check your username/password."
                )
                raise
            except paramiko.SSHException as e:
                print(f"SSH connection failed to {self.host}. SSH error: {str(e)}")
                last_exception = e
            except Exception as e:
                print(f"Failed to connect to {self.host}. Error: {str(e)}")
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

        print(output)
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
                    scp.get(remote_path, local_path)
                    print(f"File downloaded from {remote_path} to {local_path}.")
                    break
            except Exception as e:
                retry_count += 1
                if retry_count < self.max_retries:
                    print(
                        f"Download failed, attempting retry {retry_count}/{self.max_retries}..."
                    )
                    time.sleep(self.retry_delay)
                    self.connect()  # 重新连接
                else:
                    print(f"Failed to download file after {self.max_retries} attempts.")
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

        self.close_timer = threading.Timer(300, self.close)  # 5分钟后自动关闭
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


app = Flask(__name__)
app.json.sort_keys = False  # 禁用 jsonify 自动排序


@app.route("/")
def home():
    server_host = request.headers.get("host")
    server_ip = server_host.split(":")[0]
    gs_config_files_path = [
        item["path"] for item in config_info["gs_config_files"].values()
    ]
    gs_config_files_path.append(config_info_file)
    return render_template(
        "index.html", server_ip=server_ip, gs_config_files_path=gs_config_files_path
    )


@app.route("/load_gs_config/<filename>", methods=["GET"])
def load_gs_config(filename):
    # global config_gs
    # config_file_path = config_info["gs_config_files"][filename]["path"]
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
        # config_file = config_info["gs_config_files"]["gs"]["path"] + ".new"
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
                f" {config_info['gs_config_files'][filename]['path']} && echo success"
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
    # global config_drone
    # 从文件载入配置
    # config_file = config_info["drone_config_files"][filename]["path"]
    # config_drone = load_yaml_config(config_file)
    # print(f"【Load】{config_drone}")

    config_file_remote = config_info["drone_config_files"][filename]["path"]
    config_file_local = f"drone_files/{os.path.basename(config_file_remote)}"
    # print(config_file_remote)
    # print(config_file_local)
    try:
        ssh.connect()
        print("Downloading file...")
        ssh.download_file(config_file_remote, config_file_local)
        print("File downloaded successfully.")

        config_drone = load_yaml_config(config_file_local)
        return jsonify(config_drone)
    except EOFError as e:
        # 捕捉EOFError并记录错误
        print(f"EOFError: 网络连接中断或远程服务器关闭连接: {str(e)}")
        # 可以选择重试逻辑或者其他恢复策略
        return jsonify({"error": "Failed to load configuration."}), 400
    except Exception as e:
        # 捕捉其他所有异常并记录
        print(f"发生了其他错误: {str(e)}")
        return jsonify({"error": "Failed to load configuration."}), 400
    finally:
        # ssh.close()
        pass


@app.route("/save_drone_config/<filename>", methods=["POST"])
def save_drone_config(filename):
    # global config_drone
    config_drone = load_yaml_config(f"drone_files/{filename}.yaml")

    # config_file = config_info["drone_config_files"][filename]["path"]
    # config_drone = load_yaml_config(config_file)
    config_drone_old = {}
    for file, content in config_drone.items():
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
        # print(f"【New】{config_drone_new}")
        if config_drone_new == {}:
            return jsonify({"success": False, "message": "请先加载配置！"})
        # update_content = {k: config_drone_new[k] for k in config_drone_old if k in config_drone_new and config_drone_old[k] != config_drone_new[k]}
        update_content = get_new_dict_value(config_drone_old, config_drone_new)
        # print(update_content)
        update_command = ""
        update_command_used = ""
        if filename == "wfb":
            update_command_used = "wfb-cli"
        elif filename == "majestic":
            update_command_used = "cli"
        else:
            update_command_used = ""
        for k, v in update_content.items():
            update_command += f"{update_command_used} -s .{k} {v} && "
        update_command += "echo success"
        print(update_command)
        try:
            ssh.connect()
            print("Executing remote command...")
            output = ssh.execute_command(update_command)
            print(f"Command Output: {output}")
        finally:
            # ssh.close()
            pass
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
        print(f"收到【地面站】按钮指令: {function_name}")
        button_command = f"/gs/button.sh {function_name}"
        print(f"执行命令：{button_command}")
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
        # 函数名和命令映射字典
        drone_function_command = {
            "reboot_drone": "reboot",
            "shutdown_drone": "poweroff",
            "restart_majestic": "killall -1 majestic",
            "restart_wfb": "/etc/init.d/S98wifibroadcast stop && /etc/init.d/S98wifibroadcast start &",
            "firstboot_drone": "firstboot &",
            "test": "echo test drone",
        }

        # 打印接收到的按钮ID
        print(f"收到【天空端】按钮指令: {function_name}")
        button_command = drone_function_command[function_name]
        print(f"执行命令：{button_command}")
        try:
            ssh.connect()
            print("Executing remote command...")
            output = ssh.execute_command(button_command)
            print(f"Command Output: {output}")
            return jsonify({"success": True, "message": "命令已执行！"})
        except Exception as e:
            return jsonify({"success": False, "message": str(e)})
        finally:
            # ssh.close()
            pass


@app.route("/filemanager/")
@app.route("/filemanager/<path:subpath>")
def index(subpath=""):
    base_path = os.path.join(MANAGER_FOLDER, subpath)
    if not os.path.exists(base_path):
        return redirect("/")

    files = []
    for item in os.listdir(base_path):
        full_path = os.path.join(base_path, item)
        is_dir = os.path.isdir(full_path)
        rel_path = os.path.join(subpath, item) if subpath else item
        file_size = os.path.getsize(full_path) if not is_dir else 0
        file_type, _ = mimetypes.guess_type(full_path)
        file_type = file_type if file_type else "Unknown"
        created_time = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getctime(full_path))
        )

        item_info = {
            "name": item,
            "path": rel_path,
            "is_dir": is_dir,
            "size": format_size(file_size),
            "type": "Folder" if is_dir else file_type,
            "created": created_time,
        }
        files.append(item_info)

    # 生成面包屑导航
    breadcrumb = [{"name": "Home", "path": "filemanager"}]
    path_parts = subpath.split("/") if subpath else []
    cumulative_path = "filemanager"
    for part in path_parts:
        cumulative_path = os.path.join(cumulative_path, part)
        breadcrumb.append({"name": part, "path": cumulative_path})

    return render_template(
        "filemanager.html",
        files=files,
        current_path=subpath,
        parent_path=os.path.dirname(subpath),
        breadcrumb=breadcrumb,
    )


@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files["file"]
    subpath = request.form.get("current_path", "")
    if file:
        save_path = os.path.join(MANAGER_FOLDER, subpath, file.filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
    return redirect(url_for("index", subpath=subpath))


@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form["folder_name"]
    subpath = request.form.get("current_path", "")
    new_folder = os.path.join(MANAGER_FOLDER, subpath, folder_name)
    os.makedirs(new_folder, exist_ok=True)
    return redirect(url_for("index", subpath=subpath))


@app.route("/delete/<path:filepath>")
def delete_file(filepath):
    full_path = os.path.join(MANAGER_FOLDER, filepath)
    parent_dir = os.path.dirname(filepath)
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    else:
        os.remove(full_path)
    return redirect(url_for("index", subpath=parent_dir))


@app.route("/download/<path:filepath>")
def download_file(filepath):
    return send_from_directory(MANAGER_FOLDER, filepath, as_attachment=True)


@app.route("/preview/<path:filepath>")
def preview_file(filepath):
    """支持图片和视频预览"""
    return send_from_directory(MANAGER_FOLDER, filepath)


@app.route("/edit/<path:filepath>", methods=["GET", "POST"])
def edit_file(filepath):
    filepath = os.path.join("/", filepath)

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
    return jsonify(files)


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


@app.route("/load_wfb_key_config", methods=["GET"])
def load_wfb_key_config():
    wfb_key_config = config_info["wfb_key_pair"]
    return jsonify(wfb_key_config)


@app.route("/save_wfb_key_config/<keypair>", methods=["POST"])
def save_wfb_key_config(keypair):
    global config_info
    new_keypair_content = request.get_json()
    config_info['wfb_key_pair'][keypair] = new_keypair_content
    # 保存修改后的配置到文件
    # 会改变顺序和注释，需优化
    with open(config_info_file, 'w') as file:
        yaml.dump(config_info, file)
    return jsonify({"status": "success"})


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


@app.route("/systeminfo")
def gs_systeminfo():
    cat_gs_release = "cat /etc/gs-release"
    command_result = subprocess.run(
        cat_gs_release, shell=True, capture_output=True, text=True
    )
    return jsonify(command_result.stdout)


if __name__ == "__main__":
    config_info_file = "/gs/webui/configs/config_files.yaml"
    config_info = load_yaml_config(config_info_file)
    ssh = SSHClient(config_info["drone_config"])
    Videos_dir = load_config(config_info, "gs", "gs")["rec_dir"]
    MANAGER_FOLDER = "/config"
    # os.makedirs(MANAGER_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
