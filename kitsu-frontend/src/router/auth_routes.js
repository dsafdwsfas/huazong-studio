/**
 * 画宗认证路由补充
 *
 * 使用方式：在 routes.js 中 import 并合并到路由数组
 *
 *   import huazongAuthRoutes from '@/router/auth_routes'
 *   export const routes = [
 *     ...huazongAuthRoutes,
 *     // ... 现有路由
 *   ]
 */

const LoginHuazong = () =>
  import('@/components/pages/LoginHuazong.vue')
const OAuthCallback = () =>
  import('@/components/pages/OAuthCallback.vue')

export default [
  {
    path: '/login-huazong',
    component: LoginHuazong,
    name: 'login-huazong'
  },
  {
    path: '/auth/callback',
    component: OAuthCallback,
    name: 'oauth-callback'
  }
]
