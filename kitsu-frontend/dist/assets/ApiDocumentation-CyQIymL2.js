import{_ as m,r as g,o,c as s,d as t,F as l,e as q,n as i,t as p,h as u,j as b,f as x,w as _,k as y}from"./index-A_ef7tka.js";const E={name:"api-documentation",data(){return{activeSection:"auth",activeExample:"curl",sections:[{id:"auth",label:"认证"},{id:"assets",label:"资产",children:[{id:"assets-list",label:"列表"},{id:"assets-detail",label:"详情"},{id:"assets-create",label:"创建"},{id:"assets-update",label:"更新"},{id:"assets-delete",label:"删除"}]},{id:"search",label:"搜索"},{id:"categories",label:"分类"},{id:"versions",label:"版本"},{id:"usages",label:"使用记录"},{id:"graph",label:"图谱"},{id:"rate-limiting",label:"速率限制"},{id:"errors",label:"错误码"},{id:"examples",label:"代码示例"}]}},mounted(){this.setupScrollSpy()},beforeUnmount(){this._observer&&this._observer.disconnect()},methods:{scrollTo(v){const d=document.getElementById(v);d&&(d.scrollIntoView({behavior:"smooth",block:"start"}),this.activeSection=v)},setupScrollSpy(){const v={root:this.$refs.docContent,rootMargin:"-80px 0px -60% 0px",threshold:0};this._observer=new IntersectionObserver(d=>{for(const n of d)n.isIntersecting&&(this.activeSection=n.target.id)},v),this.$nextTick(()=>{document.querySelectorAll(".doc-section, .endpoint-card").forEach(n=>{n.id&&this._observer.observe(n)})})}}},k={class:"api-documentation page"},f={class:"doc-layout"},T={class:"doc-sidebar"},A={class:"nav-list"},S=["onClick"],I={key:0,class:"nav-sublist"},P=["onClick"],C={class:"doc-content",ref:"docContent"},O={id:"auth",class:"doc-section"},w={id:"examples",class:"doc-section"},B={class:"example-tabs"},K={key:0},N={key:1},R={key:2};function j(v,d,n,L,a,r){const h=g("router-link");return o(),s("div",k,[t("div",f,[t("nav",T,[d[3]||(d[3]=t("h3",{class:"sidebar-title"},"画宗开放 API v1",-1)),t("ul",A,[(o(!0),s(l,null,q(a.sections,e=>(o(),s("li",{key:e.id,class:i({active:a.activeSection===e.id})},[t("a",{onClick:c=>r.scrollTo(e.id)},p(e.label),9,S),e.children?(o(),s("ul",I,[(o(!0),s(l,null,q(e.children,c=>(o(),s("li",{key:c.id,class:i({active:a.activeSection===c.id})},[t("a",{onClick:z=>r.scrollTo(c.id)},p(c.label),9,P)],2))),128))])):u("",!0)],2))),128))])]),t("main",C,[t("section",O,[d[7]||(d[7]=t("h1",null,"认证",-1)),d[8]||(d[8]=t("p",null,"所有 API 请求需要在请求头中携带 API Key：",-1)),d[9]||(d[9]=t("div",{class:"code-block"},[t("div",{class:"code-header"},"HTTP Header"),t("pre",null,[t("code",null,"Authorization: Bearer hz_live_xxxxxxxxxxxxxxxxxxxxxxxx")])],-1)),t("p",null,[d[5]||(d[5]=b(" API Key 可在 ")),x(h,{to:{name:"api-key-manager"}},{default:_(()=>d[4]||(d[4]=[b("API 密钥管理")])),_:1}),d[6]||(d[6]=b(" 页面创建和管理。每个密钥可配置独立的权限范围和速率限制。 "))]),d[10]||(d[10]=t("div",{class:"info-box"},[t("strong",null,"安全提示："),b("密钥仅在创建时显示一次，请妥善保管。 不要在客户端代码或版本控制中暴露密钥。 ")],-1))]),d[15]||(d[15]=y(`<section id="assets" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>资产</h1><div id="assets-list" class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets</code></div><p class="endpoint-desc" data-v-70d6229b>获取资产列表，支持分页和过滤。</p><h4 data-v-70d6229b>查询参数</h4><table class="param-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>参数</th><th data-v-70d6229b>类型</th><th data-v-70d6229b>必填</th><th data-v-70d6229b>说明</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>page</code></td><td data-v-70d6229b>integer</td><td data-v-70d6229b>否</td><td data-v-70d6229b>页码，默认 1</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>per_page</code></td><td data-v-70d6229b>integer</td><td data-v-70d6229b>否</td><td data-v-70d6229b>每页条数，默认 20，最大 100</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>category_id</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>按分类 ID 过滤</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>status</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>按状态过滤: draft / active / archived</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>search</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>关键词搜索名称和标签</td></tr></tbody></table><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;data&quot;: [
    {
      &quot;id&quot;: &quot;a1b2c3d4&quot;,
      &quot;name&quot;: &quot;主角-李明&quot;,
      &quot;category&quot;: &quot;character&quot;,
      &quot;status&quot;: &quot;active&quot;,
      &quot;tags&quot;: [&quot;主角&quot;, &quot;男性&quot;],
      &quot;thumbnail_url&quot;: &quot;/api/thumbnails/a1b2c3d4.png&quot;,
      &quot;usage_count&quot;: 42,
      &quot;created_at&quot;: &quot;2025-03-01T10:00:00Z&quot;,
      &quot;updated_at&quot;: &quot;2025-03-15T14:30:00Z&quot;
    }
  ],
  &quot;meta&quot;: {
    &quot;page&quot;: 1,
    &quot;per_page&quot;: 20,
    &quot;total&quot;: 156,
    &quot;total_pages&quot;: 8
  }
}</code></pre></div></div><div id="assets-detail" class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}</code></div><p class="endpoint-desc" data-v-70d6229b>获取单个资产详情，包括文件列表和元数据。</p><h4 data-v-70d6229b>路径参数</h4><table class="param-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>参数</th><th data-v-70d6229b>类型</th><th data-v-70d6229b>说明</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>asset_id</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>资产 ID</td></tr></tbody></table><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;id&quot;: &quot;a1b2c3d4&quot;,
  &quot;name&quot;: &quot;主角-李明&quot;,
  &quot;category&quot;: &quot;character&quot;,
  &quot;description&quot;: &quot;故事主角，28岁程序员&quot;,
  &quot;status&quot;: &quot;active&quot;,
  &quot;tags&quot;: [&quot;主角&quot;, &quot;男性&quot;],
  &quot;metadata&quot;: { &quot;height&quot;: &quot;178cm&quot;, &quot;style&quot;: &quot;写实&quot; },
  &quot;files&quot;: [
    { &quot;id&quot;: &quot;f1&quot;, &quot;name&quot;: &quot;front.png&quot;, &quot;size&quot;: 245000, &quot;type&quot;: &quot;image/png&quot; }
  ],
  &quot;versions&quot;: 3,
  &quot;usage_count&quot;: 42,
  &quot;created_at&quot;: &quot;2025-03-01T10:00:00Z&quot;,
  &quot;updated_at&quot;: &quot;2025-03-15T14:30:00Z&quot;
}</code></pre></div></div><div id="assets-create" class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge post" data-v-70d6229b>POST</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets</code></div><p class="endpoint-desc" data-v-70d6229b>创建新资产。需要 <code data-v-70d6229b>assets:write</code> 权限。</p><h4 data-v-70d6229b>请求体</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>JSON</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;name&quot;: &quot;新场景-森林&quot;,
  &quot;category&quot;: &quot;scene&quot;,
  &quot;description&quot;: &quot;魔法森林场景&quot;,
  &quot;tags&quot;: [&quot;森林&quot;, &quot;魔幻&quot;],
  &quot;metadata&quot;: { &quot;lighting&quot;: &quot;黄昏&quot;, &quot;mood&quot;: &quot;神秘&quot; }
}</code></pre></div><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>201 Created</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;id&quot;: &quot;e5f6g7h8&quot;,
  &quot;name&quot;: &quot;新场景-森林&quot;,
  &quot;category&quot;: &quot;scene&quot;,
  &quot;status&quot;: &quot;draft&quot;,
  &quot;created_at&quot;: &quot;2025-03-20T09:00:00Z&quot;
}</code></pre></div></div><div id="assets-update" class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge put" data-v-70d6229b>PUT</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}</code></div><p class="endpoint-desc" data-v-70d6229b>更新资产。需要 <code data-v-70d6229b>assets:write</code> 权限。支持部分更新。</p><h4 data-v-70d6229b>请求体</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>JSON</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;name&quot;: &quot;更新后的名称&quot;,
  &quot;tags&quot;: [&quot;新标签&quot;],
  &quot;status&quot;: &quot;active&quot;
}</code></pre></div></div><div id="assets-delete" class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge delete" data-v-70d6229b>DELETE</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}</code></div><p class="endpoint-desc" data-v-70d6229b>删除资产。需要 <code data-v-70d6229b>assets:delete</code> 权限。此操作不可恢复。</p></div></section><section id="search" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>搜索</h1><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/search</code></div><p class="endpoint-desc" data-v-70d6229b>全文搜索资产。需要 <code data-v-70d6229b>search</code> 权限。</p><h4 data-v-70d6229b>查询参数</h4><table class="param-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>参数</th><th data-v-70d6229b>类型</th><th data-v-70d6229b>必填</th><th data-v-70d6229b>说明</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>q</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>是</td><td data-v-70d6229b>搜索关键词</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>category</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>限定分类</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>page</code></td><td data-v-70d6229b>integer</td><td data-v-70d6229b>否</td><td data-v-70d6229b>页码</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>per_page</code></td><td data-v-70d6229b>integer</td><td data-v-70d6229b>否</td><td data-v-70d6229b>每页条数</td></tr></tbody></table><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;data&quot;: [
    {
      &quot;id&quot;: &quot;a1b2c3d4&quot;,
      &quot;name&quot;: &quot;主角-李明&quot;,
      &quot;score&quot;: 0.95,
      &quot;highlights&quot;: [&quot;<em data-v-70d6229b>主角</em>-李明&quot;]
    }
  ],
  &quot;meta&quot;: { &quot;total&quot;: 12, &quot;query_time_ms&quot;: 23 }
}</code></pre></div></div></section><section id="categories" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>分类</h1><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/categories</code></div><p class="endpoint-desc" data-v-70d6229b>获取分类树。需要 <code data-v-70d6229b>categories:read</code> 权限。</p><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;data&quot;: [
    {
      &quot;id&quot;: &quot;cat-001&quot;,
      &quot;name&quot;: &quot;人物&quot;,
      &quot;slug&quot;: &quot;character&quot;,
      &quot;icon&quot;: &quot;user&quot;,
      &quot;children&quot;: [
        { &quot;id&quot;: &quot;cat-002&quot;, &quot;name&quot;: &quot;主要角色&quot;, &quot;parent_id&quot;: &quot;cat-001&quot; },
        { &quot;id&quot;: &quot;cat-003&quot;, &quot;name&quot;: &quot;配角&quot;, &quot;parent_id&quot;: &quot;cat-001&quot; }
      ]
    }
  ]
}</code></pre></div></div><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/categories/{category_id}</code></div><p class="endpoint-desc" data-v-70d6229b>获取单个分类详情及其子分类。</p></div></section><section id="versions" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>版本</h1><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}/versions</code></div><p class="endpoint-desc" data-v-70d6229b>获取资产的版本历史列表。</p><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;data&quot;: [
    {
      &quot;version&quot;: 3,
      &quot;comment&quot;: &quot;更新了正面视图&quot;,
      &quot;author&quot;: &quot;张三&quot;,
      &quot;created_at&quot;: &quot;2025-03-15T14:30:00Z&quot;,
      &quot;files_changed&quot;: 2
    }
  ]
}</code></pre></div></div></section><section id="usages" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>使用记录</h1><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}/usages</code></div><p class="endpoint-desc" data-v-70d6229b>获取资产在各项目中的使用记录。</p></div><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge post" data-v-70d6229b>POST</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/assets/{asset_id}/usages</code></div><p class="endpoint-desc" data-v-70d6229b>记录资产使用（外部工具集成时调用）。</p><h4 data-v-70d6229b>请求体</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>JSON</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;project_id&quot;: &quot;proj-123&quot;,
  &quot;context&quot;: &quot;blender-scene-import&quot;,
  &quot;tool&quot;: &quot;Blender 4.1&quot;
}</code></pre></div></div></section><section id="graph" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>图谱</h1><div class="endpoint-card" data-v-70d6229b><div class="endpoint-header" data-v-70d6229b><span class="method-badge get" data-v-70d6229b>GET</span><code class="endpoint-url" data-v-70d6229b>/open-api/v1/graph</code></div><p class="endpoint-desc" data-v-70d6229b>查询资产关系图谱。需要 <code data-v-70d6229b>graph:read</code> 权限。</p><h4 data-v-70d6229b>查询参数</h4><table class="param-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>参数</th><th data-v-70d6229b>类型</th><th data-v-70d6229b>必填</th><th data-v-70d6229b>说明</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>asset_id</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>以此资产为中心查询</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>depth</code></td><td data-v-70d6229b>integer</td><td data-v-70d6229b>否</td><td data-v-70d6229b>关系深度，默认 2</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>relation_type</code></td><td data-v-70d6229b>string</td><td data-v-70d6229b>否</td><td data-v-70d6229b>关系类型过滤</td></tr></tbody></table><h4 data-v-70d6229b>响应示例</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>200 OK</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;nodes&quot;: [
    { &quot;id&quot;: &quot;a1&quot;, &quot;name&quot;: &quot;主角-李明&quot;, &quot;type&quot;: &quot;character&quot; },
    { &quot;id&quot;: &quot;a2&quot;, &quot;name&quot;: &quot;魔法森林&quot;, &quot;type&quot;: &quot;scene&quot; }
  ],
  &quot;edges&quot;: [
    { &quot;source&quot;: &quot;a1&quot;, &quot;target&quot;: &quot;a2&quot;, &quot;relation&quot;: &quot;appears_in&quot; }
  ]
}</code></pre></div></div></section><section id="rate-limiting" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>速率限制</h1><p data-v-70d6229b>每个 API Key 有独立的速率限制（创建时配置，默认 100 次/分钟）。</p><h4 data-v-70d6229b>响应头</h4><table class="param-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>头部</th><th data-v-70d6229b>说明</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>X-RateLimit-Limit</code></td><td data-v-70d6229b>当前窗口允许的最大请求数</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>X-RateLimit-Remaining</code></td><td data-v-70d6229b>当前窗口剩余请求数</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>X-RateLimit-Reset</code></td><td data-v-70d6229b>窗口重置的 Unix 时间戳</td></tr></tbody></table><p data-v-70d6229b>超过限制时返回 <code data-v-70d6229b>429 Too Many Requests</code>，请等待窗口重置后重试。</p></section><section id="errors" class="doc-section" data-v-70d6229b><h1 data-v-70d6229b>错误码</h1><table class="param-table error-table" data-v-70d6229b><thead data-v-70d6229b><tr data-v-70d6229b><th data-v-70d6229b>状态码</th><th data-v-70d6229b>说明</th><th data-v-70d6229b>处理建议</th></tr></thead><tbody data-v-70d6229b><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>400</code></td><td data-v-70d6229b>请求参数错误</td><td data-v-70d6229b>检查请求体和查询参数格式</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>401</code></td><td data-v-70d6229b>未认证 — 缺少或无效的 API Key</td><td data-v-70d6229b>检查 Authorization 头格式和密钥有效性</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>403</code></td><td data-v-70d6229b>权限不足 — API Key 缺少所需 scope</td><td data-v-70d6229b>在密钥管理页面添加对应权限</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>404</code></td><td data-v-70d6229b>资源不存在</td><td data-v-70d6229b>确认资源 ID 正确且未被删除</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>429</code></td><td data-v-70d6229b>请求过于频繁</td><td data-v-70d6229b>等待 X-RateLimit-Reset 后重试</td></tr><tr data-v-70d6229b><td data-v-70d6229b><code data-v-70d6229b>500</code></td><td data-v-70d6229b>服务器内部错误</td><td data-v-70d6229b>请稍后重试或联系管理员</td></tr></tbody></table><h4 data-v-70d6229b>错误响应格式</h4><div class="code-block" data-v-70d6229b><div class="code-header" data-v-70d6229b>JSON</div><pre data-v-70d6229b><code data-v-70d6229b>{
  &quot;error&quot;: {
    &quot;code&quot;: &quot;INSUFFICIENT_SCOPE&quot;,
    &quot;message&quot;: &quot;API Key 缺少 assets:write 权限&quot;,
    &quot;required_scope&quot;: &quot;assets:write&quot;
  }
}</code></pre></div></section>`,8)),t("section",w,[d[14]||(d[14]=t("h1",null,"代码示例",-1)),t("div",B,[t("span",{class:i(["example-tab",{active:a.activeExample==="curl"}]),onClick:d[0]||(d[0]=e=>a.activeExample="curl")},"cURL",2),t("span",{class:i(["example-tab",{active:a.activeExample==="python"}]),onClick:d[1]||(d[1]=e=>a.activeExample="python")},"Python",2),t("span",{class:i(["example-tab",{active:a.activeExample==="javascript"}]),onClick:d[2]||(d[2]=e=>a.activeExample="javascript")},"JavaScript",2)]),a.activeExample==="curl"?(o(),s("div",K,d[11]||(d[11]=[t("h4",null,"获取资产列表",-1),t("div",{class:"code-block"},[t("div",{class:"code-header"},"bash"),t("pre",null,[t("code",null,`curl -X GET "https://your-domain.com/api/open-api/v1/assets?page=1&per_page=10" \\
  -H "Authorization: Bearer hz_live_xxxxxxxx"`)])],-1),t("h4",null,"创建资产",-1),t("div",{class:"code-block"},[t("div",{class:"code-header"},"bash"),t("pre",null,[t("code",null,`curl -X POST "https://your-domain.com/api/open-api/v1/assets" \\
  -H "Authorization: Bearer hz_live_xxxxxxxx" \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "新角色",
    "category": "character",
    "tags": ["NPC"]
  }'`)])],-1)]))):u("",!0),a.activeExample==="python"?(o(),s("div",N,d[12]||(d[12]=[t("h4",null,"获取资产列表",-1),t("div",{class:"code-block"},[t("div",{class:"code-header"},"python"),t("pre",null,[t("code",null,`import requests

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
print(f"Created: {new_asset.json()['id']}")`)])],-1)]))):u("",!0),a.activeExample==="javascript"?(o(),s("div",R,d[13]||(d[13]=[t("h4",null,"获取资产列表",-1),t("div",{class:"code-block"},[t("div",{class:"code-header"},"javascript"),t("pre",null,[t("code",null,`const API_KEY = 'hz_live_xxxxxxxx'
const BASE_URL = 'https://your-domain.com/api/open-api/v1'

const headers = {
  'Authorization': \`Bearer \${API_KEY}\`,
  'Content-Type': 'application/json'
}

// 获取资产列表
const resp = await fetch(
  \`\${BASE_URL}/assets?page=1&per_page=20\`,
  { headers }
)
const { data, meta } = await resp.json()
console.log(\`共 \${meta.total} 个资产\`)

// 创建资产
const created = await fetch(\`\${BASE_URL}/assets\`, {
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
console.log(\`Created: \${newAsset.id}\`)`)])],-1)]))):u("",!0)])],512)])])}const G=m(E,[["render",j],["__scopeId","data-v-70d6229b"]]);export{G as default};
//# sourceMappingURL=ApiDocumentation-CyQIymL2.js.map
