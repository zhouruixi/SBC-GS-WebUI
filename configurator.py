from flask import Flask, render_template, request, redirect, url_for, jsonify
import configparser
from configobj import ConfigObj
import yaml
import os
from configupdater import ConfigUpdater
import subprocess

config_info_path = '/gs/webui/configs/config_files.yaml'
config_info = {}
config_gs = ""

# load_shell_config
def parse_shellconf_to_dict(file_path):
    # 临时添加一个默认节
    with open(file_path, 'r') as file:
        content = file.read().replace("'", "'")
        if not content.startswith("["):
            content = "[DEFAULT]\n" + content
    # 使用 ConfigUpdater 解析文件内容
    updater = ConfigUpdater()
    updater.read_string(content)
    # 转换为字典
    '''
    config_dict = {}
    for section in updater.sections():
        config_dict[section] = {}
        for key, option in updater.items(section):
            config_dict[section][key] = option.value  # 获取 Option 对象的 value
    '''
    config_dict = {}
    for key, option in updater.items('DEFAULT'):
        config_dict[key] = option.value  # 获取 Option 对象的 value
    return config_dict

# save_shell_config
def save_shell_config(file_path):
    # 临时添加一个默认节
    with open(file_path, 'r') as file:
        content = file.read().replace("'", "")
        if not content.startswith("["):
            content = "[DEFAULT]\n" + content
    # 使用 ConfigUpdater 解析文件内容
    updater = ConfigUpdater()
    updater.read_string(content)
    with open('/home/cc/SBC-WEBUI/web3/configs/gs.ini', 'w') as f2:
        updater.write(f2)

''' def save_shellconf_to_file(file_path, sed_command):
    """使用sed更新配置文件"""
    # sed_command = f"sed -i '' -e 's|^{key}=.*|{key}=\\'{new_value}\\'|' {file_path}"
    sed_command += f" {file_path}"
    try:
        # 使用 subprocess 调用 sed 命令
        subprocess.run(sed_command, shell=True, check=True)
        print(f"Updated {file_path} success")
    except subprocess.CalledProcessError as e:
        print(f"Failed to update {file_path}: {e}") '''
'''
# load_shell_config
def load_shell_config(file_path):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    with open(file_path) as f:
        f_default = '[DEFAULT]\n' + f.read()
        config.read_string(f_default)
    return config.defaults()
'''

# load_shell_config
def load_shell_config(file_path):
    # 读取没有节的 INI 文件
    config_gs = ConfigObj(file_path)

# load_ini_config
def parse_ini_to_dict(file_path):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    config.read(file_path)
    return config
    '''
    settings_dict = {}
    for key in config.defaults():
        settings_dict[key] = config.get('DEFAULT', key)
    return settings_dict
    '''
# load_yaml_config
def parse_yaml_to_dict(file_path):
    with open(file_path, 'r') as file:
        yaml_dict = yaml.safe_load(file)
    return yaml_dict

def parse_config(file_path, file_type):
    if file_type == 'ini':
        return parse_ini_to_dict(file_path)
    elif file_type == 'yaml':
        return parse_yaml_to_dict(file_path)
    elif file_type == 'shell':
        return load_shell_config(file_path)
    else:
        raise ValueError("Unsupported file type. Use 'ini' 'yaml' or 'shell'.")

def load_config_file_info(config_info_path):
    global config_info
    with open(config_info_path, 'r', encoding='utf-8') as file:
        config_info = yaml.safe_load(file)
    print(config_info)
    return config_info

def load_all_configs(side):
    global config_info_path
    config_files = load_config_file_info(config_info_path)
    all_configs = {}
    for config_file in config_files[f"{side}_config_files"]:
        name = config_file['name']
        path = config_file['path']
        file_type = config_file['format']

        if os.path.exists(path):
            config_data = parse_config(path, file_type)
            all_configs[name] = config_data
        else:
            print(f"Warning: {path} does not exist.")

    return all_configs

# all_configs_drone = load_all_configs('drone')
# all_configs_gs = load_all_configs('gs')

# ToDo

# 定义 YAML 文件路径
YAML_FILE_PATH = "./configs/drone_config.yaml"


# 保存 YAML 文件
def save_yaml(data):
    with open(YAML_FILE_PATH, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, default_flow_style=False)

gs_conf_content = {}
drone_conf_content = {}

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/load_gs_config', methods=['GET'])
def load_gs_config():
    # data = load_all_configs('gs')
    # return jsonify(data['gs'])
    ## gs_conf_content = parse_shellconf_to_dict('/etc/gs.conf')
    # data = load_yaml()
    # print(type(data))
    # print(data)
    global gs_conf_content
    gs_conf_content = load_all_configs('gs')
    # print(gs_conf_content)
    return jsonify(gs_conf_content['gs'])


@app.route('/save_gs_config', methods=['POST'])
def save_gs_config():
    try:
        global config_info
        save_shell_config('/etc/gs.conf')
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
    '''
    try:
        data = request.json  # 获取前端传来的 JSON 数据
        # print(data)
        # save_yaml(data)
        sed_command = 'sed -i'
        for k,v in data.items():
            if gs_conf_content['gs'][k] != v:
                sed_command += f" -e 's/^{k}=.*/{k}=\\'{v}\\''"
                # print(f"{k}------{v}")
        print(sed_command)
        # save_shellconf_to_file(config_info['gs']['gs']['path'], sed_command)
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})
'''

@app.route('/load_drone_config', methods=['GET'])
def load_drone_config():
    global drone_conf_content
    drone_conf_content = load_all_configs('drone')
    # data = load_yaml()
    # print(drone_conf_content)
    return jsonify(drone_conf_content['wfb'])


@app.route('/save_drone_config', methods=['POST'])
def save_drone_config():
    try:
        data = request.json  # 获取前端传来的 JSON 数据
        # print(type(data))
        # print(data)
        save_yaml(data) # ~~~~~~~~~~~~~~~~~~~~
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

