<template>
  <div class="api-documentation page">
    <div class="doc-layout">
      <!-- Sidebar navigation -->
      <nav class="doc-sidebar">
        <h3 class="sidebar-title">画宗开放 API v1</h3>
        <ul class="nav-list">
          <li
            v-for="section in sections"
            :key="section.id"
            :class="{ active: activeSection === section.id }"
          >
            <a @click="scrollTo(section.id)">{{ section.label }}</a>
            <ul v-if="section.children" class="nav-sublist">
              <li
                v-for="child in section.children"
                :key="child.id"
                :class="{ active: activeSection === child.id }"
              >
                <a @click="scrollTo(child.id)">{{ child.label }}</a>
              </li>
            </ul>
          </li>
        </ul>
      </nav>

      <!-- Main doc content -->
      <main class="doc-content" ref="docContent">
        <!-- Auth -->
        <section id="auth" class="doc-section">
          <h1>认证</h1>
          <p>所有 API 请求需要在请求头中携带 API Key：</p>
          <div class="code-block">
            <div class="code-header">HTTP Header</div>
            <pre><code>Authorization: Bearer hz_live_xxxxxxxxxxxxxxxxxxxxxxxx</code></pre>
          </div>
          <p>
            API Key 可在
            <router-link :to="{ name: 'api-key-manager' }">API 密钥管理</router-link>
            页面创建和管理。每个密钥可配置独立的权限范围和速率限制。
          </p>
          <div class="info-box">
            <strong>安全提示：</strong>密钥仅在创建时显示一次，请妥善保管。
            不要在客户端代码或版本控制中暴露密钥。
          </div>
        </section>

        <!-- Assets -->
        <section id="assets" class="doc-section">
          <h1>资产</h1>

          <!-- GET /assets -->
          <div id="assets-list" class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/assets</code>
            </div>
            <p class="endpoint-desc">获取资产列表，支持分页和过滤。</p>
            <h4>查询参数</h4>
            <table class="param-table">
              <thead>
                <tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr><td><code>page</code></td><td>integer</td><td>否</td><td>页码，默认 1</td></tr>
                <tr><td><code>per_page</code></td><td>integer</td><td>否</td><td>每页条数，默认 20，最大 100</td></tr>
                <tr><td><code>category_id</code></td><td>string</td><td>否</td><td>按分类 ID 过滤</td></tr>
                <tr><td><code>status</code></td><td>string</td><td>否</td><td>按状态过滤: draft / active / archived</td></tr>
                <tr><td><code>search</code></td><td>string</td><td>否</td><td>关键词搜索名称和标签</td></tr>
              </tbody>
            </table>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "data": [
    {
      "id": "a1b2c3d4",
      "name": "主角-李明",
      "category": "character",
      "status": "active",
      "tags": ["主角", "男性"],
      "thumbnail_url": "/api/thumbnails/a1b2c3d4.png",
      "usage_count": 42,
      "created_at": "2025-03-01T10:00:00Z",
      "updated_at": "2025-03-15T14:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 156,
    "total_pages": 8
  }
}</code></pre>
            </div>
          </div>

          <!-- GET /assets/:id -->
          <div id="assets-detail" class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}</code>
            </div>
            <p class="endpoint-desc">获取单个资产详情，包括文件列表和元数据。</p>
            <h4>路径参数</h4>
            <table class="param-table">
              <thead>
                <tr><th>参数</th><th>类型</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr><td><code>asset_id</code></td><td>string</td><td>资产 ID</td></tr>
              </tbody>
            </table>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "id": "a1b2c3d4",
  "name": "主角-李明",
  "category": "character",
  "description": "故事主角，28岁程序员",
  "status": "active",
  "tags": ["主角", "男性"],
  "metadata": { "height": "178cm", "style": "写实" },
  "files": [
    { "id": "f1", "name": "front.png", "size": 245000, "type": "image/png" }
  ],
  "versions": 3,
  "usage_count": 42,
  "created_at": "2025-03-01T10:00:00Z",
  "updated_at": "2025-03-15T14:30:00Z"
}</code></pre>
            </div>
          </div>

          <!-- POST /assets -->
          <div id="assets-create" class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge post">POST</span>
              <code class="endpoint-url">/open-api/v1/assets</code>
            </div>
            <p class="endpoint-desc">创建新资产。需要 <code>assets:write</code> 权限。</p>
            <h4>请求体</h4>
            <div class="code-block">
              <div class="code-header">JSON</div>
              <pre><code>{
  "name": "新场景-森林",
  "category": "scene",
  "description": "魔法森林场景",
  "tags": ["森林", "魔幻"],
  "metadata": { "lighting": "黄昏", "mood": "神秘" }
}</code></pre>
            </div>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">201 Created</div>
              <pre><code>{
  "id": "e5f6g7h8",
  "name": "新场景-森林",
  "category": "scene",
  "status": "draft",
  "created_at": "2025-03-20T09:00:00Z"
}</code></pre>
            </div>
          </div>

          <!-- PUT /assets/:id -->
          <div id="assets-update" class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge put">PUT</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}</code>
            </div>
            <p class="endpoint-desc">更新资产。需要 <code>assets:write</code> 权限。支持部分更新。</p>
            <h4>请求体</h4>
            <div class="code-block">
              <div class="code-header">JSON</div>
              <pre><code>{
  "name": "更新后的名称",
  "tags": ["新标签"],
  "status": "active"
}</code></pre>
            </div>
          </div>

          <!-- DELETE /assets/:id -->
          <div id="assets-delete" class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge delete">DELETE</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}</code>
            </div>
            <p class="endpoint-desc">删除资产。需要 <code>assets:delete</code> 权限。此操作不可恢复。</p>
          </div>
        </section>

        <!-- Search -->
        <section id="search" class="doc-section">
          <h1>搜索</h1>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/assets/search</code>
            </div>
            <p class="endpoint-desc">全文搜索资产。需要 <code>search</code> 权限。</p>
            <h4>查询参数</h4>
            <table class="param-table">
              <thead>
                <tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr><td><code>q</code></td><td>string</td><td>是</td><td>搜索关键词</td></tr>
                <tr><td><code>category</code></td><td>string</td><td>否</td><td>限定分类</td></tr>
                <tr><td><code>page</code></td><td>integer</td><td>否</td><td>页码</td></tr>
                <tr><td><code>per_page</code></td><td>integer</td><td>否</td><td>每页条数</td></tr>
              </tbody>
            </table>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "data": [
    {
      "id": "a1b2c3d4",
      "name": "主角-李明",
      "score": 0.95,
      "highlights": ["<em>主角</em>-李明"]
    }
  ],
  "meta": { "total": 12, "query_time_ms": 23 }
}</code></pre>
            </div>
          </div>
        </section>

        <!-- Categories -->
        <section id="categories" class="doc-section">
          <h1>分类</h1>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/categories</code>
            </div>
            <p class="endpoint-desc">获取分类树。需要 <code>categories:read</code> 权限。</p>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "data": [
    {
      "id": "cat-001",
      "name": "人物",
      "slug": "character",
      "icon": "user",
      "children": [
        { "id": "cat-002", "name": "主要角色", "parent_id": "cat-001" },
        { "id": "cat-003", "name": "配角", "parent_id": "cat-001" }
      ]
    }
  ]
}</code></pre>
            </div>
          </div>

          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/categories/{category_id}</code>
            </div>
            <p class="endpoint-desc">获取单个分类详情及其子分类。</p>
          </div>
        </section>

        <!-- Versions -->
        <section id="versions" class="doc-section">
          <h1>版本</h1>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}/versions</code>
            </div>
            <p class="endpoint-desc">获取资产的版本历史列表。</p>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "data": [
    {
      "version": 3,
      "comment": "更新了正面视图",
      "author": "张三",
      "created_at": "2025-03-15T14:30:00Z",
      "files_changed": 2
    }
  ]
}</code></pre>
            </div>
          </div>
        </section>

        <!-- Usages -->
        <section id="usages" class="doc-section">
          <h1>使用记录</h1>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}/usages</code>
            </div>
            <p class="endpoint-desc">获取资产在各项目中的使用记录。</p>
          </div>

          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge post">POST</span>
              <code class="endpoint-url">/open-api/v1/assets/{asset_id}/usages</code>
            </div>
            <p class="endpoint-desc">记录资产使用（外部工具集成时调用）。</p>
            <h4>请求体</h4>
            <div class="code-block">
              <div class="code-header">JSON</div>
              <pre><code>{
  "project_id": "proj-123",
  "context": "blender-scene-import",
  "tool": "Blender 4.1"
}</code></pre>
            </div>
          </div>
        </section>

        <!-- Graph -->
        <section id="graph" class="doc-section">
          <h1>图谱</h1>
          <div class="endpoint-card">
            <div class="endpoint-header">
              <span class="method-badge get">GET</span>
              <code class="endpoint-url">/open-api/v1/graph</code>
            </div>
            <p class="endpoint-desc">查询资产关系图谱。需要 <code>graph:read</code> 权限。</p>
            <h4>查询参数</h4>
            <table class="param-table">
              <thead>
                <tr><th>参数</th><th>类型</th><th>必填</th><th>说明</th></tr>
              </thead>
              <tbody>
                <tr><td><code>asset_id</code></td><td>string</td><td>否</td><td>以此资产为中心查询</td></tr>
                <tr><td><code>depth</code></td><td>integer</td><td>否</td><td>关系深度，默认 2</td></tr>
                <tr><td><code>relation_type</code></td><td>string</td><td>否</td><td>关系类型过滤</td></tr>
              </tbody>
            </table>
            <h4>响应示例</h4>
            <div class="code-block">
              <div class="code-header">200 OK</div>
              <pre><code>{
  "nodes": [
    { "id": "a1", "name": "主角-李明", "type": "character" },
    { "id": "a2", "name": "魔法森林", "type": "scene" }
  ],
  "edges": [
    { "source": "a1", "target": "a2", "relation": "appears_in" }
  ]
}</code></pre>
            </div>
          </div>
        </section>

        <!-- Rate Limiting -->
        <section id="rate-limiting" class="doc-section">
          <h1>速率限制</h1>
          <p>每个 API Key 有独立的速率限制（创建时配置，默认 100 次/分钟）。</p>
          <h4>响应头</h4>
          <table class="param-table">
            <thead>
              <tr><th>头部</th><th>说明</th></tr>
            </thead>
            <tbody>
              <tr><td><code>X-RateLimit-Limit</code></td><td>当前窗口允许的最大请求数</td></tr>
              <tr><td><code>X-RateLimit-Remaining</code></td><td>当前窗口剩余请求数</td></tr>
              <tr><td><code>X-RateLimit-Reset</code></td><td>窗口重置的 Unix 时间戳</td></tr>
            </tbody>
          </table>
          <p>超过限制时返回 <code>429 Too Many Requests</code>，请等待窗口重置后重试。</p>
        </section>

        <!-- Error Codes -->
        <section id="errors" class="doc-section">
          <h1>错误码</h1>
          <table class="param-table error-table">
            <thead>
              <tr><th>状态码</th><th>说明</th><th>处理建议</th></tr>
            </thead>
            <tbody>
              <tr>
                <td><code>400</code></td>
                <td>请求参数错误</td>
                <td>检查请求体和查询参数格式</td>
              </tr>
              <tr>
                <td><code>401</code></td>
                <td>未认证 — 缺少或无效的 API Key</td>
                <td>检查 Authorization 头格式和密钥有效性</td>
              </tr>
              <tr>
                <td><code>403</code></td>
                <td>权限不足 — API Key 缺少所需 scope</td>
                <td>在密钥管理页面添加对应权限</td>
              </tr>
              <tr>
                <td><code>404</code></td>
                <td>资源不存在</td>
                <td>确认资源 ID 正确且未被删除</td>
              </tr>
              <tr>
                <td><code>429</code></td>
                <td>请求过于频繁</td>
                <td>等待 X-RateLimit-Reset 后重试</td>
              </tr>
              <tr>
                <td><code>500</code></td>
                <td>服务器内部错误</td>
                <td>请稍后重试或联系管理员</td>
              </tr>
            </tbody>
          </table>
          <h4>错误响应格式</h4>
          <div class="code-block">
            <div class="code-header">JSON</div>
            <pre><code>{
  "error": {
    "code": "INSUFFICIENT_SCOPE",
    "message": "API Key 缺少 assets:write 权限",
    "required_scope": "assets:write"
  }
}</code></pre>
          </div>
        </section>

        <!-- Code Examples -->
        <section id="examples" class="doc-section">
          <h1>代码示例</h1>

          <div class="example-tabs">
            <span
              class="example-tab"
              :class="{ active: activeExample === 'curl' }"
              @click="activeExample = 'curl'"
            >cURL</span>
            <span
              class="example-tab"
              :class="{ active: activeExample === 'python' }"
              @click="activeExample = 'python'"
            >Python</span>
            <span
              class="example-tab"
              :class="{ active: activeExample === 'javascript' }"
              @click="activeExample = 'javascript'"
            >JavaScript</span>
          </div>

          <div v-if="activeExample === 'curl'">
            <h4>获取资产列表</h4>
            <div class="code-block">
              <div class="code-header">bash</div>
              <pre><code>curl -X GET "https://your-domain.com/api/open-api/v1/assets?page=1&per_page=10" \
  -H "Authorization: Bearer hz_live_xxxxxxxx"</code></pre>
            </div>

            <h4>创建资产</h4>
            <div class="code-block">
              <div class="code-header">bash</div>
              <pre><code>curl -X POST "https://your-domain.com/api/open-api/v1/assets" \
  -H "Authorization: Bearer hz_live_xxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新角色",
    "category": "character",
    "tags": ["NPC"]
  }'</code></pre>
            </div>
          </div>

          <div v-if="activeExample === 'python'">
            <h4>获取资产列表</h4>
            <div class="code-block">
              <div class="code-header">python</div>
              <pre><code>import requests

