# app.py
import os
import mimetypes
from flask import Flask, render_template, request, send_file, redirect, url_for, abort
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_ROOT'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB限制

def get_file_type(filename):
    type_, _ = mimetypes.guess_type(filename)
    return (type_ or '').split('/')[0]

def is_safe_path(base, path):
    return os.path.abspath(path).startswith(os.path.abspath(base))

@app.route('/')
@app.route('/browse/<path:subpath>')
def index(subpath=''):
    current_path = os.path.join(app.config['UPLOAD_ROOT'], subpath)
    
    if not is_safe_path(app.config['UPLOAD_ROOT'], current_path):
        abort(403)
    
    if not os.path.exists(current_path):
        os.makedirs(current_path, exist_ok=True)
    
    items = []
    parent_dir = os.path.dirname(subpath)
    if subpath:
        items.append({
            'name': '..',
            'is_dir': True,
            'path': parent_dir if parent_dir != subpath else ''
        })
    
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        rel_path = os.path.join(subpath, name)
        is_dir = os.path.isdir(full_path)
        items.append({
            'name': name,
            'size': os.path.getsize(full_path) if not is_dir else 0,
            'is_dir': is_dir,
            'path': rel_path if is_dir else '',
            'file_type': get_file_type(name) if not is_dir else 'dir'
        })
    
    return render_template('index.html', 
                         items=items,
                         current_path=subpath)

@app.route('/upload/<path:subpath>', methods=['POST'])
def upload_file(subpath=''):
    current_path = os.path.join(app.config['UPLOAD_ROOT'], subpath)
    
    if not is_safe_path(app.config['UPLOAD_ROOT'], current_path):
        abort(403)
    
    if 'file' not in request.files:
        return redirect(url_for('index', subpath=subpath))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index', subpath=subpath))
    
    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(current_path, filename))
    
    return redirect(url_for('index', subpath=subpath))

@app.route('/download/<path:filename>')
def download_file(filename):
    full_path = os.path.join(app.config['UPLOAD_ROOT'], filename)
    
    if not is_safe_path(app.config['UPLOAD_ROOT'], full_path):
        abort(403)
    
    if os.path.isdir(full_path):
        abort(400, "Cannot download directories")
    
    return send_file(full_path, as_attachment=True)

@app.route('/delete/<path:filename>')
def delete_file(filename):
    full_path = os.path.join(app.config['UPLOAD_ROOT'], filename)
    
    if not is_safe_path(app.config['UPLOAD_ROOT'], full_path):
        abort(403)
    
    if os.path.isdir(full_path):
        os.rmdir(full_path)
    else:
        os.remove(full_path)
    
    parent_dir = os.path.dirname(filename)
    return redirect(url_for('index', subpath=parent_dir))

@app.route('/new_folder/<path:subpath>', methods=['POST'])
def new_folder(subpath=''):
    current_path = os.path.join(app.config['UPLOAD_ROOT'], subpath)
    folder_name = secure_filename(request.form.get('folder_name', ''))
    
    if not folder_name:
        return redirect(url_for('index', subpath=subpath))
    
    new_folder_path = os.path.join(current_path, folder_name)
    os.makedirs(new_folder_path, exist_ok=True)
    
    return redirect(url_for('index', subpath=subpath))

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_ROOT'], exist_ok=True)
    app.run(debug=True)
