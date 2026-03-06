<template>
  <div class="monitor-page">
    <div class="bg-orb bg-orb-left"></div>
    <div class="bg-orb bg-orb-right"></div>

    <section class="hero">
      <div class="hero-title-wrap">
        <h1 class="hero-title">Lab GPU Monitor</h1>
        <p class="hero-subtitle">仅保留 GPU 资源监控，5 分钟采样周期，低开销运行。</p>
      </div>
      <div class="hero-actions">
        <el-tag type="info" effect="plain" round>上次更新: {{ lastUpdatedAt || "初始化中" }}</el-tag>
        <el-button type="primary" @click="refreshNow" :loading="loading">立即刷新</el-button>
      </div>
    </section>

    <section class="overview-grid">
      <el-card class="overview-card">
        <div class="label">在线服务器</div>
        <div class="value">{{ onlineServers }} / {{ totalServers }}</div>
      </el-card>
      <el-card class="overview-card">
        <div class="label">离线服务器</div>
        <div class="value danger">{{ offlineServers }}</div>
      </el-card>
      <el-card class="overview-card">
        <div class="label">GPU 总数</div>
        <div class="value">{{ totalGpus }}</div>
      </el-card>
      <el-card class="overview-card">
        <div class="label">高负载 GPU</div>
        <div class="value warn">{{ busyGpus }}</div>
      </el-card>
    </section>

    <section v-loading="loading" class="server-grid">
      <el-card v-for="server in gup_data" :key="server.server_name" shadow="hover" class="server-card">
        <template #header>
          <div class="server-card-header">
            <div class="server-name">{{ server.server_name }}</div>
            <el-tag v-if="server.gpu_list.length > 0" type="success" effect="dark">ONLINE</el-tag>
            <el-tag v-else type="danger" effect="dark">OFFLINE</el-tag>
          </div>
        </template>

        <div v-if="server.gpu_list.length === 0" class="server-offline">
          无法获取该机器 GPU 状态
        </div>

        <div v-else>
          <div class="gpu-chip-row">
            <el-tag
              v-for="gpu in server.gpu_list"
              :key="gpu.num"
              :type="gpuBadgeType(gpu)"
              effect="plain"
              round
            >
              GPU{{ gpu.num }} · {{ gpu.gpu_util || 0 }}%
            </el-tag>
          </div>

          <div class="gpu-row" v-for="gpu in server.gpu_list" :key="`gpu-${server.server_name}-${gpu.num}`">
            <div class="gpu-row-title">
              <span>GPU{{ gpu.num }} · {{ gpu.name }}</span>
              <span>{{ gpu.temp }}°C</span>
            </div>
            <el-progress
              :stroke-width="16"
              :text-inside="true"
              :percentage="calcPercent(gpu.use_memory, gpu.total_memory)"
              :status="memoryStatus(gpu.use_memory, gpu.total_memory)"
              :format="() => `${gpu.use_memory}/${gpu.total_memory} MB`"
            />
            <el-progress
              :stroke-width="16"
              :text-inside="true"
              :percentage="Number(gpu.gpu_util || 0)"
              :status="utilStatus(gpu.gpu_util)"
              :format="(p) => `Util ${p}%`"
            />
          </div>
        </div>

        <template #footer>
          <div class="server-card-footer">
            <span>进程数: {{ serverProcessCount(server) }}</span>
            <el-button text type="primary" @click="openServerDetail(server)">查看详情</el-button>
          </div>
        </template>
      </el-card>
    </section>

    <el-drawer
      v-model="detailVisible"
      :title="selectedServer ? `${selectedServer.server_name} 进程详情` : '进程详情'"
      direction="rtl"
      size="58%"
    >
      <div v-if="!selectedServer || selectedServer.gpu_list.length === 0" class="server-offline">
        当前服务器离线或暂无 GPU 信息
      </div>
      <div v-else>
        <div
          class="detail-gpu-block"
          v-for="gpu in selectedServer.gpu_list"
          :key="`detail-${selectedServer.server_name}-${gpu.num}`"
        >
          <div class="detail-title">
            GPU{{ gpu.num }} · {{ gpu.name }} · {{ gpu.program_list.length }} 个进程
          </div>
          <el-table :data="gpu.program_list" size="small" stripe empty-text="暂无运行进程">
            <el-table-column prop="username" label="用户" min-width="100" />
            <el-table-column prop="pid" label="PID" min-width="90" />
            <el-table-column label="显存(MB)" min-width="110">
              <template #default="scope">
                {{ scope.row.use_memory }}
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="启动时间" min-width="180" />
            <el-table-column prop="duration" label="运行时长" min-width="120" />
            <el-table-column prop="command" label="命令" min-width="380" show-overflow-tooltip />
          </el-table>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script src="./_gpu_monitor.js" lang="js"></script>
<style src="./_gpu_monitor.less" lang="less" scoped></style>
