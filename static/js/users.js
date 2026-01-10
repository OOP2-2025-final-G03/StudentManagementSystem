document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("user-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const mode = form.dataset.mode;        // create / edit
    const userId = form.dataset.userId;    // 編集時のみ

    const data = {
      user_id: document.getElementById("user_id").value,
      name: document.getElementById("name").value,
      birth_date: document.getElementById("birth_date").value,
      role: document.getElementById("role").value,
      department: document.getElementById("department").value,
      password: document.getElementById("password").value
    };

    const url = mode === "edit"
      ? `/users/${userId}/edit`
      : `/users/create`;

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": "Bearer " + localStorage.getItem("token")
        },
        body: JSON.stringify(data)
      });

      const result = await res.json();

      if (!res.ok) {
        const errorMsg =
          result.description || result.error || "処理に失敗しました";
        throw new Error(errorMsg);
      }

      document.getElementById("message").textContent =
        mode === "edit"
          ? "ユーザー情報を更新しました"
          : "ユーザーを登録しました";

      if (mode === "create") {
        form.reset();
      }

    } catch (err) {
      document.getElementById("message").textContent = err.message;
    }
  });
});
