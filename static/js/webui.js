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
            $('#editModalLabel').text(`正在编辑: ${filename}`);  // 模态框标题
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
                alert('文件已保存！');
                $('#editModal').modal('hide');
            },
            error: function () {
                alert('保存文件失败！');
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
                alert(`按钮指令 ${buttonId} 已发送`);
            })
            .catch(error => {
                console.error('发生错误:', error);
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
                                加载配置成功！
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $('#load-result-gs-success-alert').alert('close');
            }, 2000);
        }).fail(function () {
            alert("加载 gs 配置失败，请手动重新加载！");
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
                alert("保存 gs 配置失败！");
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
                                加载配置成功！
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $(`#load-result-drone-${config_name}-success-alert`).alert('close');
            }, 2000);
        }).fail(function () {
            resultDiv.html(`<div class="alert alert-danger alert-dismissible fade show" role="alert" id="load-result-drone-${config_name}-success-alert">
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                加载 Drone ${config_name} 配置失败，请手动重新加载！
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
                alert(`保存 Drone ${config_name} 配置失败！`);
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
                    downloadBtn.textContent = "下载";
                    actionsCell.appendChild(downloadBtn);

                    const deleteBtn = document.createElement("button");
                    deleteBtn.className = "btn btn-danger btn-sm ms-1";
                    deleteBtn.textContent = "删除";
                    deleteBtn.onclick = function () { deleteVideoFile(file.name); };
                    actionsCell.appendChild(deleteBtn);

                    if (file.name.endsWith('.jpg') || file.name.endsWith('.jpeg') || file.name.endsWith('.png') || file.name.endsWith('.gif') || file.name.endsWith('.mp4') || file.name.endsWith('.avi')) {
                        const previewBtn = document.createElement("button");
                        previewBtn.className = "btn btn-info btn-sm ms-1";
                        previewBtn.textContent = "预览";
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
                    droneKeyDiv.innerHTML = '<b>Current Drone key: </b>加载失败，点击标题重新加载';
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
                                    <button type="button" class="btn btn-danger ms-2" id="apply-key-${keypair}-${side}">应用key</button>
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
                    <div class="d-flex justify-content-center align-items-center mt-3 sticky-top">
                        <!-- 按钮组 -->
                        <div>
                            <button type="button" class="btn btn-primary" id="upload-gs-key-${keypair}">上传 gs key</button>
                            <button type="button" class="btn btn-success" id="download-gs-key-${keypair}">下载 gs key</button>
                            <button type="button" class="btn btn-primary" id="upload-drone-key-${keypair}">上传 drone key</button>
                            <button type="button" class="btn btn-success" id="download-drone-key-${keypair}">下载 drone key</button>
                            <button type="button" class="btn btn-secondary" id="random-key-${keypair}">随机生成key</button>
                            <button type="button" class="btn btn-warning" id="save-key-${keypair}">保存到配置文件</button>
                        </div>
                    </div>`;
                container.append(button_key_pair);

                // 为随机生成按钮绑定点击事件
                $(`#random-key-${keypair}`).on('click', function () {
                    // 调用 getRandomWfbKey 函数并传递 keypair
                    getRandomWfbKey(keypair);
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
                                加载配置成功！
                            </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $(`#load-result-wfb-key-success-alert`).alert('close');
            }, 2000);
        }).fail(function () {
            alert(`加载 wfb key 配置失败，请手动重新加载！`);
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
                    console.log(`上传 ${side}:`, base64);
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
                alert('key 已保存！');
            },
            error: function () {
                alert('key 保存失败！');
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
                alert('key 已应用！');
            },
            error: function () {
                alert(`${keypairContent['name']} key 应用失败！`);
            }
        });
    }

    // 生成随机 wfb key 配置
    function getRandomWfbKey(keypair) {
        $.get('get_random_wfb_key', function (data) {
            const gsKeyBase64 = data.gs;
            const droneKeyBase64 = data.drone;
            // 使用 jQuery 查找具有 data-key="key1.gs" 属性的输入框并填充值
            $(`[data-key="wfb-${keypair}.gs"]`).val(gsKeyBase64);
            $(`[data-key="wfb-${keypair}.drone"]`).val(droneKeyBase64);

            const resultDiv = $(`#save-result-wfb-key`);
            resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-wfb-key-success-alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                生成随机 wfb key 成功！
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $(`#load-result-wfb-key-success-alert`).alert('close');
            }, 2000);
        }).fail(function () {
            alert(`生成随机 wfb key 失败`);
        });
    }

    function previewVideoFile(filename) {
        const fileUrl = `/download_video/${encodeURIComponent(filename)}`;
        const modal = new bootstrap.Modal(document.getElementById('previewModal'));
        const img = document.getElementById('previewImage');
        const video = document.getElementById('previewVideo');
        const videoSource = document.getElementById('previewVideoSource');

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
            .catch(() => alert("预览失败，文件可能已被删除或路径错误"));
    }

    function deleteVideoFile(filename) {
        if (!confirm(`确定要删除 ${filename} 吗？`)) return;

        fetch(`/delete_video/${encodeURIComponent(filename)}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    loadVideoFiles();
                } else {
                    alert("删除失败: " + data.message);
                }
            });
    }

    function loadSystenInfo(side) {
        // 获取显示系统信息的 div
        const systemInfoText = document.getElementById(`${side}SystemInfoText`);

        // 将数据逐项展示到页面
        function displaySystemInfo(data) {
            let content = '<ul class="list-group">';
            // 遍历 jsonData 中的每个键值对
            for (const [key, value] of Object.entries(data)) {
                // 如果该项有值，则显示
                if (value.trim()) {
                    content += `<li class="list-group-item"><strong>${formatKey(key)}:</strong><pre>${value}</pre></li>`;
                }
            }
            content += '</ul>';

            // 将生成的内容插入到页面中
            systemInfoText.innerHTML = content;
        }

        // 格式化键名，使其变得更友好（如 "gs_release" 转为 "Release Information"）
        function formatKey(key) {
            const formattedKey = key
                .replace(/_/g, ' ') // 替换下划线为空格
                .replace(/\b\w/g, char => char.toUpperCase()); // 首字母大写
            return formattedKey;
        }

        $.get(`/systeminfo/${side}`, function (data) {
            // document.getElementById(`${side}SystemInfoText`).innerText = data;
            // 调用函数显示系统信息
            displaySystemInfo(data);
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
                        <button class="btn btn-info btn-sm ms-2" id="acs-scan-${interfaceName}">开始扫描</button>
                    </h4>
                    <div class="d-flex justify-content-center align-items-center mt-3">
                        <div id="acs-result-${interfaceName}"> <!-- ACS 结果将在此加载 --> </div>
                    </div>
                `);
                $('#available-acs-nics-container').append(nicInfo);

                // 为 开始扫描 按钮绑定点击事件
                $(`#acs-scan-${interfaceName}`).on('click', function () {
                    execAcsScan(interfaceName);
                    $(`#acs-result-${interfaceName}`).text('扫描已开始，请等待扫描完成（5~10秒）。');
                });
            });
        }).fail(function () {
            console.error('获取网卡信息失败');
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
            console.error('ACS 扫描失败');
        });

    }


    loadGSConfig();  // 初始化页面时加载 GS 配置
    loadDroneConfig("wfb");  // 初始化页面时加载 Drone wfb 配置
    loadDroneConfig("majestic");  // 初始化页面时加载 Drone majestic 配置
    loadVideoFiles();  // 加载DVR文件列表
    loadCurrentWfbKey();  // 加载当前使用的key
    loadWfbKeyConfig();  // 加载wfb key pair
    loadSystenInfo("gs");  // 加载 GS 系统信息
    loadSystenInfo("drone");  // 加载 Drone 系统信息
    getAvailableNics(); // 获取可用于ACS的网卡

    listenToButtons();  // 监听WEB按钮（代替物理按钮）
    listenToDroneSettingButtons();  // 监听Drone 快捷设置按钮

    // document.getElementById('refreshDvrFiles').addEventListener('click', loadVideoFiles);
    document.getElementById('refreshDvrFiles').onclick = loadVideoFiles;  // 点击 DVR管理 标题刷新DVR文件列表
    document.getElementById('refreshGsSystemInfo').onclick = function() { loadSystenInfo("gs"); };  // 点击 GS信息 标题刷新信息
    document.getElementById('refreshDroneSystemInfo').onclick = function() { loadSystenInfo("drone"); };  // 点击 Drine信息 标题刷新信息
    document.getElementById('refreshAcsInfo').onclick = getAvailableNics;  // 点击 ACS 标题刷新ACS信息
    document.getElementById('refreshCurrentWfbKey').onclick = loadCurrentWfbKey; // 点击 wfb key配置 标题重载当前key

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

    // 监听标签页切换事件
    $('#myTab a').on('shown.bs.tab', function (e) {
        if ($(e.target).attr('id') === 'droneconfig-tab') {
            loadGSConfig();
        }
    });

    // 监听模态框关闭事件，停止视频播放
    document.getElementById('previewModal').addEventListener('hidden.bs.modal', function () {
        const video = document.getElementById('previewVideo');
        video.pause();
        video.currentTime = 0;
    });
});