API_KEY = "hz_live_xxxxxxxx"
BASE_URL = "https://your-domain.com/api/open-api/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}

# 获取资产列表
resp = requests.get(
    f"{BASE_URL}/assets",
    headers=headers,
    params={"page": 1, "per_page": 20, "category_id": "character"}
)
assets = resp.json()

for asset in assets["data"]:
    print(f"{asset['name']} ({asset['category']})")

# 创建资产
new_asset = requests.post(
    f"{BASE_URL}/assets",
    headers=headers,
    json={
        "name": "新角色",
        "category": "character",
        "description": "测试创建",
        "tags": ["NPC", "测试"]
    }
)
print(f"Created: {new_asset.json()['id']}")</code></pre>
            </div>
          </div>

          <div v-if="activeExample === 'javascript'">
            <h4>获取资产列表</h4>
            <div class="code-block">
              <div class="code-header">javascript</div>
              <pre><code>const API_KEY = 'hz_live_xxxxxxxx'
const BASE_URL = 'https://your-domain.com/api/open-api/v1'

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
}

// 获取资产列表
const resp = await fetch(
  `${BASE_URL}/assets?page=1&per_page=20`,
  { headers }
)
const { data, meta } = await resp.json()
console.log(`共 ${meta.total} 个资产`)

// 创建资产
const created = await fetch(`${BASE_URL}/assets`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    name: '新角色',
    category: 'character',
    description: '通过 API 创建',
    tags: ['NPC', '测试']
  })
})
const newAsset = await created.json()
console.log(`Created: ${newAsset.id}`)</code></pre>
            </div>
          </div>
        </section>
      </main>
    </div>
  </div>
