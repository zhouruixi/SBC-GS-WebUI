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

    // 发送按钮 ID 到后端
    function sendButtonFunctionToBackend(function_name) {
        fetch('/exec_button_function', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ button_id: function_name })
        })
            .then(response => response.json())
            .then(data => {
                // console.log('服务器响应:', data);
                alert(`按钮指令 ${function_name} 已发送`);
            })
            .catch(error => {
                console.error('发生错误:', error);
            });
    }

    // 监听所有 id 以 gs_btn_ 开头的按钮
    function listenToButtons() {
        const buttons = document.querySelectorAll('[id^="gs_btn_"]');

        buttons.forEach(button => {
            button.addEventListener('click', function () {
                // 获取按钮的 id 并调用发送请求的函数
                const buttonId = button.id;
                const function_name = buttonId.slice(7)
                sendButtonFunctionToBackend(function_name);
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
                                <input type="text" class="form-control config-input" data-key="${key}" value="${value}" placeholder="${value}">
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
            // resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
            // alert("加载配置成功！");
        }).fail(function () {
            alert("加载 gs 配置失败，请手动重新加载！");
        });
        // }
    }

    // 保存 GS 配置
    function saveGSConfig() {
        // if ($("#gsconfig").hasClass("active")) {
        const data = {};
        $(".config-input").each(function () {
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
        // }
    }

    // 加载 Drone 配置
    function loadDroneConfig(config_name) {
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
                                    <input type="text" class="form-control config-input" data-key="${file}.${key}" value="${value}" placeholder="${value}">
                                </div>
                            </div>`;
                    container.append(row);
                }
            }
            const resultDiv = $(`#save-result-drone-${config_name}`);
            resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert" id="load-result-drone-${config_name}-success-alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                加载配置成功！
                                </div>`);
            // 设置 2 秒后自动消失
            setTimeout(function () {
                $(`#load-result-drone-${config_name}-success-alert`).alert('close');
            }, 2000);
            // resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
            // alert("加载配置成功！");
        }).fail(function () {
            alert(`加载 Drone ${config_name} 配置失败，请手动重新加载！`);
        });
    }

    // 保存 Drone 配置
    function saveDroneConfig(config_name) {
        const data = {};
        $(".config-input").each(function () {
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
                    resultDiv.html(`<div class="alert alert-danger">${response.message}</div>`);
                }
            },
            error: function () {
                alert(`保存 Drone ${config_name} 配置失败！`);
            },
        });
        // }
    }

    // 初始化页面时加载 Drone 配置
    loadGSConfig();
    loadDroneConfig("wfb");
    loadDroneConfig("majestic");

    // 初始化按钮监听
    listenToButtons();

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

    // 加载 Drone majestic 配置
    $("#reload-button-drone-majestic").on("click", function () {
        loadDroneConfig("majestic");
    });

    // 保存 Drone majestic 配置
    $("#save-button-drone-majestic").on("click", function () {
        saveDroneConfig("majestic");
    });

    // 监听标签页切换事件
    $('#myTab a').on('shown.bs.tab', function (e) {
        if ($(e.target).attr('id') === 'droneconfig-tab') {
            loadGSConfig();
        }
    });
});
