let selectedFiles = [];

const fileInput = document.getElementById('image');
const previewContainer = document.getElementById('previewContainer');
let imageFiles = []; 

const MAX_FILE_SIZE_MB = 25; 
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024; // for converting to bytes to know the size

fileInput.addEventListener('change', (event) => {
  const files = Array.from(event.target.files);

  if (imageFiles.length + files.length > 10) {
    alert('You can only upload up to 10 files per listing.');
    return;
  }

  files.forEach((file) => {
    if (file.size > MAX_FILE_SIZE) {
      alert(`${file.name} is too large. Each file must be under ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }

    imageFiles.push(file);

    const reader = new FileReader();
    reader.onload = (e) => {
      const previewDiv = document.createElement('div');
      previewDiv.style.position = 'relative';
      previewDiv.style.display = 'inline-block';

      let previewElement;
      if (file.type.startsWith('video/')) {
        previewElement = document.createElement('video');
        previewElement.src = e.target.result;
        previewElement.controls = true;
        previewElement.style.maxWidth = '120px';
        previewElement.style.borderRadius = '6px';
        previewElement.style.border = '1px solid #ccc';
      } else {
        previewElement = document.createElement('img');
        previewElement.src = e.target.result;
        previewElement.style.maxWidth = '120px';
        previewElement.style.borderRadius = '6px';
        previewElement.style.border = '1px solid #ccc';
      }

      const deleteBtn = document.createElement('button');
      deleteBtn.textContent = '×';
      deleteBtn.style.position = 'absolute';
      deleteBtn.style.top = '0';
      deleteBtn.style.right = '0';
      deleteBtn.style.background = 'red';
      deleteBtn.style.color = 'white';
      deleteBtn.style.border = 'none';
      deleteBtn.style.borderRadius = '50%';
      deleteBtn.style.cursor = 'pointer';
      deleteBtn.style.width = '20px';
      deleteBtn.style.height = '20px';
      deleteBtn.style.lineHeight = '16px';
      deleteBtn.style.fontSize = '14px';

      deleteBtn.addEventListener('click', () => {
        previewContainer.removeChild(previewDiv);
        imageFiles = imageFiles.filter((f) => f !== file);

        // to reset after user deletes smt
         if (imageFiles.length === 0) {
            fileInput.value = '';
        }
      });

      previewDiv.appendChild(previewElement);
      previewDiv.appendChild(deleteBtn);
      previewContainer.appendChild(previewDiv);
    };
    reader.readAsDataURL(file);
  });
});

function removeImage(index) {
  selectedFiles.splice(index, 1);
  const container = document.getElementById('imagePreviewContainer');
  container.innerHTML = "";

  selectedFiles.forEach((file, i) => {
    const reader = new FileReader();
    reader.onload = function(e) {
      const previewDiv = document.createElement("div");
      previewDiv.classList.add("preview-item");

      const img = document.createElement("img");
      img.src = e.target.result;
      img.alt = `Photo ${i + 1}`;

      const deleteBtn = document.createElement("button");
      deleteBtn.textContent = "✕";
      deleteBtn.classList.add("delete-btn");
      deleteBtn.onclick = () => removeImage(i);

      previewDiv.appendChild(img);
      previewDiv.appendChild(deleteBtn);
      container.appendChild(previewDiv);
    };
    reader.readAsDataURL(file);
  });
}

const nameInput = document.getElementById('productName');
const charCount = document.getElementById('charCount');

nameInput.addEventListener('input', () => {
  charCount.textContent = `${nameInput.value.length} / 120`;
});

