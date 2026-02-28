function detailsApp() {
  return {
    image: null,
    baseUrl: "",

    async init() {

        const id = this.getImageIdFromParam()
        await this.getImageDetails(id)

    },

    async getImageDetails(id) {
        if (id == null) return

        try {
            const res = await fetch(`/api/images/${id}`)
            const resJson = await this.raiseForStatus(res)
            this.image = resJson
        } catch(err) {
            console.error("failed to fetch image details: ", err)
        }
    },

    getImageIdFromParam() {
        const params = new URLSearchParams(window.location.search);
        this.orderId = params.get("id")
        return this.orderId
    },

    async raiseForStatus(res) {
        if (!res.ok) {
            let message;
            try {
                const data = await res.json();
                message = data?.message || JSON.stringify(data);
            } catch {
                message = await res.text();
            }
            throw new Error(`HTTP ${res.status}: ${message}`);
        }

        const data = await res.json()
        return data;
    },
  }
}
