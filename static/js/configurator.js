// scripts.js
$(document).ready(function () {
    // 加载 GS 配置
    function loadGSConfig() {
        if ($("#gsconfig").hasClass("active")) {
            $.get("/load_gs_config/gs", function (data) {
                const container = $("#gs-config-container");
                container.empty(); // 清空容器

                // 动态生成配置表单
                for (const [key, value] of Object.entries(data)) {
                    const row = `
                        <div class="mb-3 px-3">
                            <label class="form-label">${key}</label>
                            <input type="text" class="form-control config-input" data-key="${key}" value="${value}" placeholder="${value}">
                        </div>`;
                    container.append(row);
                }
                const resultDiv = $("#save-result-gs");
                resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                加载配置成功！
                                </div>`);
                // resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
                // alert("加载配置成功！");
            }).fail(function () {
                alert("加载配置失败！");
            });
        }
    }

    // 保存 GS 配置
    function saveGSConfig() {
        if ($("#gsconfig").hasClass("active")) {
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
                        resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                        ${response.message}
                                        </div>`);
                    } else {
                        resultDiv.html(`<div class="alert alert-danger">${response.message}</div>`);
                    }
                },
                error: function () {
                    alert("保存配置失败！");
                },
            });
        }
    }

    // 加载 Drone wfb 配置
    function loadDroneWfbConfig() {
        if ($("#drone-config-wfb").hasClass("active")) {
            $.get("/load_drone_config/wfb", function (data) {
                const container = $("#drone-config-container-wfb");
                container.empty(); // 清空容器

                // 动态生成配置表单
                for (const [file, content] of Object.entries(data)) {
                    const titel_part = `<h4 class="mt-4 p-1 bg-secondary text-white rounded-2">${file}</h4>`
                                        // <hr class="border-primary">`
                    container.append(titel_part);
                    for (const [key, value] of Object.entries(content)) {
                        const row = `
                            <div class="mb-3 px-3">
                                <label class="form-label">${key}</label>
                                <input type="text" class="form-control config-input" data-key="${file}.${key}" value="${value}" placeholder="${value}">
                            </div>`;
                        container.append(row);
                    }
                }
                const resultDiv = $("#save-result-drone-wfb");
                resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                加载配置成功！
                                </div>`);
                // resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
                // alert("加载配置成功！");
            }).fail(function () {
                alert("加载配置失败！");
            });
        }
    }

    // 保存 Drone wfb配置
    function saveDroneWfbConfig() {
        if ($("#drone-config-wfb").hasClass("active")) {
            const data = {};
            $(".config-input").each(function () {
                const key = $(this).data("key");
                const value = $(this).val();
                data[key] = value;
            });

            $.ajax({
                url: "/save_drone_config/wfb",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(data),
                success: function (response) {
                    const resultDiv = $("#save-result-drone-wfb");
                    if (response.success) {
                        resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                        ${response.message}
                                        </div>`);
                    } else {
                        resultDiv.html(`<div class="alert alert-danger">${response.message}</div>`);
                    }
                },
                error: function () {
                    alert("保存配置失败！");
                },
            });
        }
    }

    // 加载 Drone majestic 配置
    function loadDroneMajesticConfig() {
        if ($("#drone-config-majestic").hasClass("active")) {
            $.get("/load_drone_config/majestic", function (data) {
                const container = $("#drone-config-container-majestic");
                container.empty(); // 清空容器

                // 动态生成配置表单
                for (const [file, content] of Object.entries(data)) {
                    const titel_part = `<h4 class="mt-4 p-1 bg-secondary text-white rounded-2">${file}</h4>`
                                        // <hr class="border-primary">`
                    container.append(titel_part);
                    for (const [key, value] of Object.entries(content)) {
                        const row = `
                            <div class="mb-3 px-3">
                                <label class="form-label">${key}</label>
                                <input type="text" class="form-control config-input" data-key="${file}.${key}" value="${value}" placeholder="${value}">
                            </div>`;
                        container.append(row);
                    }
                }
                const resultDiv = $("#save-result-drone-majestic");
                resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                加载配置成功！
                                </div>`);
                // resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
                // alert("加载配置成功！");
            }).fail(function () {
                alert("加载配置失败！");
            });
        }
    }

    // 保存 Drone Majestic 配置
    function saveDroneMajesticConfig() {
        if ($("#drone-config-majestic").hasClass("active")) {
            const data = {};
            $(".config-input").each(function () {
                const key = $(this).data("key");
                const value = $(this).val();
                data[key] = value;
            });

            $.ajax({
                url: "/save_drone_config/majestic",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(data),
                success: function (response) {
                    const resultDiv = $("#save-result-drone-majestic");
                    if (response.success) {
                        resultDiv.html(`<div class="alert alert-success alert-dismissible fade show" role="alert">
                                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                                        ${response.message}
                                        </div>`);
                    } else {
                        resultDiv.html(`<div class="alert alert-danger">${response.message}</div>`);
                    }
                },
                error: function () {
                    alert("保存配置失败！");
                },
            });
        }
    }

    // 初始化页面时加载 Drone 配置（只会在 "Drone 配置" 标签页激活时加载）
    // loadDroneConfig(); // 页面加载时默认加载配置，只有当 "Drone 配置" 标签页激活时才执行

    // 点击 "读取配置" 按钮时重新加载 GS 配置
    $("#reload-button-gs").on("click", function () {
        loadGSConfig(); // 仅在 "GS 配置" 标签页激活时重新加载
    });

    // 点击 "保存配置" 按钮时保存 GS 配置
    $("#save-button-gs").on("click", function () {
        saveGSConfig(); // 仅在 "GS 配置" 标签页激活时保存配置
    });

    // 点击 "读取配置" 按钮时重新加载 Drone 配置
    $("#reload-button-drone-wfb").on("click", function () {
        loadDroneWfbConfig(); // 仅在 "Drone 配置" 标签页激活时重新加载
    });

    // 点击 "保存配置" 按钮时保存 Drone 配置
    $("#save-button-drone-wfb").on("click", function () {
        saveDroneWfbConfig(); // 仅在 "Drone 配置" 标签页激活时保存配置
    });

    // 点击 "读取配置" 按钮时重新加载 Drone majestic 配置
    $("#reload-button-drone-majestic").on("click", function () {
        loadDroneMajesticConfig(); // 仅在 "Drone 配置" 标签页激活时重新加载
    });

    // 点击 "保存配置" 按钮时保存 Drone 配置
    $("#save-button-drone-majestic").on("click", function () {
        saveDroneMajesticConfig();
    });

    // 监听标签页切换事件，当 "Drone 配置" 标签页激活时重新加载配置
    $('#myTab a').on('shown.bs.tab', function (e) {
        if ($(e.target).attr('id') === 'droneconfig-tab') {
            loadDroneConfig(); // 如果 "Drone 配置" 标签页激活，重新加载配置
        }
    });
});
