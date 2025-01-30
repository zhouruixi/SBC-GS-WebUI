from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    url_for,
)
import os
import shutil
import mimetypes
import time
from pathlib import Path

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def format_size(size):
    """将字节大小转换为 KB、MB、GB"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


@app.route("/filemanager/")
@app.route("/filemanager/<path:subpath>")
def index(subpath=""):
    base_path = os.path.join(UPLOAD_FOLDER, subpath)
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
        save_path = os.path.join(UPLOAD_FOLDER, subpath, file.filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
    return redirect(url_for("index", subpath=subpath))


@app.route("/create_folder", methods=["POST"])
def create_folder():
    folder_name = request.form["folder_name"]
    subpath = request.form.get("current_path", "")
    new_folder = os.path.join(UPLOAD_FOLDER, subpath, folder_name)
    os.makedirs(new_folder, exist_ok=True)
    return redirect(url_for("index", subpath=subpath))


@app.route("/delete/<path:filepath>")
def delete_file(filepath):
    full_path = os.path.join(UPLOAD_FOLDER, filepath)
    parent_dir = os.path.dirname(filepath)
    if os.path.isdir(full_path):
        shutil.rmtree(full_path)
    else:
        os.remove(full_path)
    return redirect(url_for("index", subpath=parent_dir))


@app.route("/download/<path:filepath>")
def download_file(filepath):
    """修复 302 错误，确保下载正常"""
    return send_from_directory(UPLOAD_FOLDER, filepath, as_attachment=True)


@app.route("/preview/<path:filepath>")
def preview_file(filepath):
    """支持图片和视频预览"""
    return send_from_directory(UPLOAD_FOLDER, filepath)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
