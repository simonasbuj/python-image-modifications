import { raiseForStatus } from './utils.js';

function detailsApp() {
  return {
    image: null,
    error: null,

    async init() {

        const id = this.getImageIdFromParam()
        await this.getImageDetails(id)

    },

    async getImageDetails(id) {
        if (id == null) return

        try {
            const res = await fetch(`/api/images/${id}`)
            const resJson = await raiseForStatus(res)
            this.image = resJson
        } catch(err) {
            this.error = err
            console.log(this.error)
        }
    },

    getImageIdFromParam() {
        const params = new URLSearchParams(window.location.search);
        this.orderId = params.get("id")
        return this.orderId
    },
  }
}

window.detailsApp = detailsApp
