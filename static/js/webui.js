// scripts.js
$(document).ready(function () {
    // 使用 Fetch API 发送 POST 请求到服务器备份文件
    // 在html中调用js文件中的函数需要这样写
    backupFile = function (filename) {
        fetch(`/backup/${filename}`, {
            method: 'POST',
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);  // 弹出备份成功的提示
            })
            .catch(error => {
                console.error('Error backing up file:', error);
                alert('Error backing up file');
            });
    }

    // 点击文件编辑后加载文件内容到模态框
    editFile = function (filename) {
        $.get(`/edit/${filename}`, function (data) {
            $('#editModalLabel').text(i18next.t('configEditor.editNow', { filename: filename}));  // 模态框标题
            // $('#editModalLabel').text(`正在编辑: ${filename}`);  // 模态框标题
            $('#fileContent').val(data.content);  // 填充文件内容
            $('#editModal').modal('show');  // 显示模态框

            // 保存按钮事件
            $('#saveFileBtn').off('click').on('click', function () {
                saveFile(filename);
            });
        }).fail(function () {
            alert("无法加载文件内容！");
        });
    }

    // 保存文件
    function saveFile(filename) {
        const content = $('#fileContent').val();
        $.ajax({
            url: `/edit/${filename}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ content: content }),
            success: function () {
                alert(i18next.t('configEditor.saveSuccess'));
                $('#editModal').modal('hide');
            },
            error: function () {
                alert(i18next.t(configEditor.saveFail));
            }
        });
    }

    // 发送按钮 ID 到后端
    function sendButtonFunctionToBackend(buttonId, targetValue = null) {
        fetch('/exec_button_function', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ "button_id": buttonId, "target_value": targetValue })
        })
            .then(response => response.json())
            .then(data => {
                // console.log('服务器响应:', data);
                alert(i18next.t('webButton.buttonSuccess', {buttonId: buttonId}));
            })
            .catch(error => {
                console.error(i18next.t('webButton.buttonFail', {buttonId: buttonId}), error);
            });
    }

    // 监听所有 gs_btn_ 或 drone_btn_ 开头的控制指令按钮
    function listenToButtons() {
        const buttons = document.querySelectorAll('[id^="gs_btn_"], [id^="drone_btn_"]');
        buttons.forEach(button => {
            button.addEventListener('click', function () {
                // 获取按钮的 id 并调用发送请求的函数
                const buttonId = button.id;
                sendButtonFunctionToBackend(buttonId);
            });
        });
    }

    // 监听所有 drone_setting_ 开头的快捷设置按钮
    function listenToDroneSettingButtons() {
        const buttons = document.querySelectorAll('[id^="drone_setting_"]');
        buttons.forEach(button => {
            button.addEventListener('click', function () {
                // 获取按钮的 id 并调用发送请求的函数
                const buttonId = button.id;
                const targetValue = $(`#content_${buttonId}`).val();
                // console.log(`Hello, ${targetValue}!`);
                if (targetValue.trim() !== '') {
                    // 如果input框不为空，发送按钮指令
                    sendButtonFunctionToBackend(buttonId, targetValue);
                }
            });
        });
    }

    // 加载 GS 配置
    function loadGSConfig() {
        // if ($("#gsconfig").hasClass("active")) {
        $.get("/load_gs_config/gs", function (data) {
            const container = $("#gs-config-container");
            container.empty(); // 清空容器

            // 动态生成配置表单
            for (const [key, value] of Object.entries(data)) {
                const row = `
                        <div class="mb-3 px-3 row">
                            <label class="col-form-label col-auto text-start">${key}</label>
                            <div class="col flex-grow-1">
                                <input type="text" class="form-control config-input-gs" data-key="${key}" value="${value}" placeholder="${value}">
                            </div>
                        </div>`;
                container.append(row);
            }
            const resultDiv = $("#save-result-gs");
            resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-gs-success-alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                ${i18next.t('common.loadSuccess')}
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $('#load-result-gs-success-alert').alert('close');
            }, 2000);
        }).fail(function () {
            alert(i18next.t('common.loadFail'));
        });
        // }
    }

    // 保存 GS 配置
    function saveGSConfig() {
        const data = {};
        $(".config-input-gs").each(function () {
            const key = $(this).data("key");
            const value = $(this).val();
            data[key] = value;
        });

        $.ajax({
            url: "/save_gs_config/gs",
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function (response) {
                const resultDiv = $("#save-result-gs");
                if (response.success) {
                    resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="save-result-gs-success-alert">
                                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                        ${response.message}
                                        </div>`);
                    // 设置 2 秒后自动消失
                    setTimeout(function () {
                        $('#save-result-gs-success-alert').alert('close');
                    }, 2000);
                } else {
                    resultDiv.html(`<div class="alert alert-danger">${response.message}</div>`);
                }
            },
            error: function () {
                alert(i18next.t('common.saveFail'));
            },
        });
    }

    // 加载 Drone 配置
    function loadDroneConfig(config_name) {
        const resultDiv = $(`#save-result-drone-${config_name}`);
        $.get(`/load_drone_config/${config_name}`, function (data) {
            const container = $(`#drone-config-container-${config_name}`);
            container.empty(); // 清空容器

            // 动态生成配置表单
            for (const [file, content] of Object.entries(data)) {
                const titel_part = `<h4 class="mt-4 p-1 bg-secondary text-white rounded-2">${file}</h4>`
                // <hr class="border-primary">`
                container.append(titel_part);
                for (const [key, value] of Object.entries(content)) {
                    const row = `
                            <div class="mb-3 px-3 row">
                                <label class="col-form-label col-sm-1 text-start">${key}</label>
                                <div class="col">
                                    <input type="text" class="form-control config-input-drone-${config_name}" data-key="${file}.${key}" value="${value}" placeholder="${value}">
                                </div>
                            </div>`;
                    container.append(row);
                }
            }
            resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-drone-${config_name}-success-alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                <div data-i18n="common.loadSuccess">${i18next.t('common.loadSuccess')}</div>
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $(`#load-result-drone-${config_name}-success-alert`).alert('close');
            }, 2000);
        }).fail(function () {
            resultDiv.html(`<div class="alert alert-danger alert-dismissible fade show" role="alert" id="load-result-drone-${config_name}-success-alert">
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                <div data-i18n="common.loadFail">${i18next.t('common.loadFail')}</div>
                </div>`);
            // alert(`加载 Drone ${config_name} 配置失败，请手动重新加载！`);
        });
    }

    // 保存 Drone 配置
    function saveDroneConfig(config_name) {
        const data = {};
        $(`.config-input-drone-${config_name}`).each(function () {
            const key = $(this).data("key");
            const value = $(this).val();
            data[key] = value;
        });

        $.ajax({
            url: `/save_drone_config/${config_name}`,
            method: "POST",
            contentType: "application/json",
            data: JSON.stringify(data),
            success: function (response) {
                const resultDiv = $(`#save-result-drone-${config_name}`);
                if (response.success) {
                    resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="save-result-drone-${config_name}-success-alert">
                                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                            ${response.message}
                                            </div>`);
                    // 设置 2 秒后自动消失
                    setTimeout(function () {
                        $(`#save-result-drone-${config_name}-success-alert`).alert('close');
                    }, 2000);
                } else {
                    resultDiv.html(`<div class="alert alert-danger alert-dismissible fade show">
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                        ${response.message}</div>`);
                }
            },
            error: function () {
                alert(i18next.t('common.saveFail'));
            },
        });
    }

    // 加载 DVR 文件列表
    function loadVideoFiles() {
        fetch('/list_video_files')
            .then(response => response.json())
            .then(files => {
                const fileList = document.getElementById("fileList");
                fileList.innerHTML = "";

                files.forEach(file => {
                    const row = document.createElement("tr");

                    const nameCell = document.createElement("td");
                    nameCell.textContent = file.name;
                    row.appendChild(nameCell);

                    const sizeCell = document.createElement("td");
                    sizeCell.textContent = file.size;
                    row.appendChild(sizeCell);

                    const actionsCell = document.createElement("td");

                    const downloadBtn = document.createElement("a");
                    downloadBtn.href = `/download_video/${encodeURIComponent(file.name)}`;
                    downloadBtn.className = "btn btn-success btn-sm";
                    downloadBtn.dataset.i18n = "common.download";
                    downloadBtn.textContent = i18next.t('common.download');
                    actionsCell.appendChild(downloadBtn);

                    const deleteBtn = document.createElement("button");
                    deleteBtn.className = "btn btn-danger btn-sm ms-1";
                    deleteBtn.dataset.i18n = "common.delete";
                    deleteBtn.textContent = i18next.t('common.delete');
                    deleteBtn.onclick = function () { deleteVideoFile(file.name); };
                    actionsCell.appendChild(deleteBtn);

                    if (file.name.endsWith('.jpg') || file.name.endsWith('.jpeg') || file.name.endsWith('.png') || file.name.endsWith('.gif') || file.name.endsWith('.mp4') || file.name.endsWith('.avi')) {
                        const previewBtn = document.createElement("button");
                        previewBtn.className = "btn btn-info btn-sm ms-1";
                        previewBtn.dataset.i18n = "common.preview";
                        previewBtn.textContent = i18next.t('common.preview');
                        previewBtn.onclick = function () { previewVideoFile(file.name); };
                        actionsCell.appendChild(previewBtn);
                    }

                    row.appendChild(actionsCell);
                    fileList.appendChild(row);
                });
            });
    }

    // 加载当前 wfb key 配置
    function loadCurrentWfbKey() {
        fetch('/load_wfb_key_config/current')
            .then(response => {
                if (!response.ok) {
                    throw new Error('网络请求失败');
                }
                return response.json();  // 将响应解析为 JSON
            })
            .then(data => {
                document.getElementById('current-wfb-gs-key').innerHTML = `<b>Current GS key: </b>${data.gs}`;
                const droneKeyDiv = document.getElementById('current-wfb-drone-key');
                // 检查 data.drone 是否为空
                if (data.drone) {
                    droneKeyDiv.innerHTML = `<b>Current Drone key: </b>${data.drone}`;
                } else {
                    droneKeyDiv.innerHTML = `<b>Current Drone key: </b>${i18next.t('keyManager.clickToReload')}`;
                    // droneKeyDiv.style.color = 'red';  // 设置提示文字为红色
                }
            });
    }

    // 加载 wfb key 配置
    function loadWfbKeyConfig() {
        $.get(`/load_wfb_key_config`, function (data) {
            const container = $(`#wfb-key-config-container`);
            container.empty(); // 清空容器

            // 动态生成配置表单
            for (const [keypair, content] of Object.entries(data)) {
                const titel_part = `<h4 class="mt-4 p-1 bg-secondary text-white rounded-2">${keypair}</h4>`
                container.append(titel_part);
                for (const [side, value] of Object.entries(content)) {
                    const row = `
                        <div class="mb-1 px-3 row">
                            <label class="col-form-label col-sm-1 text-start">${side}</label>
                            <div class="col d-flex align-items-center">
                                <input type="text" class="form-control config-input-wfb-key" data-key="wfb-${keypair}.${side}" value="${value}" placeholder="${value}">
                                <div class="col-auto">
                                    <button type="button" class="btn btn-danger ms-2" id="apply-key-${keypair}-${side}" data-i18n="keyManager.applyKey">${i18next.t('keyManager.applyKey')}</button>
                                </div>
                            </div>
                        </div>`;
                    container.append(row);

                    // 为应用 key 按钮绑定点击事件
                    $(`#apply-key-${keypair}-${side}`).on('click', function () {
                        // 调用 saveWfbKeyConfig 函数并传递 keypair
                        applyWfbKey(keypair, side);
                    });
                }

                const button_key_pair = `
                    <div class="d-flex justify-content-center align-items-center mt-3">
                        <!-- 按钮组 -->
                        <div>
                            <button type="button" class="btn btn-primary" id="upload-gs-key-${keypair}" data-i18n="keyManager.uploadGsKey">${i18next.t('keyManager.uploadGsKey')}</button>
                            <button type="button" class="btn btn-success" id="download-gs-key-${keypair}" data-i18n="keyManager.downloadGsKey">${i18next.t('keyManager.downloadGsKey')}</button>
                            <button type="button" class="btn btn-primary" id="upload-drone-key-${keypair}" data-i18n="keyManager.uploadDroneKey">${i18next.t('keyManager.uploadDroneKey')}</button>
                            <button type="button" class="btn btn-success" id="download-drone-key-${keypair}" data-i18n="keyManager.downloadDroneKey">${i18next.t('keyManager.downloadDroneKey')}</button>
                            <button type="button" class="btn btn-secondary" id="random-key-${keypair}" data-i18n="keyManager.randomKey">${i18next.t('keyManager.randomKey')}</button>
                            <input type="password" id="wfb-key-password-${keypair}" placeholder="${i18next.t("keyManager.keyPassword")}" data-i18n-placeholder="keyManager.keyPassword">
                            <button type="button" class="btn btn-secondary" id="random-key-password-${keypair}" data-i18n="keyManager.derivationKeypair">${i18next.t('keyManager.derivationKeypair')}</button>
                            <button type="button" class="btn btn-warning" id="save-key-${keypair}" data-i18n="keyManager.saveToFile">${i18next.t('keyManager.saveToFile')}</button>
                        </div>
                    </div>`;
                container.append(button_key_pair);

                // 为随机生成 wfb key 按钮绑定点击事件
                $(`#random-key-${keypair}`).on('click', function () {
                    // 调用 getRandomWfbKey 函数并传递 keypair
                    getRandomWfbKey(keypair);
                });
                $(`#random-key-password-${keypair}`).on('click', function () {
                    const wfbKeyPassword = $(`#wfb-key-password-${keypair}`).val();
                    getRandomWfbKey(keypair, wfbKeyPassword);
                });

                // 为保存 key 按钮绑定点击事件
                $(`#save-key-${keypair}`).on('click', function () {
                    // 调用 saveWfbKeyConfig 函数并传递 keypair
                    saveWfbKeyConfig(keypair);
                });

                // 上传 gs key
                $(`#upload-gs-key-${keypair}`).on('click', function () {
                    uploadWfbKey(keypair, 'gs');
                });

                // 下载 gs key
                $(`#download-gs-key-${keypair}`).on('click', function () {
                    downloadWfbKey(keypair, 'gs');
                });

                // 上传 drone key
                $(`#upload-drone-key-${keypair}`).on('click', function () {
                    uploadWfbKey(keypair, 'drone');
                });

                // 下载 drone key
                $(`#download-drone-key-${keypair}`).on('click', function () {
                    downloadWfbKey(keypair, 'drone');
                });
            }

            const resultDiv = $(`#save-result-wfb-key`);
            resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-wfb-key-success-alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                ${i18next.t('common.loadSuccess')}
                            </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $('#load-result-wfb-key-success-alert').alert('close');
            }, 2000);
        }).fail(function () {
            alert(i18next.t('common.loadFail'));
        });
    }

    // 将上传的 wfb key 转为 base64
    function uploadWfbKey(keypair, side) {
        const fileInput = $('<input type="file" />');
        fileInput.on('change', function (e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    const base64 = e.target.result.split(',')[1];
                    $(`input[data-key="wfb-${keypair}.${side}"]`).val(base64);
                    console.log(`Upload ${side}:`, base64);
                };
                reader.readAsDataURL(file);
            }
        });
        fileInput.click();
    }

    // 将 base64 转为二进制 wfb key 并提供下载
    function downloadWfbKey(keypair, side) {
        // 从对应的 input 框获取 base64 数据
        const base64Data = $(`input[data-key="wfb-${keypair}.${side}"]`).val();
        if (!base64Data) return;

        const binaryString = window.atob(base64Data);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        const blob = new Blob([bytes]);

        // 创建下载链接
        const downloadLink = document.createElement('a');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = `${keypair}-${side}.key`; // 根据类型设置文件名

        // 触发下载
        downloadLink.click();

        // 清理 URL 对象
        URL.revokeObjectURL(downloadLink.href);
    }

    // 保存 wfb key 配置
    function saveWfbKeyConfig(keypair) {
        // const content = $('#fileContent').val();
        // var value = $(`input[data-key="wfb-${keypair}.gs"]`).val();
        var keypairContent = {};
        keypairContent['name'] = $(`input[data-key="wfb-${keypair}.name"]`).val();
        keypairContent['gs'] = $(`input[data-key="wfb-${keypair}.gs"]`).val();
        keypairContent['drone'] = $(`input[data-key="wfb-${keypair}.drone"]`).val();

        $.ajax({
            url: `/save_wfb_key_config/${keypair}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(keypairContent),
            success: function () {
                alert(i18next.t('common.saveSuccess'));
            },
            error: function () {
                alert(i18next.t('common.saveFail'));
            }
        });
    }

    // 应用 wfb key 配置
    function applyWfbKey(keypair, side) {
        var keypairContent = {};
        keypairContent['name'] = $(`input[data-key="wfb-${keypair}.name"]`).val();
        keypairContent['gs'] = $(`input[data-key="wfb-${keypair}.gs"]`).val();
        keypairContent['drone'] = $(`input[data-key="wfb-${keypair}.drone"]`).val();

        $.ajax({
            url: `/apply_wfb_key/${side}`,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(keypairContent),
            success: function () {
                alert(`key ${i18next.t('common.applySuccess')}`);
            },
            error: function () {
                alert(`${keypairContent['name']} key ${i18next.t('common.applyFail')}`);
            }
        });
    }

    // 生成随机 wfb key 配置
    function getRandomWfbKey(keypair, password = null) {
        const url = 'get_random_wfb_key';

        if (password) {
            $.ajax({
                url: url,
                type: 'POST',
                contentType: "application/json",
                data: JSON.stringify({ password: password }),
                success: function (data) {
                    showWfbKey(data, keypair);
                },
                error: function () {
                    alert(`${i18next.t('keyManager.randomKey')} ${i18next.t('common.fail')}`);
                }
            });
        } else {
            $.get(url, function (data) {
                showWfbKey(data, keypair);
            }).fail(function () {
                alert(`${i18next.t('keyManager.randomKey')} ${i18next.t('common.fail')}`);
            });
        }
    }

    // 在页面中展示生成的 wfb key
    function showWfbKey(data, keypair) {
        const gsKeyBase64 = data.gs;
        const droneKeyBase64 = data.drone;

        $(`[data-key="wfb-${keypair}.gs"]`).val(gsKeyBase64);
        $(`[data-key="wfb-${keypair}.drone"]`).val(droneKeyBase64);

        const resultDiv = $('#save-result-wfb-key');
        resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-wfb-key-success-alert">
                            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                            ${i18next.t('keyManager.randomKey')} ${i18next.t('common.success')}
                        </div>`);

        setTimeout(function () {
            $('#load-result-wfb-key-success-alert').alert('close');
        }, 2000);
    }

    // 点击预览后显示内容到模态框
    function previewVideoFile(filename) {
        const fileUrl = `/download_video/${encodeURIComponent(filename)}`;
        const modal = new bootstrap.Modal(document.getElementById('previewModal'));
        const img = document.getElementById('previewImage');
        const video = document.getElementById('previewVideo');
        const videoSource = document.getElementById('previewVideoSource');
        $('#previewModalLabel').text(`${i18next.t('dvr.previewNow')}: ${filename}`);

        img.classList.add('d-none');
        video.classList.add('d-none');

        fetch(fileUrl)
            .then(response => {
                if (!response.ok) throw new Error('File not found');
                if (filename.match(/\.(jpg|jpeg|png|gif)$/i)) {
                    img.src = fileUrl;
                    img.classList.remove('d-none');
                } else if (filename.match(/\.(mp4|avi)$/i)) {
                    videoSource.src = fileUrl;
                    video.load();
                    video.classList.remove('d-none');
                    video.play();
                }
                modal.show();
            })
            .catch(() => alert(i18next.t('dvr.previewFail')));
    }

    function deleteVideoFile(filename) {
        if (!confirm(i18next.t('common.confirmDelete', {filename: filename}))) return;

        fetch(`/delete_video/${encodeURIComponent(filename)}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    loadVideoFiles();
                } else {
                    alert(`${i18next.t('common.deleteFail')}${data.message}`);
                }
            });
    }

    function loadSystemInfo(side) {
        // 格式化键名，使其变得更友好（如 "gs_release" 转为 "Release Information"）
        function formatKey(key) {
            const formattedKey = key
                .replace(/_/g, ' ') // 替换下划线为空格
                .replace(/\b\w/g, char => char.toUpperCase()); // 首字母大写
            return formattedKey;
        }

        // 获取显示系统信息的 div
        const systemInfoText = document.getElementById(`${side}SystemInfoText`);
        $.get(`/systeminfo/${side}`, function (data) {
            // document.getElementById(`${side}SystemInfoText`).innerText = data;
            let content = '<ul class="list-group">';
            // 遍历 jsonData 中的每个键值对
            for (const [key, value] of Object.entries(data)) {
                // 如果该项有值，则显示
                const strValue = String(value);
                if (strValue.trim()) {
                    content += `<li class="list-group-item"><strong>${formatKey(key)}:</strong><pre>${strValue}</pre></li>`;
                }
            }
            content += '</ul>';

            // 将生成的内容插入到页面中
            systemInfoText.innerHTML = content;
        }).fail(function () {
            systemInfoText.innerHTML = i18next.t('common.getInfoFail');
        });
    }

    // 获取可用于ACS的网卡信息
    function getAvailableNics() {
        $.get('/wifi_acs', function (data) {
            $('#available-acs-nics-container').empty();  // 清空之前的内容
            // 遍历网卡信息并生成卡片
            $.each(data, function (interfaceName, driver) {
                const nicInfo = $(`
                    <h4 class="mt-4 d-flex justify-content-center align-items-center p-1 bg-secondary text-white rounded-2">
                        ${interfaceName} (${driver})
                        <button class="btn btn-info btn-sm ms-2" id="acs-scan-${interfaceName}" data-i18n="acs.startScan">开始扫描</button>
                    </h4>
                    <div class="d-flex justify-content-center align-items-center mt-3">
                        <div id="acs-result-${interfaceName}"> <!-- ACS 结果将在此加载 --> </div>
                    </div>
                `);
                $('#available-acs-nics-container').append(nicInfo);

                // 为 开始扫描 按钮绑定点击事件
                $(`#acs-scan-${interfaceName}`).on('click', function () {
                    execAcsScan(interfaceName);
                    $(`#acs-result-${interfaceName}`).text(i18next.t('acs.scanTips'));
                });
            });
        }).fail(function () {
            console.error(i18next.t('acs.getNicFail'));
        });
    }

    // 执行 ACS 扫描
    function execAcsScan(interfaceName) {
        $.get(`/wifi_acs/${interfaceName}`, function (data) {
            $(`#acs-result-${interfaceName}`).empty();  // 清空之前的内容
            // 获取显示系统信息的 div
            const acsResult = document.getElementById(`acs-result-${interfaceName}`);
            let content = '<ul class="list-group">';
            // 遍历结果信息并生成卡片
            $.each(data, function (file, result) {
                content += `
                    <li class="list-group-item">
                    <strong class="d-block bg-secondary text-white p-1 rounded-2">${file}:</strong>
                    <pre class="mb-0">${result}</pre>
                    </li>
                `;
            });
            content += '</ul>';
            acsResult.innerHTML = content;
        }).fail(function () {
            console.error(i18next.t('acs.acsFail'));
        });

    }

    // 获取固件列表
    function getFirmwareList() {
        $.get('/upgrade/list', function (data) {
            if (data.firmwares.length > 0) {
                var html = '<ul class="list-group">';
                data.firmwares.forEach(function (firmware) {
                    html += `
                    <li class="list-group-item d-flex justify-content-between align-items-center">
                        ${firmware}
                        <div>
                            <button class="btn btn-warning btn-sm deleteBtn" data-firmware="${firmware}" data-i18n="common.delete">删除</button>
                            <button class="btn btn-info btn-sm sendBtn" data-firmware="${firmware}" data-i18n="common.upload">上传</button>
                            <button class="btn btn-danger btn-sm upgradeBtn" data-firmware="${firmware}" data-i18n="firmwareUpgrade.upgrade">刷写</button>
                        </div>
                    </li>
                    `;
                });
                html += '</ul>';
                $('#firmwareList').html(html);
                listenFirmwareOperate();
            } else {
                $('#firmwareList').html(`<div class="alert alert-info" data-i18n="firmwareUpgrade.noAvailableFirmware">没有可用固件，请先上传固件到GS。</div>`);
            }
        });
    }

    // 上传固件
    function uploadFirmware() {
        var formData = new FormData($('#firmwareUploadForm')[0]);
        $.ajax({
            url: '/upgrade/upload',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function (response) {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-success">${i18next.t('common.uploadSuccess')}: ${response.message}</div>`);
                getFirmwareList();
            },
            error: function () {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-danger">${i18next.t('common.uploadFail')}</div>`);
            }
        });
    }

    // 执行固件操作
    function listenFirmwareOperate() {
        // 刷写固件
        $('#firmwareList').off('click', '.upgradeBtn').on('click', '.upgradeBtn', function () {
            $('#firmwareUpgradeStatus').html(`<div class="alert alert-success ">${i18next.t('firmwareUpgrade.upgradeTips')}</div>`);
            var firmware = $(this).data('firmware');
            $.post('/upgrade/execute', { firmware: firmware }, function (response) {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-success ">${response.message}</div>`);
                getSysupgradeProcess();
            }).fail(function () {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-danger">${i18next.t('firmwareUpgrade.upgradeFail')}</div>`);
            });

            function getSysupgradeProcess() {
                document.getElementById("log-container").style.display = "block";
                var sysupgradeStdout = document.getElementById("sysupgrade-stdout")
                const logContainer = document.getElementById('log-container');
                const ansiConverter = new AnsiUp();
                sysupgradeStdout.innerHTML = "";
                var eventSource = new EventSource("/upgrade/progress");
                eventSource.onmessage = function (event) {
                    const html = ansiConverter.ansi_to_html(event.data);
                    sysupgradeStdout.innerHTML += html + "<br>";
                    // 自动滚动到最底部
                    logContainer.scrollTop = logContainer.scrollHeight;
                };

                eventSource.onerror = function () {
                    console.log("SSE connect closed");
                    eventSource.close();  // 关闭 SSE 连接，防止重复连接
                };
            }
        });

        // 发送固件
        $('#firmwareList').off('click', '.sendBtn').on('click', '.sendBtn', function () {
            $('#firmwareUpgradeStatus').html(`<div class="alert alert-info ">${i18next.t('firmwareUpgrade.sendFirmwareTips')}</div>`);
            var firmware = $(this).data('firmware');
            $.post('/upgrade/send', { firmware: firmware }, function (response) {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-success">${response.message}</div>`);
            }).fail(function () {
                $('#firmwareUpgradeStatus').html(`<div class="alert alert-danger">${i18next.t('firmwareUpgrade.sendFail')}</div>`);
            });
        });

        // 删除固件
        $('#firmwareList').off('click', '.deleteBtn').on('click', '.deleteBtn', function () {
            var firmware = $(this).data('firmware');
            if (confirm(i18next.t('common.confirmDelete', {filename: firmware}))) {
                $.ajax({
                    url: '/upgrade/delete',
                    type: 'POST',
                    data: { firmware: firmware },
                    success: function (response) {
                        $('#firmwareUpgradeStatus').html(`<div class="alert alert-success">${i18next.t('common.deleteSuccess')}: ${response.message}</div>`);
                        getFirmwareList(); // 删除后刷新页面
                    },
                    error: function () {
                        $('#firmwareUpgradeStatus').html(`<div class="alert alert-danger">${i18next.t('common.deleteFail')}</div>`);
                        // alert('删除失败，请重试');
                    }
                });
            }
        });
    }

    // 上传救砖固件
    function uploadRescueFirmware() {
        // 当选择文件后，提交文件
        $('#rescueFirmwareInput').change(function () {
            var formData = new FormData();
            formData.append('firmware', $('#rescueFirmwareInput')[0].files[0]);
            $.ajax({
                url: '/upgrade/upload',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function (response) {
                    $('#rescueServiceStatus').html(`<div class="alert alert-success">${i18next.t('common.uploadSuccess')}</div>`);
                },
                error: function (xhr, status, error) {
                    var errorMessage = xhr.responseJSON ? xhr.responseJSON.error : "Upload failed";
                    $('#rescueServiceStatus').html(`<div class="alert alert-danger">${i18next.t('common.uploadFail')}${errorMessage}</div>`);
                }
            });
        });
    }

    // 将客户端时间同步到SBC
    function syncTimeToServer() {
        let now = new Date();
        let formattedTime = now.toISOString(); // 获取 ISO 8601 格式的时间
        let timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone; // 获取浏览器时区
        $.ajax({
            url: "/sync-time",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ time: formattedTime, timezone: timeZone }),
            success: function (response) {
                console.log("Server time synced:", response);
            },
            error: function (error) {
                console.error("Sync time Failed:", error.responseText);
            }
        });
    }

    syncTimeToServer();  // 将客户端时间同步到SBC
    loadGSConfig();  // 初始化页面时加载 GS 配置
    loadDroneConfig("wfb");  // 初始化页面时加载 Drone wfb 配置
    loadDroneConfig("majestic");  // 初始化页面时加载 Drone majestic 配置
    loadVideoFiles();  // 加载DVR文件列表
    loadCurrentWfbKey();  // 加载当前使用的key
    loadWfbKeyConfig();  // 加载wfb key pair
    loadSystemInfo("gs");  // 加载 GS 系统信息
    loadSystemInfo("drone");  // 加载 Drone 系统信息
    getAvailableNics(); // 获取可用于ACS的网卡
    getFirmwareList();  // 加载固件列表
    uploadRescueFirmware(); //监听救砖固件上传

    listenToButtons();  // 监听WEB按钮（代替物理按钮）
    listenToDroneSettingButtons();  // 监听Drone 快捷设置按钮

    // document.getElementById('refreshDvrFiles').addEventListener('click', loadVideoFiles);
    document.getElementById('refreshDvrFiles').onclick = loadVideoFiles;  // 点击 DVR管理 标题刷新DVR文件列表
    document.getElementById('refreshGsSystemInfo').onclick = function () { loadSystemInfo("gs"); };  // 点击 GS信息 标题刷新信息
    document.getElementById('refreshDroneSystemInfo').onclick = function () { loadSystemInfo("drone"); };  // 点击 Drine信息 标题刷新信息
    document.getElementById('refreshAcsInfo').onclick = getAvailableNics;  // 点击 ACS 标题刷新ACS信息
    document.getElementById('refreshCurrentWfbKey').onclick = loadCurrentWfbKey; // 点击 wfb key配置 标题重载当前key
    document.getElementById('firmwareUploadBtn').onclick = uploadFirmware; // 点击 wfb key配置 标题重载当前key

    // 加载 gs 配置
    $("#reload-button-gs").on("click", function () {
        loadGSConfig();
    });

    // 保存 gs 配置
    $("#save-button-gs").on("click", function () {
        saveGSConfig();
    });

    // 加载 Drone wfb 配置
    $("#reload-button-drone-wfb").on("click", function () {
        loadDroneConfig("wfb");
    });

    // 保存 Drone wfb 配置
    $("#save-button-drone-wfb").on("click", function () {
        saveDroneConfig("wfb");
    });

    // 保存并应用 Drone wfb 配置
    $("#apply-button-drone-wfb").on("click", function () {
        saveDroneConfig("wfb");
        sendButtonFunctionToBackend("drone_btn_restart_wfb");
    });

    // 加载 Drone majestic 配置
    $("#reload-button-drone-majestic").on("click", function () {
        loadDroneConfig("majestic");
    });

    // 保存 Drone majestic 配置
    $("#save-button-drone-majestic").on("click", function () {
        saveDroneConfig("majestic");
    });

    // 保存并应用 Drone majestic 配置
    $("#apply-button-drone-majestic").on("click", function () {
        saveDroneConfig("majestic");
        sendButtonFunctionToBackend("drone_btn_restart_majestic");
    });

    // 启动救砖服务
    $("#startRescueServiceBtn").on("click", function () {
        sendButtonFunctionToBackend("gs_btn_start_rescue");
        $(this).hide();
        $("#stopRescueServiceBtn").show();
        setTimeout(function () {
            $('#openRescueTerminalBtn').click();
        }, 1500);
    });

    // 停止救砖服务
    $("#stopRescueServiceBtn").on("click", function () {
        sendButtonFunctionToBackend("gs_btn_stop_rescue");
        $(this).hide();
        $("#startRescueServiceBtn").show();
    });

    // 监听标签页切换事件
    $('#myTab a').on('shown.bs.tab', function (e) {
        if ($(e.target).attr('id') === 'droneconfig-tab') {
            loadGSConfig();
        }
    });

    // 按下"上传救砖固件"按钮，触发文件选择框
    $('#uploadRescueFirmwareBtn').click(function () {
        $('#rescueFirmwareInput').click();
    });

    // 监听模态框关闭事件，停止视频播放
    document.getElementById('previewModal').addEventListener('hidden.bs.modal', function () {
        const video = document.getElementById('previewVideo');
        video.pause();
        video.currentTime = 0;
    });
});

