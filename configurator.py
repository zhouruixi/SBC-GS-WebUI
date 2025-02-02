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


class SSHClient:
    def __init__(self, host_conf):
        self.host = host_conf["host"]
        self.username = host_conf["username"]
        self.password = host_conf["password"]
        self.port = host_conf["port"]
        self.client = None

    def connect(self):
        self.client = paramiko.SSHClient()
        # 自动接受未验证的主机密钥
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.client.connect(
                self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                timeout=5,
            )
        except paramiko.ssh_exception.NoValidConnectionsError:
            print("无法连接到目标主机")
            raise
        except paramiko.AuthenticationException:
            print(
                f"Authentication failed when connecting to {self.host}. Please check your username/password or key file."
            )
            raise
        except paramiko.SSHException as e:
            print(f"SSH connection failed to {self.host}. SSH error: {str(e)}")
            raise
        except Exception as e:
            print(f"Failed to connect to {self.host}. Error: {str(e)}")
            raise

    def execute_command(self, command):
        if not self.client:
            raise ValueError(
                "SSH connection not established. Please call connect() first."
            )
        stdin, stdout, stderr = self.client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        if error:
            raise Exception(f"Error executing command: {error}")
        return output

    def download_file(self, remote_path, local_path):
        """下载文件"""
        if not self.client:
            raise ValueError(
                "SSH connection not established. Please call connect() first."
            )
        with SCPClient(self.client.get_transport()) as scp:
            try:
                scp.get(remote_path, local_path)
                print(f"File downloaded from {remote_path} to {local_path}.")
            except Exception as e:
                print(f"Failed to download file from {remote_path}. Error: {str(e)}")
                raise

    def close(self):
        """关闭SSH连接"""
        if self.client:
            self.client.close()
            print("SSH connection closed.")


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
    except EOFError as e:
        # 捕捉EOFError并记录错误
        print(f"EOFError: 网络连接中断或远程服务器关闭连接: {str(e)}")
        # 可以选择重试逻辑或者其他恢复策略
    except Exception as e:
        # 捕捉其他所有异常并记录
        print(f"发生了其他错误: {str(e)}")
    finally:
        ssh.close()

    # config_drone = load_config(config_info, "drone", config_file)
    # config_drone = yaml.safe_load(config_drone_str)
    config_drone = load_yaml_config(config_file_local)
    return jsonify(config_drone)


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
            ssh.close()
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/exec_button_function", methods=["POST"])
def exec_button_function():
    # 获取前端发送的数据
    data = request.get_json()
    function_name = data.get("button_id")

    # 打印接收到的按钮ID
    print(f"收到按钮指令: {function_name}")
    button_command = f"/gs/button.sh {function_name}"
    print(f"执行命令：{button_command}")
    button_command_result = subprocess.run(
        button_command, shell=True, capture_output=True, text=True
    )
    if button_command_result.returncode != 0:
        raise ValueError("执行按钮命令出错")  # 主动抛出异常
    # 返回按钮 ID
    return jsonify({"status": "success", "button_id": function_name})


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
    """修复 302 错误，确保下载正常"""
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


if __name__ == "__main__":
    config_info_file = "/gs/webui/configs/config_files.yaml"
    config_info = load_yaml_config(config_info_file)
    ssh = SSHClient(config_info["drone_config"])
    Videos_dir = load_config(config_info, "gs", "gs")["rec_dir"]
    MANAGER_FOLDER = "/"
    # os.makedirs(MANAGER_FOLDER, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