</template>

<script>
export default {
  name: 'api-documentation',

  data() {
    return {
      activeSection: 'auth',
      activeExample: 'curl',
      sections: [
        { id: 'auth', label: '认证' },
        {
          id: 'assets',
          label: '资产',
          children: [
            { id: 'assets-list', label: '列表' },
            { id: 'assets-detail', label: '详情' },
            { id: 'assets-create', label: '创建' },
            { id: 'assets-update', label: '更新' },
            { id: 'assets-delete', label: '删除' }
          ]
        },
        { id: 'search', label: '搜索' },
        { id: 'categories', label: '分类' },
        { id: 'versions', label: '版本' },
        { id: 'usages', label: '使用记录' },
        { id: 'graph', label: '图谱' },
        { id: 'rate-limiting', label: '速率限制' },
        { id: 'errors', label: '错误码' },
        { id: 'examples', label: '代码示例' }
      ]
    }
  },

  mounted() {
    this.setupScrollSpy()
  },

  beforeUnmount() {
    if (this._observer) this._observer.disconnect()
  },

  methods: {
    scrollTo(id) {
      const el = document.getElementById(id)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        this.activeSection = id
      }
    },

    setupScrollSpy() {
      const options = {
        root: this.$refs.docContent,
        rootMargin: '-80px 0px -60% 0px',
        threshold: 0
      }
      this._observer = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            this.activeSection = entry.target.id
          }
        }
      }, options)

      this.$nextTick(() => {
        const sectionEls = document.querySelectorAll('.doc-section, .endpoint-card')
        sectionEls.forEach((el) => {
          if (el.id) this._observer.observe(el)
        })
      })
    }
  }
}
</script>

