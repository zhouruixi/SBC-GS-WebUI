from flask import Flask, render_template, request, redirect, url_for, jsonify
import configparser
import yaml
import os

def parse_ini_to_dict(file_path):
    config = configparser.ConfigParser(allow_no_value=True)
    config.optionxform = str
    with open(file_path) as f:
        f_default = '[DEFAULT]\n' + f.read()
        config.read_string(f_default)
    return config.defaults()
    '''
    settings_dict = {}
    for key in config.defaults():
        settings_dict[key] = config.get('DEFAULT', key)
    return settings_dict
    '''

def parse_yaml_to_dict(file_path):
    with open(file_path, 'r') as file:
        yaml_dict = yaml.safe_load(file)
    return yaml_dict

def parse_config(file_path, file_type):
    if file_type == 'ini':
        return parse_ini_to_dict(file_path)
    elif file_type == 'yaml':
        return parse_yaml_to_dict(file_path)
    else:
        raise ValueError("Unsupported file type. Use 'ini' or 'yaml'.")

def load_config_file_info(config_info_path):
    with open(config_info_path, 'r', encoding='utf-8') as file:
        config_info = yaml.safe_load(file)
    return config_info


def load_all_configs(side):
    config_info_path = '/gs/webui/configs/config_files.yaml'
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
# all_configs_local = load_all_configs('gs')

# ToDo

# 定义 YAML 文件路径
YAML_FILE_PATH = "./configs/drone_config.yaml"


# 加载 YAML 文件内容
def load_yaml():
    if not os.path.exists(YAML_FILE_PATH):
        return {}
    with open(YAML_FILE_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


# 保存到 YAML 文件
def save_yaml(data):
    with open(YAML_FILE_PATH, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, allow_unicode=True, default_flow_style=False)



app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/load_gs_config', methods=['GET'])
def load_gs_config():
    data = load_all_configs('gs')
    # data = load_yaml()
    # print(type(data))
    # print(data)
    return jsonify(data['gs'])


@app.route('/save_gs_config', methods=['POST'])
def save_gs_config():
    try:
        data = request.json  # 获取前端传来的 JSON 数据
        save_yaml(data) # ~~~~~~~~~~~~~~~~~~~~
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/load_drone_config', methods=['GET'])
def load_drone_config():
    data = load_all_configs('drone')
    # data = load_yaml()
    # print(data)
    return jsonify(data['wfb'])


@app.route('/save_drone_config', methods=['POST'])
def save_drone_config():
    try:
        data = request.json  # 获取前端传来的 JSON 数据
        save_yaml(data) # ~~~~~~~~~~~~~~~~~~~~
        return jsonify({"success": True, "message": "配置已保存！"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

