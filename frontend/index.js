import { raiseForStatus } from './utils.js';

function indexApp() {
  return {
    images: [],
    page: 1,
    isUploading: false,

    async init() {
      await this.getImages(this.page)
    },

    async getImages(page) {
        if (page == null) return

        try {
            const res = await fetch(`/api/images/`)
            const resJson = await raiseForStatus(res)
            if (page = 1) {
              this.images = resJson
            } else {
              this.images.push(...resJson)
            }
            this.page += 1
        } catch(err) {
            this.error = err
            console.log(this.error)
        }
    },

    async uploadImage() {
      const file = this.$refs.fileInput.files[0];

      if (!file) {
        alert('Please select an image first');
        return;
      }

      this.isUploading = true;
      this.error = null;

      try {
        const formData = new FormData()
        formData.append('file', file)

        const res = await fetch('/api/images/', {
          method: 'POST',
          body: formData,
        })

        await raiseForStatus(res)

        await this.getImages(1)
        this.$refs.fileInput.value = ''

      } catch(err) {
        this.error = err;
        console.log(this.error);
        alert('Upload failed: ' + err.message);
      } finally {
        this.isUploading = false;
      }
    },
  }
}

window.indexApp = indexApp