<style lang="scss" scoped>
.api-documentation {
  height: 100vh;
  overflow: hidden;
}

.doc-layout {
  display: flex;
  height: 100%;
}

/* Sidebar */
.doc-sidebar {
  width: 220px;
  min-width: 220px;
  background: #161b22;
  border-right: 1px solid #30363d;
  padding: 24px 0;
  overflow-y: auto;
  position: sticky;
  top: 0;
}

.sidebar-title {
  color: #e5e7eb;
  font-size: 0.95em;
  font-weight: 700;
  padding: 0 20px;
  margin-bottom: 20px;
}

.nav-list {
  list-style: none;
  padding: 0;
  margin: 0;

  > li {
    > a {
      display: block;
      padding: 8px 20px;
      color: #8b949e;
      font-size: 0.9em;
      text-decoration: none;
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: all 0.15s;

      &:hover {
        color: #c9d1d9;
        background: #1c2129;
      }
    }

    &.active > a {
      color: #58a6ff;
      border-left-color: #58a6ff;
      background: #1c2129;
    }
  }
}

.nav-sublist {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    a {
      display: block;
      padding: 5px 20px 5px 36px;
      color: #6b7280;
      font-size: 0.82em;
      text-decoration: none;
      cursor: pointer;
      transition: color 0.15s;

      &:hover {
        color: #c9d1d9;
      }
    }

    &.active a {
      color: #58a6ff;
    }
  }
}

