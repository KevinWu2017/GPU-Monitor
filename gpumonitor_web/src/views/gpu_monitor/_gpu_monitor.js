import { ElMessage } from "element-plus";

export default {
    name: "GpuMonitor",

    data() {
        return {
            pollIntervalMs: 5 * 60 * 1000,
            timer: null,
            loading: false,
            gup_data: [],
            detailVisible: false,
            selectedServer: null,
            lastUpdatedAt: "",
        };
    },

    computed: {
        totalServers() {
            return this.gup_data.length;
        },
        onlineServers() {
            return this.gup_data.filter((item) => item.gpu_list.length > 0).length;
        },
        offlineServers() {
            return this.totalServers - this.onlineServers;
        },
        totalGpus() {
            return this.gup_data.reduce((sum, server) => sum + server.gpu_list.length, 0);
        },
        busyGpus() {
            return this.gup_data.reduce(
                (sum, server) => sum + server.gpu_list.filter((gpu) => Number(gpu.gpu_util || 0) >= 60).length,
                0
            );
        },
    },

    mounted() {
        this.fetchGpuData();
        this.timer = setInterval(() => {
            this.fetchGpuData();
        }, this.pollIntervalMs);
    },

    beforeUnmount() {
        clearInterval(this.timer);
    },

    methods: {
        fetchGpuData() {
            this.loading = true;
            this.$http
                .get("/get_gpu_state")
                .then((res) => {
                    if (res.status === 200) {
                        this.gup_data = Array.isArray(res.data) ? res.data : [];
                        this.lastUpdatedAt = new Date().toLocaleString();
                        if (this.selectedServer) {
                            const latest = this.gup_data.find((item) => item.server_name === this.selectedServer.server_name);
                            if (latest) {
                                this.selectedServer = latest;
                            }
                        }
                    }
                })
                .catch(() => {
                    ElMessage.error("GPU 数据加载失败");
                })
                .finally(() => {
                    this.loading = false;
                });
        },
        refreshNow() {
            this.fetchGpuData();
        },
        openServerDetail(server) {
            this.selectedServer = server;
            this.detailVisible = true;
        },
        calcPercent(used, total) {
            if (!total) return 0;
            return Math.max(0, Math.min(100, Math.round((Number(used) / Number(total)) * 100)));
        },
        utilStatus(util) {
            const value = Number(util || 0);
            if (value >= 85) return "exception";
            if (value >= 60) return "warning";
            if (value >= 30) return "success";
            return "";
        },
        memoryStatus(used, total) {
            const value = this.calcPercent(used, total);
            if (value >= 90) return "exception";
            if (value >= 75) return "warning";
            if (value >= 50) return "success";
            return "";
        },
        serverProcessCount(server) {
            return server.gpu_list.reduce((sum, gpu) => sum + gpu.program_list.length, 0);
        },
        gpuBadgeType(gpu) {
            return Number(gpu.use_memory || 0) < 100 ? "success" : "info";
        },
    },
};
