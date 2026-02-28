function indexApp() {
  return {
    images: [],
    isUploadingImage: false,

    async init() {
      console.log(this.isUploadingImage)
    },

    getBaseURL() {
      return window.location.origin;
    },

  }
}
