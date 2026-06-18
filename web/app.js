const resultEl = document.getElementById("result");

function show(obj) {
  resultEl.textContent = JSON.stringify(obj, null, 2);
  resultEl.className = obj.success ? "success" : "error";
}

document.getElementById("runBtn").addEventListener("click", async () => {
  const phone = document.getElementById("phone").value.trim();
  const btn = document.getElementById("runBtn");
  btn.disabled = true;
  btn.textContent = "处理中...";
  try {
    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    });
    const data = await res.json();
    show(data);
  } catch (e) {
    show({ success: false, message: "请求失败: " + e.message });
  } finally {
    btn.disabled = false;
    btn.textContent = "开始处理";
  }
});

document.getElementById("importBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) {
    show({ success: false, message: "请先选择配置文件" });
    return;
  }
  const btn = document.getElementById("importBtn");
  btn.disabled = true;
  btn.textContent = "导入中...";
  try {
    const form = new FormData();
    form.append("file", fileInput.files[0]);
    const res = await fetch("/api/config/import", { method: "POST", body: form });
    const data = await res.json();
    show(data);
  } catch (e) {
    show({ success: false, message: "请求失败: " + e.message });
  } finally {
    btn.disabled = false;
    btn.textContent = "导入配置";
  }
});
