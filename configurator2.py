from flask import Flask, render_template, request, redirect, url_for, jsonify
import configparser
from configobj import ConfigObj
import yaml
import os
from configupdater import ConfigUpdater
import subprocess


# 定义一个自定义 representer，用于将布尔值转换为小写字符串
def bool_representer(dumper, data):
    # 根据 data 的真假返回 'true' 或 'false'
    value = "true" if data else "false"
    return dumper.represent_scalar("tag:yaml.org,2002:bool", value)


# 将自定义 representer 注册到 PyYAML 中，针对 bool 类型
yaml.add_representer(bool, bool_representer)


# load_yaml_config
def load_yaml_config(file_path) -> dict:
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


config_info_file = "/gs/webui/configs/config_files.yaml"
config_info = load_yaml_config(config_info_file)

config_info_gs = config_info["gs_config_files"]
config_info_drone = config_info["drone_config_files"]
# print(config_info)
"""{
"gs_config_files": {
    "gs": {"path": "/etc/gs.conf", "format": "sh"},
    "wfb": {"path": "/etc/wifibroadcast.cfg", "format": "ini"},
    "wfb_default": {"path": "/etc/default/wifibroadcast", "format": "sh"},
},
"drone_config_files": {
    "majestic": {"path": "/etc/majestic.yaml", "format": "yaml"},
    "wfb": {"path": "/etc/wfb.yaml", "format": "yaml"},
    "wfb_legency": {"path": "/etc/wfb.conf", "format": "sh"},
    "datalink_legency": {"path": "/etc/datalink.conf", "format": "sh"},
    "telemetry_legency": {"path": "/etc/telemetry.conf", "format": "sh"},
},
}"""

config_gs = None
config_drone = None  # 必须每次保存配置前读取配置，不然config_drone保存的可能是别的配置文件的内容或旧的内容

app = Flask(__name__)
app.json.sort_keys = False # 禁用 jsonify 自动排序


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/load_gs_config", methods=["GET"])
def load_gs_config():
    global config_gs
    config_file = config_info["gs_config_files"]["gs"]["path"]
    config_gs = ConfigObj(config_file)
    return jsonify(config_gs)


@app.route("/save_gs_config", methods=["POST"])
def save_gs_config():
    try:
        global config_gs
        # 设置新的保存路径
        config_file = config_info["gs_config_files"]["gs"]["path"] + ".new"
        config_gs.filename = config_file
        config_gs.write()
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/load_drone_config/<filename>", methods=["GET"])
def load_drone_config(filename):
    global config_drone
    # 从文件载入配置
    config_file = config_info["drone_config_files"][filename]["path"]
    config_drone = load_yaml_config(config_file)
    print(f"【Load】{config_drone}")
    # ssh 远程命令执行获取wfb.yml文件内容
    config_drone_str = ""
    # config_drone = yaml.safe_load(config_drone_str)
    return jsonify(config_drone)


@app.route("/save_drone_config/<filename>", methods=["POST"])
def save_drone_config(filename):
    global config_drone
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
        # diff = {k: (config_drone_old[k], config_drone_new[k]) for k in config_drone_old if k in config_drone_new and config_drone_old[k] != config_drone_new[k]}
        update_content = {k: config_drone_new[k] for k in config_drone_old if k in config_drone_new and config_drone_old[k] != config_drone_new[k]}
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
