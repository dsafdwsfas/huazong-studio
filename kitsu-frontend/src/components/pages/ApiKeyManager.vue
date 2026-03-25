<template>
  <div class="api-key-manager page">
    <div class="page-header flexrow">
      <page-title class="mt1 filler" text="API 密钥管理" />
      <button-simple
        class="flexrow-item"
        text="创建密钥"
        icon="plus"
        @click="showCreateModal = true"
      />
    </div>

    <!-- New key secret banner (shown only once after creation) -->
    <div class="new-key-banner" v-if="newKeySecret">
      <div class="banner-icon">&#9888;</div>
      <div class="banner-content">
        <div class="banner-title">新创建的密钥（只显示一次！请立即复制）</div>
        <div class="secret-row">
          <code class="secret-text">{{ newKeySecret }}</code>
          <button class="copy-btn" @click="copySecret">
            {{ copied ? '已复制' : '复制' }}
          </button>
        </div>
      </div>
      <button class="banner-close" @click="dismissSecret">&times;</button>
    </div>

    <!-- Key list -->
    <div class="key-list-section">
      <h2 class="section-title">密钥列表</h2>

      <spinner v-if="isLoading" />

      <div class="empty-state" v-else-if="keys.length === 0">
        <p>暂无 API 密钥。点击"创建密钥"生成第一个。</p>
      </div>

      <table class="key-table" v-else>
        <thead>
          <tr>
            <th>名称</th>
            <th>前缀</th>
            <th>权限</th>
            <th>限流</th>
            <th>过期时间</th>
            <th>最后使用</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="key in keys" :key="key.id">
            <td class="name-cell">{{ key.name }}</td>
            <td class="prefix-cell">
              <code>{{ key.prefix }}...</code>
            </td>
            <td class="scopes-cell">
              <span
                class="scope-tag"
                v-for="scope in formatScopes(key.scopes)"
                :key="scope"
              >
                {{ scope }}
              </span>
            </td>
            <td class="rate-cell">{{ key.rate_limit || 100 }}/min</td>
            <td class="expires-cell">
              {{ key.expires_at ? formatDate(key.expires_at) : '永不过期' }}
            </td>
            <td class="last-used-cell">
              {{ key.last_used_at ? formatRelativeTime(key.last_used_at) : '从未使用' }}
            </td>
            <td class="actions-cell">
              <button class="action-btn edit-btn" @click="openEditModal(key)">
                编辑
              </button>
              <button class="action-btn delete-btn" @click="confirmDelete(key)">
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create modal -->
    <div class="modal-overlay" v-if="showCreateModal" @click.self="showCreateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>创建 API 密钥</h3>
          <button class="modal-close" @click="showCreateModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>密钥名称 <span class="required">*</span></label>
            <input
              type="text"
              v-model="form.name"
              placeholder="例如: Blender 插件、Unity 集成"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label>权限范围</label>
            <div class="scope-checkboxes">
              <label
                class="scope-checkbox"
                v-for="scope in availableScopes"
                :key="scope.value"
              >
                <input
                  type="checkbox"
                  :value="scope.value"
                  v-model="form.scopes"
                />
                <span class="scope-label">{{ scope.label }}</span>
                <span class="scope-desc">{{ scope.description }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>速率限制（请求/分钟）</label>
            <input
              type="number"
              v-model.number="form.rate_limit"
              min="1"
              max="10000"
              class="form-input rate-input"
            />
          </div>

          <div class="form-group">
            <label>过期时间</label>
            <div class="expires-row">
              <label class="no-expire-checkbox">
                <input type="checkbox" v-model="form.never_expires" />
                永不过期
              </label>
              <input
                type="date"
                v-model="form.expires_at"
                class="form-input date-input"
                :disabled="form.never_expires"
                v-if="!form.never_expires"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showCreateModal = false">取消</button>
          <button
            class="btn-create"
            @click="handleCreate"
            :disabled="!form.name || isLoading"
          >
            {{ isLoading ? '创建中...' : '创建密钥' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div class="modal-overlay" v-if="showEditModal" @click.self="showEditModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>编辑 API 密钥</h3>
          <button class="modal-close" @click="showEditModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>密钥名称 <span class="required">*</span></label>
            <input
              type="text"
              v-model="editForm.name"
              class="form-input"
            />
          </div>

          <div class="form-group">
            <label>权限范围</label>
            <div class="scope-checkboxes">
              <label
                class="scope-checkbox"
                v-for="scope in availableScopes"
                :key="scope.value"
              >
                <input
                  type="checkbox"
                  :value="scope.value"
                  v-model="editForm.scopes"
                />
                <span class="scope-label">{{ scope.label }}</span>
                <span class="scope-desc">{{ scope.description }}</span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>速率限制（请求/分钟）</label>
            <input
              type="number"
              v-model.number="editForm.rate_limit"
              min="1"
              max="10000"
              class="form-input rate-input"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showEditModal = false">取消</button>
          <button
            class="btn-create"
            @click="handleUpdate"
            :disabled="!editForm.name || isLoading"
          >
            保存
          </button>
        </div>
      </div>
    </div>

    <!-- Delete confirmation -->
    <div class="modal-overlay" v-if="showDeleteModal" @click.self="showDeleteModal = false">
      <div class="modal-content modal-small">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="modal-close" @click="showDeleteModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <p>
            确定要删除密钥 <strong>{{ deleteTarget?.name }}</strong> 吗？
            此操作不可恢复，使用此密钥的所有集成将立即失效。
          </p>
        </div>
        <div class="modal-footer">
          <button class="btn-cancel" @click="showDeleteModal = false">取消</button>
          <button class="btn-delete" @click="handleDelete">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex'

import ButtonSimple from '@/components/widgets/ButtonSimple.vue'
import PageTitle from '@/components/widgets/PageTitle.vue'
import Spinner from '@/components/widgets/Spinner.vue'

export default {
  name: 'api-key-manager',

  components: {
    ButtonSimple,
    PageTitle,
    Spinner
  },

  data() {
    return {
      showCreateModal: false,
      showEditModal: false,
      showDeleteModal: false,
      deleteTarget: null,
      editTarget: null,
      copied: false,
      form: {
        name: '',
        scopes: ['assets:read'],
        rate_limit: 100,
        expires_at: '',
        never_expires: true
      },
      editForm: {
        name: '',
        scopes: [],
        rate_limit: 100
      },
      availableScopes: [
        {
          value: 'assets:read',
          label: '资产读取',
          description: '查看资产列表和详情'
        },
        {
          value: 'assets:write',
          label: '资产写入',
          description: '创建和更新资产'
        },
        {
          value: 'assets:delete',
          label: '资产删除',
          description: '删除资产'
        },
        {
          value: 'categories:read',
          label: '分类读取',
          description: '查看分类树'
        },
        {
          value: 'search',
          label: '搜索',
          description: '全文搜索资产'
        },
        {
          value: 'graph:read',
          label: '图谱读取',
          description: '查询资产关系图谱'
        }
      ]
    }
  },

  mounted() {
    this.loadApiKeys()
  },

  computed: {
    ...mapGetters(['apiKeys', 'apiKeysIsLoading', 'newKeySecret']),

    keys() {
      return this.apiKeys
    },

    isLoading() {
      return this.apiKeysIsLoading
    }
  },

  methods: {
    ...mapActions([
      'loadApiKeys',
      'createApiKey',
      'updateApiKey',
      'deleteApiKey',
      'clearNewKeySecret'
    ]),

    formatScopes(scopes) {
      if (!scopes) return []
      const labelMap = {
        'assets:read': '读',
        'assets:write': '写',
        'assets:delete': '删',
        'categories:read': '分类',
        'search': '搜索',
        'graph:read': '图谱'
      }
      return (Array.isArray(scopes) ? scopes : [scopes]).map(
        (s) => labelMap[s] || s
      )
    },

    formatDate(dateStr) {
      if (!dateStr) return ''
      const d = new Date(dateStr)
      return d.toLocaleDateString('zh-CN')
    },

    formatRelativeTime(dateStr) {
      if (!dateStr) return ''
      const now = new Date()
      const d = new Date(dateStr)
      const diff = now - d
      const minutes = Math.floor(diff / 60000)
      if (minutes < 1) return '刚刚'
      if (minutes < 60) return `${minutes}分钟前`
      const hours = Math.floor(minutes / 60)
      if (hours < 24) return `${hours}小时前`
      const days = Math.floor(hours / 24)
      if (days < 30) return `${days}天前`
      return this.formatDate(dateStr)
    },

    async copySecret() {
      try {
        await navigator.clipboard.writeText(this.newKeySecret)
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      } catch {
        // Fallback for older browsers
        const el = document.createElement('textarea')
        el.value = this.newKeySecret
        document.body.appendChild(el)
        el.select()
        document.execCommand('copy')
        document.body.removeChild(el)
        this.copied = true
        setTimeout(() => {
          this.copied = false
        }, 2000)
      }
    },

    dismissSecret() {
      this.clearNewKeySecret()
    },

    async handleCreate() {
      const payload = {
        name: this.form.name,
        scopes: this.form.scopes,
        rate_limit: this.form.rate_limit
      }
      if (!this.form.never_expires && this.form.expires_at) {
        payload.expires_at = this.form.expires_at
      }
      try {
        await this.createApiKey(payload)
        this.showCreateModal = false
        this.resetForm()
      } catch (err) {
        console.error('Create key failed:', err)
      }
    },

    openEditModal(key) {
      this.editTarget = key
      this.editForm = {
        name: key.name,
        scopes: [...(key.scopes || [])],
        rate_limit: key.rate_limit || 100
      }
      this.showEditModal = true
    },

    async handleUpdate() {
      try {
        await this.updateApiKey({
          keyId: this.editTarget.id,
          data: {
            name: this.editForm.name,
            scopes: this.editForm.scopes,
            rate_limit: this.editForm.rate_limit
          }
        })
        this.showEditModal = false
      } catch (err) {
        console.error('Update key failed:', err)
      }
    },

    confirmDelete(key) {
      this.deleteTarget = key
      this.showDeleteModal = true
    },

    async handleDelete() {
      try {
        await this.deleteApiKey(this.deleteTarget.id)
        this.showDeleteModal = false
        this.deleteTarget = null
      } catch (err) {
        console.error('Delete key failed:', err)
      }
    },

    resetForm() {
      this.form = {
        name: '',
        scopes: ['assets:read'],
        rate_limit: 100,
        expires_at: '',
        never_expires: true
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.api-key-manager {
  padding: 2em;
  max-width: 1200px;
}

.page-header {
  align-items: center;
  margin-bottom: 1.5em;
}

/* New key banner */
.new-key-banner {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  background: #1a1a2e;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 16px 20px;
  margin-bottom: 24px;
}

.banner-icon {
  font-size: 1.5em;
  color: #f59e0b;
  flex-shrink: 0;
}

.banner-content {
  flex: 1;
}

.banner-title {
  color: #f59e0b;
  font-weight: 600;
  margin-bottom: 8px;
  font-size: 0.95em;
}

.secret-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.secret-text {
  background: #0d1117;
  color: #58a6ff;
  padding: 8px 14px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.9em;
  word-break: break-all;
  flex: 1;
  border: 1px solid #30363d;
}

.copy-btn {
  background: #f59e0b;
  color: #000;
  border: none;
  padding: 8px 18px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85em;
  white-space: nowrap;
  transition: background 0.2s;

  &:hover {
    background: #d97706;
  }
}

.banner-close {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 1.4em;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;

  &:hover {
    color: #f59e0b;
  }
}

/* Key table */
.section-title {
  font-size: 1.1em;
  color: #e5e7eb;
  margin-bottom: 16px;
  font-weight: 600;
}

.key-table {
  width: 100%;
  border-collapse: collapse;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: hidden;

  th {
    background: #161b22;
    color: #8b949e;
    font-weight: 600;
    font-size: 0.85em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid #30363d;
  }

  td {
    padding: 12px 16px;
    border-bottom: 1px solid #21262d;
    color: #c9d1d9;
    font-size: 0.9em;
  }

  tr:hover td {
    background: #161b22;
  }
}

.prefix-cell code {
  background: #0d1117;
  color: #58a6ff;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85em;
}

.scope-tag {
  display: inline-block;
  background: #1f2937;
  color: #9ca3af;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8em;
  margin-right: 4px;
  margin-bottom: 2px;
  border: 1px solid #374151;
}

.actions-cell {
  white-space: nowrap;
}

.action-btn {
  background: none;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 4px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85em;
  margin-right: 6px;
  transition: all 0.2s;

  &:hover {
    background: #21262d;
  }
}

.delete-btn:hover {
  border-color: #f85149;
  color: #f85149;
}

.edit-btn:hover {
  border-color: #58a6ff;
  color: #58a6ff;
}

/* Empty state */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;

  p {
    font-size: 1em;
  }
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1c1c2e;
  border: 1px solid #30363d;
  border-radius: 12px;
  width: 560px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

.modal-small {
  width: 420px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #30363d;

  h3 {
    color: #e5e7eb;
    font-size: 1.1em;
    font-weight: 600;
    margin: 0;
  }
}

.modal-close {
  background: none;
  border: none;
  color: #6b7280;
  font-size: 1.5em;
  cursor: pointer;
  padding: 0;
  line-height: 1;

  &:hover {
    color: #e5e7eb;
  }
}

.modal-body {
  padding: 24px;

  p {
    color: #c9d1d9;
    line-height: 1.6;
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #30363d;
}

.form-group {
  margin-bottom: 20px;

  > label {
    display: block;
    color: #e5e7eb;
    font-size: 0.9em;
    font-weight: 500;
    margin-bottom: 8px;
  }
}

.required {
  color: #f85149;
}

.form-input {
  width: 100%;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  padding: 10px 14px;
  color: #c9d1d9;
  font-size: 0.9em;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: #58a6ff;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.rate-input {
  width: 140px;
}

.date-input {
  width: 200px;
}

.expires-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.no-expire-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #c9d1d9;
  font-size: 0.9em;
  cursor: pointer;
  white-space: nowrap;
}

.scope-checkboxes {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.scope-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;

  &:hover {
    border-color: #58a6ff;
  }

  input[type='checkbox'] {
    accent-color: #58a6ff;
  }
}

.scope-label {
  color: #e5e7eb;
  font-size: 0.9em;
  font-weight: 500;
  min-width: 70px;
}

.scope-desc {
  color: #6b7280;
  font-size: 0.8em;
}

.btn-cancel {
  background: #21262d;
  border: 1px solid #30363d;
  color: #c9d1d9;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;

  &:hover {
    background: #30363d;
  }
}

.btn-create {
  background: #238636;
  border: none;
  color: #fff;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9em;

  &:hover {
    background: #2ea043;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-delete {
  background: #da3633;
  border: none;
  color: #fff;
  padding: 8px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9em;

  &:hover {
    background: #f85149;
  }
}

/* Dark theme integration */
.dark .api-key-manager {
  color: #c9d1d9;
}
</style>
