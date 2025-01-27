// scripts.js
$(document).ready(function () {
    // 加载 GS 配置，只有在 "GS 配置" 标签页激活时执行
    function loadGSConfig() {
        if ($("#gsconfig").hasClass("active")) { // 检查标签页是否处于激活状态
            $.get("/load_gs_config", function (data) {
                const container = $("#gs-config-container");
                container.empty(); // 清空容器

                // 动态生成配置表单
                for (const [key, value] of Object.entries(data)) {
                    const row = `
                        <div class="mb-3">
                            <label class="form-label">${key}</label>
                            <input type="text" class="form-control config-input" data-key="${key}" value="${value}" placeholder="${value}">
                        </div>`;
                    container.append(row);
                }
                const resultDiv = $("#save-result-gs");
                resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
                // alert("加载配置成功！");
            }).fail(function () {
                alert("加载配置失败！");
            });
        }
    }

    // 保存 GS 配置，只有在 "GS 配置" 标签页激活时执行
    function saveGSConfig() {
        if ($("#gsconfig").hasClass("active")) { // 检查标签页是否处于激活状态
            const data = {};
            $(".config-input").each(function () {
                const key = $(this).data("key");
                const value = $(this).val();
                data[key] = value;
            });

            $.ajax({
                url: "/save_gs_config",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(data),
                success: function (response) {
                    const resultDiv = $("#save-result-gs");
                    if (response.success) {
                        resultDiv.html(`<div class="alert alert-success">${response.message}</div>`);
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

    // 加载 Drone 配置，只有在 "Drone 配置" 标签页激活时执行
    function loadDroneConfig() {
        if ($("#droneconf").hasClass("active")) { // 检查标签页是否处于激活状态
            $.get("/load_drone_config", function (data) {
                const container = $("#drone-config-container");
                container.empty(); // 清空容器

                // 动态生成配置表单
                for (const [key, value] of Object.entries(data)) {
                    const row = `
                        <div class="mb-3">
                            <label class="form-label">${key}</label>
                            <input type="text" class="form-control config-input" data-key="${key}" value="${value}" placeholder="${value}">
                        </div>`;
                    container.append(row);
                }
                const resultDiv = $("#save-result");
                resultDiv.html(`<div class="alert alert-success">读取配置成功！</div>`);
                // alert("加载配置成功！");
            }).fail(function () {
                alert("加载配置失败！");
            });
        }
    }

    // 保存 Drone 配置，只有在 "Drone 配置" 标签页激活时执行
    function saveDroneConfig() {
        if ($("#droneconf").hasClass("active")) { // 检查标签页是否处于激活状态
            const data = {};
            $(".config-input").each(function () {
                const key = $(this).data("key");
                const value = $(this).val();
                data[key] = value;
            });

            $.ajax({
                url: "/save_drone_config",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(data),
                success: function (response) {
                    const resultDiv = $("#save-result");
                    if (response.success) {
                        resultDiv.html(`<div class="alert alert-success">${response.message}</div>`);
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
    $("#reload-button").on("click", function () {
        loadDroneConfig(); // 仅在 "Drone 配置" 标签页激活时重新加载
    });

    // 点击 "保存配置" 按钮时保存 Drone 配置
    $("#save-button").on("click", function () {
        saveDroneConfig(); // 仅在 "Drone 配置" 标签页激活时保存配置
    });

    // 监听标签页切换事件，当 "Drone 配置" 标签页激活时重新加载配置
    $('#myTab a').on('shown.bs.tab', function (e) {
        if ($(e.target).attr('id') === 'droneconf-tab') {
            loadDroneConfig(); // 如果 "Drone 配置" 标签页激活，重新加载配置
        }
    });
});
