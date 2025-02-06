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


config_info_file = "/gs/webui/configs/config_files.yaml"
config_info = load_yaml_config(config_info_file)
# print(config_info)
"""{
"gs_config_files": {
    "gs": {"path": "/etc/gs.conf", "format": "ini"},
    "wfb": {"path": "/etc/wifibroadcast.cfg", "format": "ini"},
    "wfb_default": {"path": "/etc/default/wifibroadcast", "format": "ini"},
},
"drone_config_files": {
    "majestic": {"path": "/etc/majestic.yaml", "format": "yaml"},
    "wfb": {"path": "/etc/wfb.yaml", "format": "yaml"},
    "wfb_legency": {"path": "/etc/wfb.conf", "format": "ini"},
    "datalink_legency": {"path": "/etc/datalink.conf", "format": "ini"},
    "telemetry_legency": {"path": "/etc/telemetry.conf", "format": "ini"},
},
}"""


"""
drone_ssh_host = config_info["drone_config"]["host"]
drone_ssh_port = config_info["drone_config"]["port"]
drone_ssh_username = config_info["drone_config"]["username"]
drone_ssh_password = config_info["drone_config"]["password"]
drone_ssh_timeout = 5

# 目标文件路径
remote_file = "/etc/majestic.yaml"
# 本地保存路径
local_file = "majestic.yaml"

# 创建 SSH 客户端
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    # 连接到目标主机
    client.connect(drone_ssh_host, drone_ssh_port, drone_ssh_username, drone_ssh_password, timeout=drone_ssh_timeout)
    # private_key_path = '/path/to/private/key'
    # client.connect(hostname, port, username, key_filename=private_key_path)

    # 使用 SCP 获取文件
    with SCPClient(client.get_transport()) as scp:
        scp.get(remote_file, local_file)
    print(f"文件已成功从 {drone_ssh_host} 下载到 {local_file}")

    # 远程执行命令
    command = "ls -l /"
    stdin, stdout, stderr = client.exec_command(command, timeout=drone_ssh_timeout)
    # 获取命令的输出
    output = stdout.read().decode()  # 将输出从字节流转换为字符串
    error = stderr.read().decode()  # 获取错误输出

    if output:
        print("命令输出：")
        print(output)
    if error:
        print("错误输出：")
        print(error)

    # 交互
    # stdin, stdout, stderr = client.exec_command('some_command')
    # stdin.write('input_data\n')  # 输入数据
    # stdin.flush()  # 刷新输入流
except paramiko.ssh_exception.NoValidConnectionsError:
    print("无法连接到目标主机")
except paramiko.AuthenticationException:
    print("认证失败")
except paramiko.SSHException as e:
    print(f"SSH 错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")
finally:
    client.close()
"""

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
        print(f"【Updated】{update_content}")
        if not update_content:
            print("配置没有变化")
        else:
            update_command = "sed -i"
            # crudini --set gs.conf.bak DEFAULT "br0_fixed_ip" "'0.0.0.0/0'"
            for k, v in update_content.items():
                update_command += f''' -e "s/^{k}=.*/{k}='{v}'/g"'''
            update_command += f" {config_info['gs_config_files'][filename]['path']} && echo success"
            print(update_command)
            # exec command
            update_command_result = subprocess.run(update_command, shell=True, capture_output=True, text=True)
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

    config_drone = load_config(config_info, "drone", filename)

    # ssh 远程命令执行获取wfb.yml文件内容
    config_drone_str = ""
    # config_drone = yaml.safe_load(config_drone_str)
    return jsonify(config_drone)


@app.route("/save_drone_config/<filename>", methods=["POST"])
def save_drone_config(filename):
    # global config_drone
    config_drone = load_config(config_info, "drone", filename)

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
    print(f"【Old】{config_drone_old}")
    try:
        config_drone_new = request.json  # 获取前端传来的 JSON 数据
        print(f"【New】{config_drone_new}")
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
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
