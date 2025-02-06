from flask import Flask, render_template, request, redirect, url_for, jsonify
from configobj import ConfigObj
import yaml
import os
import subprocess
import paramiko
from scp import SCPClient


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
                f"Authentication failed when connecting to {self.hostname}. Please check your username/password or key file."
            )
            raise
        except paramiko.SSHException as e:
            print(f"SSH connection failed to {self.hostname}. SSH error: {str(e)}")
            raise
        except Exception as e:
            print(f"Failed to connect to {self.hostname}. Error: {str(e)}")
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


app = Flask(__name__)
app.json.sort_keys = False  # 禁用 jsonify 自动排序


@app.route("/")
def home():
    return render_template("index.html")


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


if __name__ == "__main__":
    config_info_file = "/gs/webui/configs/config_files.yaml"
    config_info = load_yaml_config(config_info_file)
    ssh = SSHClient(config_info["drone_config"])
    app.run(host="0.0.0.0", port=5000, debug=True)
