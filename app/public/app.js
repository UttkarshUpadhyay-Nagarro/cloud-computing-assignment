const form = document.querySelector("#upload-form");
const input = document.querySelector("#document");
const fileName = document.querySelector("#file-name");
const status = document.querySelector("#status");

input.addEventListener("change", () => {
  fileName.textContent = input.files[0]?.name || "PDF, JPG, PNG or DOCX up to 10 MB";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.textContent = "Uploading...";
  status.className = "status busy";
  try {
    const response = await fetch("/upload", { method: "POST", body: new FormData(form) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Upload failed");
    status.textContent = `${result.message}: ${result.fileName}`;
    status.className = "status success";
    form.reset();
    fileName.textContent = "PDF, JPG, PNG or DOCX up to 10 MB";
  } catch (error) {
    status.textContent = error.message;
    status.className = "status error";
  }
});