/* Main content */
.doc-content {
  flex: 1;
  overflow-y: auto;
  padding: 40px 48px;
  scroll-behavior: smooth;
}

.doc-section {
  margin-bottom: 48px;
  padding-bottom: 32px;
  border-bottom: 1px solid #21262d;

  &:last-child {
    border-bottom: none;
  }

  h1 {
    color: #e5e7eb;
    font-size: 1.6em;
    font-weight: 700;
    margin-bottom: 16px;
  }

  p {
    color: #8b949e;
    line-height: 1.7;
    margin-bottom: 16px;
    font-size: 0.95em;

    a {
      color: #58a6ff;
      text-decoration: none;

      &:hover {
        text-decoration: underline;
      }
    }

    code {
      background: #0d1117;
      color: #e06c75;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 0.88em;
    }
  }

  h4 {
    color: #c9d1d9;
    font-size: 0.95em;
    font-weight: 600;
    margin-top: 20px;
    margin-bottom: 10px;
  }
}

.info-box {
  background: #0d1117;
  border-left: 4px solid #f59e0b;
  padding: 12px 16px;
  border-radius: 0 6px 6px 0;
  color: #8b949e;
  font-size: 0.9em;
  margin: 16px 0;

  strong {
    color: #f59e0b;
  }
}

/* Endpoint cards */
.endpoint-card {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
}

.endpoint-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.method-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.78em;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;

  &.get {
    background: #238636;
    color: #fff;
  }
  &.post {
    background: #1f6feb;
    color: #fff;
  }
  &.put {
    background: #d97706;
    color: #fff;
  }
  &.delete {
    background: #da3633;
    color: #fff;
  }
}

.endpoint-url {
  color: #c9d1d9;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.95em;
}

.endpoint-desc {
  color: #8b949e;
  font-size: 0.9em;
  margin-bottom: 12px;

  code {
    background: #161b22;
    color: #e06c75;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    font-size: 0.88em;
  }
}

/* Param table */
.param-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 16px;

  th {
    background: #161b22;
    color: #8b949e;
    font-weight: 600;
    font-size: 0.82em;
    text-align: left;
    padding: 8px 12px;
    border-bottom: 1px solid #30363d;
  }

  td {
    padding: 8px 12px;
    color: #c9d1d9;
    font-size: 0.88em;
    border-bottom: 1px solid #21262d;

    code {
      background: #161b22;
      color: #e06c75;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
      font-size: 0.9em;
    }
  }
}

/* Code blocks */
.code-block {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;
  margin: 12px 0;
}

.code-header {
  background: #161b22;
  color: #6b7280;
  padding: 6px 14px;
  font-size: 0.78em;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #30363d;
}

.code-block pre {
  margin: 0;
  padding: 16px;
  overflow-x: auto;
}

.code-block code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85em;
  color: #c9d1d9;
  line-height: 1.6;
}

/* Example tabs */
.example-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border-bottom: 1px solid #30363d;
}

.example-tab {
  padding: 10px 20px;
  color: #8b949e;
  font-size: 0.9em;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s;

  &:hover {
    color: #c9d1d9;
  }

  &.active {
    color: #58a6ff;
    border-bottom-color: #58a6ff;
  }
}

/* Nested code blocks inside endpoint cards */
.endpoint-card .code-block {
  background: #161b22;

  .code-header {
    background: #1c2129;
  }
}

/* Dark theme by default (matching project) */
.dark .api-documentation {
  color: #c9d1d9;
}
</style>
